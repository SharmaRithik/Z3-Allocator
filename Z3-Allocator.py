import pandas as pd
import re
import sys
from z3 import *

def get_device_configs(cpu_file):
    """Determine device configurations based on input filename pattern."""
    if 'android_tree' in cpu_file:
        return {
            '3A021JEHN02756': {
                'small': {'cores': [0, 1, 2, 3], 'counts': [1, 2, 3, 4]},
                'medium': {'cores': [4, 5], 'counts': [1, 2]},
                'big': {'cores': [6, 7], 'counts': [1, 2]},
                'gpu': {'cores': [8], 'counts': [1]}
            },
            '9b034f1b': {
                'small': {'cores': [0, 1], 'counts': [1, 2]},
                'medium': {'cores': [2, 3, 4], 'counts': [1, 2, 3]},
                'gpu': {'cores': [8], 'counts': [1]}
            }
        }
    elif 'jetson_tree' in cpu_file:
        return {
            'jetson': {
                'small': {'cores': [1, 2, 3, 4, 5, 6], 'counts': [1, 2, 3, 4, 5, 6]},
                'gpu': {'cores': [1], 'counts': [1]}
            }
        }
    else:
        raise ValueError(f"Unsupported device configuration for file: {cpu_file}")

def parse_benchmark_files(cpu_file_path, gpu_file_path):
    """Parse both CPU and GPU benchmark files."""
    try:
        with open(cpu_file_path, 'r') as file:
            cpu_lines = file.readlines()
        with open(gpu_file_path, 'r') as file:
            gpu_lines = file.readlines()
    except FileNotFoundError as e:
        print(f"File not found: {str(e)}")
        return None
    
    device_data = []
    current_device_id = None
    
    # Get device configurations based on input file
    device_configs = get_device_configs(cpu_file_path)
    
    found_target_device = False
    current_config = None
    
    # Parse CPU data
    for line in cpu_lines:
        line = line.strip()
        
        # Match device ID for Android devices
        device_id_match = re.search(r'on device:\s+(\S+)', line)
        if device_id_match:
            current_device_id = device_id_match.group(1)
            if 'jetson_tree' in cpu_file_path:
                current_device_id = 'jetson'  # Override device ID for Jetson
            current_config = device_configs.get(current_device_id)
            if current_config:
                found_target_device = True
            continue
        
        # Set Jetson device ID based on CPU info
        if 'jetson_tree' in cpu_file_path and 'Run on' in line and not current_device_id:
            current_device_id = 'jetson'
            current_config = device_configs.get(current_device_id)
            if current_config:
                found_target_device = True
            
        if line.startswith("ppl/") or line.startswith("[") or not line or line.startswith("CPU Caches"):
            continue
            
        # Only process CPU_Pinned data
        if "CPU_Pinned" not in line:
            continue
            
        benchmark_match = re.match(r'"([^"]+)",(\d+),([\d.]+),([\d.]+),(\w+)', line)
        if benchmark_match and current_device_id:
            task, iterations, real_time, cpu_time, time_unit = (
                benchmark_match.group(1),
                int(benchmark_match.group(2)),
                float(benchmark_match.group(3)),
                float(benchmark_match.group(4)),
                benchmark_match.group(5)
            )
            
            task_details = task.split('/')
            if len(task_details) >= 4:
                task_name = task_details[1]
                core_type = task_details[2]
                core_count = task_details[3]
                
                # Only add data if the core type is available for this device
                if core_type in current_config:
                    device_data.append([
                        current_device_id,
                        'cpu_benchmark',
                        task_name,
                        core_type,
                        core_count,
                        iterations,
                        real_time,
                        cpu_time,
                        time_unit
                    ])
    
    # Parse GPU data - handle both Vulkan and CUDA
    gpu_type = None
    if 'android_tree_vk.csv' in gpu_file_path:
        gpu_type = 'iGPU_Vulkan'
    elif 'jetson_tree_cuda.csv' in gpu_file_path:
        gpu_type = 'iGPU_CUDA'
    
    for line in gpu_lines:
        line = line.strip()
        
        # Handle device ID for Android
        device_id_match = re.search(r'on device:\s+(\S+)', line)
        if device_id_match:
            current_device_id = device_id_match.group(1)
            if 'jetson_tree' in gpu_file_path:
                current_device_id = 'jetson'
            continue
        
        # Set Jetson device ID based on CPU info in GPU file
        if 'jetson_tree' in gpu_file_path and 'Run on' in line and not current_device_id:
            current_device_id = 'jetson'
            
        if gpu_type and gpu_type in line:
            benchmark_match = re.match(r'"([^"]+)",(\d+),([\d.]+),([\d.]+),(\w+)', line)
            if benchmark_match and current_device_id:
                task, iterations, real_time, cpu_time, time_unit = (
                    benchmark_match.group(1),
                    int(benchmark_match.group(2)),
                    float(benchmark_match.group(3)),
                    float(benchmark_match.group(4)),
                    benchmark_match.group(5)
                )
                
                task_name = task.split('/')[1]
                device_data.append([
                    current_device_id,
                    'gpu_benchmark',
                    task_name,
                    'gpu',
                    '1',  # GPU always uses count of 1
                    iterations,
                    real_time,
                    cpu_time,
                    time_unit
                ])
    
    if not device_data:
        print("No data parsed from files.")
        return None
        
    df = pd.DataFrame(device_data, columns=['Device_ID', 'Category', 'Task', 'Core_Type', 
                                          'Core_Count', 'Iterations', 'Real_Time', 
                                          'CPU_Time', 'Time_Unit'])
    
    return df, device_configs

def solve_task_allocation(device_df, tasks, core_configs, task_dependencies, pipeline_sequence, num_pipelines, transfer_penalty=1.2):
    """Solve task allocation with GPU support and maximum core count enforcement."""
    solver = Optimize()
    
    # Helper function to get max core count for a core type
    def get_max_core_count(core_type):
        return max(core_configs[core_type]['counts'])
    
    # Create task assignment variables using core counts
    task_vars = {}
    for task in pipeline_sequence:
        for core_type, config in core_configs.items():
            for count in config['counts']:
                var_name = f"{task}_{core_type}_{count}"
                task_vars[var_name] = Int(var_name)
                solver.add(Or(task_vars[var_name] == 0, task_vars[var_name] == 1))
    
    # Ensure exactly one assignment per task and enforce maximum core usage
    for task in pipeline_sequence:
        # Create variables to track if each core type is used for this task
        core_type_used = {}
        for core_type in core_configs.keys():
            var_name = f"{task}_{core_type}_used"
            core_type_used[core_type] = Bool(var_name)
            
            # Define when a core type is considered "used"
            solver.add(core_type_used[core_type] == 
                      Or([task_vars[f"{task}_{core_type}_{count}"] == 1 
                         for count in core_configs[core_type]['counts']]))
            
            # If this core type is used, enforce using maximum core count
            max_count = get_max_core_count(core_type)
            solver.add(Implies(core_type_used[core_type],
                             And([task_vars[f"{task}_{core_type}_{count}"] == 0 
                                 for count in core_configs[core_type]['counts']
                                 if count != max_count])))
        
        # Ensure exactly one assignment per task
        assignment_sum = Sum([task_vars[f"{task}_{core_type}_{count}"]
                            for core_type, config in core_configs.items()
                            for count in config['counts']])
        solver.add(assignment_sum == 1)
    
    # Track when each core type is first used and when it's abandoned
    core_first_use = {}
    core_last_use = {}
    for core_type in core_configs.keys():
        # Variables to track first and last use positions
        core_first_use[core_type] = Int(f'first_use_{core_type}')
        core_last_use[core_type] = Int(f'last_use_{core_type}')
        
        # Initialize position tracking
        solver.add(core_first_use[core_type] >= 0)
        solver.add(core_first_use[core_type] < len(pipeline_sequence))
        solver.add(core_last_use[core_type] >= 0)
        solver.add(core_last_use[core_type] < len(pipeline_sequence))
        
        # Find first use
        first_use_constraints = []
        for pos, task in enumerate(pipeline_sequence):
            task_uses_core = Or([task_vars[f"{task}_{core_type}_{count}"] == 1
                               for count in core_configs[core_type]['counts']])
            first_use_constraints.append(
                And(task_uses_core,
                    And([Not(Or([task_vars[f"{pipeline_sequence[j]}_{core_type}_{count}"] == 1
                                for count in core_configs[core_type]['counts']]))
                         for j in range(pos)]))
            )
        solver.add(Or([And(first_use_constraints[pos],
                          core_first_use[core_type] == pos)
                      for pos in range(len(pipeline_sequence))]
                     + [And(And([Not(Or([task_vars[f"{task}_{core_type}_{count}"] == 1
                                        for count in core_configs[core_type]['counts']]))
                                for task in pipeline_sequence]),
                           core_first_use[core_type] == len(pipeline_sequence))]))
        
        # Find last use
        last_use_constraints = []
        for pos, task in enumerate(pipeline_sequence):
            task_uses_core = Or([task_vars[f"{task}_{core_type}_{count}"] == 1
                               for count in core_configs[core_type]['counts']])
            last_use_constraints.append(
                And(task_uses_core,
                    And([Not(Or([task_vars[f"{pipeline_sequence[j]}_{core_type}_{count}"] == 1
                                for count in core_configs[core_type]['counts']]))
                         for j in range(pos + 1, len(pipeline_sequence))]))
            )
        solver.add(Or([And(last_use_constraints[pos],
                          core_last_use[core_type] == pos)
                      for pos in range(len(pipeline_sequence))]
                     + [And(And([Not(Or([task_vars[f"{task}_{core_type}_{count}"] == 1
                                        for count in core_configs[core_type]['counts']]))
                                for task in pipeline_sequence]),
                           core_last_use[core_type] == -1)]))

    # Ensure continuous use of core types (no gaps)
    for core_type in core_configs.keys():
        for pos in range(1, len(pipeline_sequence) - 1):
            task = pipeline_sequence[pos]
            task_uses_core = Or([task_vars[f"{task}_{core_type}_{count}"] == 1
                               for count in core_configs[core_type]['counts']])
            
            solver.add(Implies(And(core_first_use[core_type] < pos,
                                 core_last_use[core_type] > pos),
                             task_uses_core))
    
    # Calculate individual task execution times
    task_exec_times = {}
    for task in pipeline_sequence:
        for core_type, config in core_configs.items():
            for count in config['counts']:
                task_data = device_df[
                    (device_df['Task'] == task) &
                    (device_df['Core_Type'] == core_type) &
                    (device_df['Core_Count'] == str(count))
                ]
                if not task_data.empty:
                    task_exec_times[(task, core_type, count)] = task_data['Real_Time'].iloc[0]
                else:
                    print(f"Warning: No execution time data found for {task} on {core_type} with {count} cores")

    # Calculate core type total execution times
    core_total_times = {}
    for core_type in core_configs.keys():
        core_total_times[core_type] = Real(f'total_time_{core_type}')
        time_expr = Sum([
            task_vars[f"{task}_{core_type}_{count}"] * task_exec_times.get((task, core_type, count), 0)
            for task in pipeline_sequence
            for count in core_configs[core_type]['counts']
            if (task, core_type, count) in task_exec_times
        ])
        solver.add(core_total_times[core_type] == time_expr)
    
    # Add constraints for balanced execution times
    total_exec_time = Sum([core_total_times[core_type] for core_type in core_configs.keys()])
    ideal_time_per_core = total_exec_time / len(core_configs)
    
    # Add soft constraints to keep core execution times close to ideal
    for core_type in core_configs.keys():
        solver.add_soft(core_total_times[core_type] <= ideal_time_per_core * 1.2, weight=100)
        solver.add_soft(core_total_times[core_type] >= ideal_time_per_core * 0.8, weight=100)
        # Calculate task times and dependencies
    task_times = {}
    start_times = {}
    end_times = {}

    for pipeline_idx in range(num_pipelines):
        for task in pipeline_sequence:
            if task not in task_times:
                task_times[task] = Real(f'time_{task}')
                time_expr = Sum([
                    task_vars[f"{task}_{core_type}_{count}"] * task_exec_times.get((task, core_type, count), 0)
                    for core_type, config in core_configs.items()
                    for count in config['counts']
                    if (task, core_type, count) in task_exec_times
                ])
                solver.add(task_times[task] == time_expr)

            start_times[f"{task}_{pipeline_idx}"] = Real(f'start_{task}_{pipeline_idx}')
            end_times[f"{task}_{pipeline_idx}"] = Real(f'end_{task}_{pipeline_idx}')
            solver.add(start_times[f"{task}_{pipeline_idx}"] >= 0)
            solver.add(end_times[f"{task}_{pipeline_idx}"] ==
                      start_times[f"{task}_{pipeline_idx}"] +
                      task_times[task])

    # Enforce pipeline sequence dependencies
    for pipeline_idx in range(num_pipelines):
        for i in range(len(pipeline_sequence) - 1):
            current_task = pipeline_sequence[i]
            next_task = pipeline_sequence[i + 1]
            solver.add(start_times[f"{next_task}_{pipeline_idx}"] >=
                      end_times[f"{current_task}_{pipeline_idx}"])

    # Enforce task dependencies across pipelines
    for task_idx, task in enumerate(pipeline_sequence):
        for pipeline_idx in range(num_pipelines - 1):
            solver.add(start_times[f"{task}_{pipeline_idx + 1}"] >=
                      end_times[f"{task}_{pipeline_idx}"])

    # Calculate total pipeline time
    total_time = Real('total_time')
    for pipeline_idx in range(num_pipelines):
        for task in pipeline_sequence:
            solver.add(total_time >= end_times[f"{task}_{pipeline_idx}"])

    # Minimize total time
    solver.minimize(total_time)

    if solver.check() == sat:
        model = solver.model()
        def safe_float(decimal_str):
            try:
                return float(str(decimal_str).replace('?', ''))
            except (ValueError, TypeError):
                return 0.0

        solution = {
            'assignments': {},
            'execution_times': {},
            'start_times': {},
            'end_times': {},
            'total_time': safe_float(model[total_time].as_decimal(6)),
            'num_pipelines': num_pipelines,
            'pipeline_sequence': pipeline_sequence,
            'core_execution_times': {core_type: safe_float(model[core_total_times[core_type]].as_decimal(6))
                                   for core_type in core_configs.keys()}
        }

        for task in pipeline_sequence:
            for core_type, config in core_configs.items():
                for count in config['counts']:
                    var_name = f"{task}_{core_type}_{count}"
                    if var_name in task_vars and model[task_vars[var_name]].as_long() == 1:
                        for pipeline_idx in range(num_pipelines):
                            solution['assignments'][(task, pipeline_idx)] = (core_type, count)
                            exec_time = safe_float(model[task_times[task]].as_decimal(6))
                            solution['execution_times'][(task, pipeline_idx)] = exec_time

        for pipeline_idx in range(num_pipelines):
            for task in pipeline_sequence:
                task_key = f"{task}_{pipeline_idx}"
                solution['start_times'][(task, pipeline_idx)] = safe_float(model[start_times[task_key]].as_decimal(6))
                solution['end_times'][(task, pipeline_idx)] = safe_float(model[end_times[task_key]].as_decimal(6))

        return solution
    else:
        return None

def main():
    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 Z3-Allocator.py <cpu_benchmark_file> <gpu_benchmark_file>")
        print("Example 1: python3 Z3-Allocator.py android_tree_cpu.csv android_tree_vk.csv")
        print("Example 2: python3 Z3-Allocator.py jetson_tree_cpu.csv jetson_tree_cuda.csv")
        return

    cpu_file = sys.argv[1]
    gpu_file = sys.argv[2]

    # Define the fixed pipeline sequence
    pipeline_sequence = [
        'run_stage1',
        'run_stage2',
        'run_stage3',
        'run_stage4',
        'run_stage5',
        'run_stage6',
        'run_stage7'
    ]

    # Define task dependencies based on sequence
    task_dependencies = {}
    for i in range(len(pipeline_sequence)-1):
        task_dependencies[pipeline_sequence[i+1]] = [pipeline_sequence[i]]
    task_dependencies['run_stage1'] = []  # First task has no dependencies

    # Get number of pipelines from user
    num_pipelines = int(input("Enter the number of times to run the pipeline: "))

    # Parse benchmark data from both CPU and GPU files
    df, device_configs = parse_benchmark_files(cpu_file, gpu_file)
    if df is None:
        return

    print(f"\nAnalyzing benchmark data from:")
    print(f"CPU File: {cpu_file}")
    print(f"GPU File: {gpu_file}")
    print("\nPipeline Sequence:")
    print(" -> ".join(pipeline_sequence))
    print(f"\nPipeline will be executed {num_pipelines} times")

    # Process each device
    for device_id, device_df in df.groupby('Device_ID'):
        print(f"\nResults for Device: {device_id}")

        if device_id in device_configs:
            print("\nCore Configuration:")
            for core_type, config in device_configs[device_id].items():
                print(f"{core_type.capitalize()} cores: {config['cores']} (Available counts: {config['counts']})")

        print("\nCalculating optimal task allocation with CPU and GPU support...")

        # Use the device-specific core configuration
        core_configs = device_configs[device_id]

        # Solve task allocation
        solution = solve_task_allocation(device_df, pipeline_sequence, core_configs,
                                      task_dependencies, pipeline_sequence, num_pipelines)

        if solution:
            print("\nOptimal Pipeline Allocation:")
            print("-" * 80)

            # Print results for each pipeline instance
            for pipeline_idx in range(num_pipelines):
                pipeline_start = float('inf')
                pipeline_end = 0
                print(f"\nPipeline Instance {pipeline_idx + 1}:")
                print("-" * 40)

                # Print task assignments and timing in sequence order
                for task in pipeline_sequence:
                    if (task, pipeline_idx) in solution['assignments']:
                        start_time = solution['start_times'][(task, pipeline_idx)]
                        end_time = solution['end_times'][(task, pipeline_idx)]
                        pipeline_start = min(pipeline_start, start_time)
                        pipeline_end = max(pipeline_end, end_time)
                        core_type, count = solution['assignments'][(task, pipeline_idx)]
                        exec_time = solution['execution_times'][(task, pipeline_idx)]
                        print(f"{task:<20} -> {core_type} [{count} cores] "
                              f"(Start: {start_time:.6f} ms, Exec: {exec_time:.6f} ms, "
                              f"End: {end_time:.6f} ms)")

                pipeline_time = pipeline_end - pipeline_start
                print(f"\nPipeline Instance {pipeline_idx + 1} Total Time: {pipeline_time:.6f} ms")
                print(f"(Start: {pipeline_start:.6f} ms, End: {pipeline_end:.6f} ms)")

            # Print core type transitions
            print("\nCore Type Transitions:")
            transitions = 0
            for pipeline_idx in range(num_pipelines):
                prev_core_type = None
                for task in pipeline_sequence:
                    if (task, pipeline_idx) in solution['assignments']:
                        curr_core_type = solution['assignments'][(task, pipeline_idx)][0]
                        if prev_core_type and curr_core_type != prev_core_type:
                            transitions += 1
                            print(f"Pipeline {pipeline_idx + 1}: {prev_core_type} -> {curr_core_type} at {task}")
                        prev_core_type = curr_core_type

            print(f"\nTotal Core Type Transitions: {transitions}")
            print(f"Total Pipeline Time: {solution['total_time']:.6f} ms")

            # Print task distribution by core type
            print("\nTask Distribution by Core Type:")
            for pipeline_idx in range(num_pipelines):
                print(f"\nPipeline Instance {pipeline_idx + 1}:")
                core_type_tasks = {}

                # Initialize task lists for all core types including GPU
                for core_type in core_configs.keys():
                    core_type_tasks[core_type] = []

                for task in pipeline_sequence:
                    if (task, pipeline_idx) in solution['assignments']:
                        core_type = solution['assignments'][(task, pipeline_idx)][0]
                        core_count = solution['assignments'][(task, pipeline_idx)][1]
                        task_str = f"{task} ({core_count} cores)"
                        core_type_tasks[core_type].append(task_str)

                # Print tasks for each core type
                for core_type in core_configs.keys():
                    tasks_str = ', '.join(core_type_tasks[core_type]) if core_type_tasks[core_type] else "No tasks assigned"
                    print(f"{core_type} cores: {tasks_str}")
        else:
            print("No feasible solution found!")
            print("Please check task names and ensure all dependencies exist in benchmark data.")

        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
