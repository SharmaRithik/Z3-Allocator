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
                               for count in core_configs[core_type]])
            first_use_constraints.append(
                And(task_uses_core,
                    And([Not(Or([task_vars[f"{pipeline_sequence[j]}_{core_type}_{count}"] == 1
                                for count in core_configs[core_type]]))
                         for j in range(pos)]))
            )
        solver.add(Or([And(first_use_constraints[pos],
                          core_first_use[core_type] == pos)
                      for pos in range(len(pipeline_sequence))]
                     + [And(And([Not(Or([task_vars[f"{task}_{core_type}_{count}"] == 1
                                        for count in core_configs[core_type]]))
                                for task in pipeline_sequence]),
                           core_first_use[core_type] == len(pipeline_sequence))]))
        
        # Find last use
        last_use_constraints = []
        for pos, task in enumerate(pipeline_sequence):
            task_uses_core = Or([task_vars[f"{task}_{core_type}_{count}"] == 1
                               for count in core_configs[core_type]])
            last_use_constraints.append(
                And(task_uses_core,
                    And([Not(Or([task_vars[f"{pipeline_sequence[j]}_{core_type}_{count}"] == 1
                                for count in core_configs[core_type]]))
                         for j in range(pos + 1, len(pipeline_sequence))]))
            )
        solver.add(Or([And(last_use_constraints[pos],
                          core_last_use[core_type] == pos)
                      for pos in range(len(pipeline_sequence))]
                     + [And(And([Not(Or([task_vars[f"{task}_{core_type}_{count}"] == 1
                                        for count in core_configs[core_type]]))
                                for task in pipeline_sequence]),
                           core_last_use[core_type] == -1)]))

    # Ensure continuous use of core types (no gaps)
    for core_type in core_configs.keys():
        for pos in range(1, len(pipeline_sequence) - 1):
            task = pipeline_sequence[pos]
            # If this position uses this core type
            task_uses_core = Or([task_vars[f"{task}_{core_type}_{count}"] == 1
                               for count in core_configs[core_type]])
            
            # If this is between first and last use, must use the core type
            solver.add(Implies(And(core_first_use[core_type] < pos,
                                 core_last_use[core_type] > pos),
                             task_uses_core))
    
    # Calculate individual task execution times
    task_exec_times = {}
    for task in pipeline_sequence:
        for core_type, counts in core_configs.items():
            for count in counts:
                task_exec_times[(task, core_type, count)] = device_df[
                    (device_df['Task'] == task) &
                    (device_df['Core_Type'] == core_type) &
                    (device_df['Core_Count'] == str(count))
                ]['Real_Time'].iloc[0]
    
    # Calculate core type total execution times
    core_total_times = {}
    for core_type in core_configs.keys():
        core_total_times[core_type] = Real(f'total_time_{core_type}')
        time_expr = Sum([
            task_vars[f"{task}_{core_type}_{count}"] * task_exec_times[(task, core_type, count)]
            for task in pipeline_sequence
            for count in core_configs[core_type]
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
                    task_vars[f"{task}_{core_type}_{count}"] * task_exec_times[(task, core_type, count)]
                    for core_type, counts in core_configs.items()
                    for count in counts
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
    
    # Rest of the function (solution extraction) remains the same
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
            for core_type, counts in core_configs.items():
                for count in counts:
                    var_name = f"{task}_{core_type}_{count}"
                    if model[task_vars[var_name]].as_long() == 1:
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
                        print(f"{task:<20} -> {core_type} [{count}] "
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
