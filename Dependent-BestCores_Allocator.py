import pandas as pd
import re
from z3 import *

def parse_benchmark_file(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return None
    
    device_data = []
    current_device_id = None
    
    for line in lines:
        line = line.strip()
        device_id_match = re.search(r'on device:\s+(\S+)', line)
        if device_id_match:
            current_device_id = device_id_match.group(1)
            continue
            
        if line.startswith("ppl/") or line.startswith("[DEBUG]") or not line:
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
                
                device_data.append([
                    current_device_id,
                    'benchmark',
                    task_name,
                    core_type,
                    core_count,
                    iterations,
                    real_time,
                    cpu_time,
                    time_unit
                ])
                
    if not device_data:
        print("No data parsed from file.")
        return None
        
    return pd.DataFrame(device_data, columns=['Device_ID', 'Category', 'Task', 'Core_Type', 
                                            'Core_Count', 'Iterations', 'Real_Time', 
                                            'CPU_Time', 'Time_Unit'])

def solve_task_allocation(device_df, tasks, core_configs, task_dependencies, pipeline_sequence, num_pipelines, transfer_penalty=1.2):
    solver = Optimize()
    
    # Create task assignment variables
    task_vars = {}
    for task in pipeline_sequence:
        for core_type, counts in core_configs.items():
            for count in counts:
                var_name = f"{task}_{core_type}_{count}"
                task_vars[var_name] = Int(var_name)
                solver.add(Or(task_vars[var_name] == 0, task_vars[var_name] == 1))
    
    # Ensure exactly one assignment per task
    for task in pipeline_sequence:
        assignment_sum = Sum([task_vars[f"{task}_{core_type}_{count}"]
                            for core_type, counts in core_configs.items()
                            for count in counts])
        solver.add(assignment_sum == 1)
    
    # Track core utilization
    core_utilization = {}
    for core_type, counts in core_configs.items():
        max_cores = max(counts)
        core_utilization[core_type] = Real(f'util_{core_type}')
        
        util_expr = Sum([
            task_vars[f"{task}_{core_type}_{count}"] * (count / max_cores)
            for task in pipeline_sequence
            for count in counts
        ]) / len(pipeline_sequence)
        
        solver.add(core_utilization[core_type] >= 0)
        solver.add(core_utilization[core_type] <= 1)
        solver.add(core_utilization[core_type] == util_expr)
    
    # Calculate base execution times for tasks
    task_times = {}
    for task in pipeline_sequence:
        task_times[task] = Real(f'time_{task}')
        time_expr = Sum([
            task_vars[f"{task}_{core_type}_{count}"] * 
            device_df[(device_df['Task'] == task) &
                     (device_df['Core_Type'] == core_type) &
                     (device_df['Core_Count'] == str(count))]['Real_Time'].iloc[0]
            for core_type, counts in core_configs.items()
            for count in counts
        ])
        solver.add(task_times[task] == time_expr)
    
    # Create timing variables for each task instance
    start_times = {}
    end_times = {}
    
    # Calculate the theoretical minimum time between iterations (critical path)
    critical_path_time = Real('critical_path_time')
    solver.add(critical_path_time == Sum([task_times[task] for task in pipeline_sequence]))
    
    # Initialize timing variables for all pipeline instances
    for pipeline_idx in range(num_pipelines):
        for task in pipeline_sequence:
            start_key = f"{task}_{pipeline_idx}"
            start_times[start_key] = Real(start_key)
            end_times[start_key] = Real(f"end_{start_key}")
            
            # Basic timing constraint: end time = start time + execution time
            solver.add(end_times[start_key] == start_times[start_key] + task_times[task])
    
    # Add dependency constraints between tasks within the same pipeline
    for pipeline_idx in range(num_pipelines):
        for i, task in enumerate(pipeline_sequence):
            if i > 0:
                prev_task = pipeline_sequence[i-1]
                solver.add(start_times[f"{task}_{pipeline_idx}"] >= 
                          end_times[f"{prev_task}_{pipeline_idx}"])
    
    # Add pipeline overlap constraints with minimum offset
    min_pipeline_offset = Real('min_pipeline_offset')
    solver.add(min_pipeline_offset >= 0)
    
    for pipeline_idx in range(1, num_pipelines):
        # Each pipeline instance can start after a minimum offset from the previous instance
        solver.add(start_times[f"{pipeline_sequence[0]}_{pipeline_idx}"] >= 
                  start_times[f"{pipeline_sequence[0]}_{pipeline_idx-1}"] + min_pipeline_offset)
    
    # Create variables to track core type assignments
    core_type_vars = {}
    for task in pipeline_sequence:
        for core_type in core_configs.keys():
            var_name = f"{task}_{core_type}_used"
            core_type_vars[var_name] = Bool(var_name)
            
            # Link core type usage to task assignments
            solver.add(core_type_vars[var_name] == 
                      Or([task_vars[f"{task}_{core_type}_{count}"] == 1 
                          for count in core_configs[core_type]]))
    
    # Prevent resource conflicts between pipeline instances
    for pipeline_idx in range(num_pipelines):
        for next_idx in range(pipeline_idx + 1, num_pipelines):
            for task1 in pipeline_sequence:
                for task2 in pipeline_sequence:
                    for core_type in core_configs.keys():
                        # If both tasks use the same core type, they can't overlap
                        solver.add(Implies(
                            And(core_type_vars[f"{task1}_{core_type}_used"],
                                core_type_vars[f"{task2}_{core_type}_used"]),
                            Or(
                                end_times[f"{task1}_{pipeline_idx}"] <= start_times[f"{task2}_{next_idx}"],
                                end_times[f"{task2}_{next_idx}"] <= start_times[f"{task1}_{pipeline_idx}"]
                            )
                        ))
    
    # Calculate total pipeline time using Z3's maximum function
    last_end_times = [end_times[f"{task}_{num_pipelines-1}"] for task in pipeline_sequence]
    first_start_times = [start_times[f"{task}_0"] for task in pipeline_sequence]
    
    total_time = Real('total_time')
    
    # Create constraints for maximum end time and minimum start time
    max_end_time = last_end_times[0]
    min_start_time = first_start_times[0]
    
    for i in range(1, len(pipeline_sequence)):
        max_end_time = If(last_end_times[i] > max_end_time, last_end_times[i], max_end_time)
        min_start_time = If(first_start_times[i] < min_start_time, first_start_times[i], min_start_time)
    
    solver.add(total_time == max_end_time - min_start_time)
    
    # Calculate average core utilization
    avg_utilization = Real('avg_utilization')
    solver.add(avg_utilization == Sum([core_utilization[core_type] 
                                     for core_type in core_configs.keys()]) / len(core_configs))
    
    # Multi-objective optimization
    optimization_objective = total_time + (1 - avg_utilization) * total_time * 0.5
    solver.minimize(optimization_objective)
    
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
            'critical_path_time': safe_float(model[critical_path_time].as_decimal(6)),
            'min_pipeline_offset': safe_float(model[min_pipeline_offset].as_decimal(6)),
            'num_pipelines': num_pipelines,
            'pipeline_sequence': pipeline_sequence,
            'core_execution_times': {},
            'core_utilization': {}
        }
        
        # Store core utilization
        for core_type in core_configs.keys():
            solution['core_utilization'][core_type] = safe_float(model[core_utilization[core_type]].as_decimal(6))
        
        # Store task assignments and timing information
        for task in pipeline_sequence:
            for core_type, counts in core_configs.items():
                for count in counts:
                    var_name = f"{task}_{core_type}_{count}"
                    if model[task_vars[var_name]].as_long() == 1:
                        exec_time = safe_float(model[task_times[task]].as_decimal(6))
                        for pipeline_idx in range(num_pipelines):
                            solution['assignments'][(task, pipeline_idx)] = (core_type, count)
                            solution['execution_times'][(task, pipeline_idx)] = exec_time
                            
                            start_key = f"{task}_{pipeline_idx}"
                            solution['start_times'][(task, pipeline_idx)] = safe_float(model[start_times[start_key]].as_decimal(6))
                            solution['end_times'][(task, pipeline_idx)] = safe_float(model[end_times[start_key]].as_decimal(6))
        
        # Calculate core execution times
        for core_type in core_configs.keys():
            total_core_time = sum(solution['execution_times'][(task, 0)]
                                for task in pipeline_sequence
                                if solution['assignments'][(task, 0)][0] == core_type)
            solution['core_execution_times'][core_type] = total_core_time
        
        return solution
    else:
        return None

def main():
    # Define the fixed pipeline sequence
    pipeline_sequence = [
        'MortonCode',
        'RadixSort',
        'RemoveDuplicates',
        'BuildRadixTree',
        'EdgeCount',
        'EdgeOffset',
        'BuildOctree'
    ]

    # Define task dependencies based on sequence
    task_dependencies = {}
    for i in range(len(pipeline_sequence)-1):
        task_dependencies[pipeline_sequence[i+1]] = [pipeline_sequence[i]]
    task_dependencies['MortonCode'] = []  # First task has no dependencies

    # Get number of pipelines from user
    num_pipelines = int(input("Enter the number of times to run the pipeline: "))

    # Parse benchmark data
    df = parse_benchmark_file('tmp.out')
    if df is None:
        return

    print("Data successfully parsed into DataFrame.")
    print("\nPipeline Sequence:")
    print(" -> ".join(pipeline_sequence))
    print(f"\nPipeline will be executed {num_pipelines} times")

    # Process each device
    for device_id, device_df in df.groupby('Device_ID'):
        print(f"\nResults for Device: {device_id}")

        # Get core configurations
        core_configs = {}
        unique_core_types = sorted(device_df['Core_Type'].unique())
        for core_type in unique_core_types:
            core_counts = sorted([int(x) for x in device_df[device_df['Core_Type'] ==
                                                          core_type]['Core_Count'].unique()])
            if len(core_counts) > 0:
                core_configs[core_type] = core_counts

        # Print available core configurations
        for core_type in unique_core_types:
            if core_type in core_configs:
                print(f"{core_type}: {core_configs[core_type]}")

        print("\nCalculating optimal task allocation with dependencies...")

        # Use pipeline sequence as tasks list to maintain order
        tasks = pipeline_sequence

        # Solve task allocation
        solution = solve_task_allocation(device_df, tasks, core_configs, task_dependencies,
                                      pipeline_sequence, num_pipelines)

        if solution:
            print("\nPipeline Metrics:")
            print(f"Critical Path Time: {solution['critical_path_time']:.6f} ms")
            print(f"Minimum Pipeline Offset: {solution['min_pipeline_offset']:.6f} ms")
            print(f"Total Time for {num_pipelines} iterations: {solution['total_time']:.6f} ms")
            print(f"Effective throughput: {num_pipelines / solution['total_time']:.6f} iterations/ms")
            
            print("\nTask Overlap Analysis:")
            all_times = []
            for pipeline_idx in range(num_pipelines):
                pipeline_start = min(solution['start_times'][(task, pipeline_idx)] 
                                   for task in pipeline_sequence)
                pipeline_end = max(solution['end_times'][(task, pipeline_idx)] 
                                 for task in pipeline_sequence)
                all_times.append((pipeline_start, pipeline_end))
                print(f"Pipeline {pipeline_idx + 1}: {pipeline_start:.6f} -> {pipeline_end:.6f} ms")

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

                # Initialize task lists for all core types
                for core_type in core_configs.keys():
                    core_type_tasks[core_type] = []

                for task in pipeline_sequence:
                    if (task, pipeline_idx) in solution['assignments']:
                        core_type = solution['assignments'][(task, pipeline_idx)][0]
                        core_type_tasks[core_type].append(task)

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
