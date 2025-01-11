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
    
    # Track which core type is used at each position
    position_core_type = {}
    for pos, task in enumerate(pipeline_sequence):
        for core_type in core_configs.keys():
            var_name = f"{pos}_{core_type}"
            position_core_type[var_name] = Bool(var_name)
            # Link to task assignments
            solver.add(position_core_type[var_name] == 
                      Or([task_vars[f"{task}_{core_type}_{count}"] == 1 
                          for count in core_configs[core_type]]))
    
    # Track core types that have been used up to each position
    core_used_before = {}
    for core_type in core_configs.keys():
        for pos in range(len(pipeline_sequence)):
            var_name = f"used_before_{core_type}_{pos}"
            core_used_before[var_name] = Bool(var_name)
            
            if pos == 0:
                # For first position, used_before is false
                solver.add(core_used_before[var_name] == False)
            else:
                # For other positions, core is used before if it was used before previous position
                # or was used in the previous position
                solver.add(core_used_before[var_name] == 
                         Or(core_used_before[f"used_before_{core_type}_{pos-1}"],
                            position_core_type[f"{pos-1}_{core_type}"]))
    
    # Prevent using a core type if it was used before but not in the immediately previous position
    for pos in range(1, len(pipeline_sequence)):
        for core_type in core_configs.keys():
            current_use = position_core_type[f"{pos}_{core_type}"]
            prev_use = position_core_type[f"{pos-1}_{core_type}"]
            used_before = core_used_before[f"used_before_{core_type}_{pos}"]
            
            # If we use this core type at this position:
            # Either it must have been used in the previous position
            # Or it must have never been used before
            solver.add(Implies(current_use,
                             Or(prev_use,
                                Not(used_before))))
    
    # Calculate task execution times
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
    
    # Create timing variables for first pipeline instance
    start_times = {}
    end_times = {}
    
    # Initialize timing for first pipeline
    prev_end_time = Real('start')
    solver.add(prev_end_time == 0)
    
    for task in pipeline_sequence:
        start_times[task] = Real(f'start_{task}')
        end_times[task] = Real(f'end_{task}')
        
        solver.add(start_times[task] >= prev_end_time)
        solver.add(end_times[task] == start_times[task] + task_times[task])
        prev_end_time = end_times[task]
    
    # Calculate total time
    total_time = Real('total_time')
    solver.add(total_time == prev_end_time)  # Last end time
    
    # Minimize total execution time
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
            'core_execution_times': {},
            'core_utilization': {}
        }
        
        # Get base assignments and execution times
        base_assignments = {}
        base_times = {}
        for task in pipeline_sequence:
            for core_type, counts in core_configs.items():
                for count in counts:
                    var_name = f"{task}_{core_type}_{count}"
                    if model[task_vars[var_name]].as_long() == 1:
                        base_assignments[task] = (core_type, count)
                        base_times[task] = safe_float(model[task_times[task]].as_decimal(6))
                        break
        
        # Store assignments and timing for all pipeline instances
        for pipeline_idx in range(num_pipelines):
            for task in pipeline_sequence:
                solution['assignments'][(task, pipeline_idx)] = base_assignments[task]
                solution['execution_times'][(task, pipeline_idx)] = base_times[task]
                
                if pipeline_idx == 0:
                    solution['start_times'][(task, pipeline_idx)] = safe_float(model[start_times[task]].as_decimal(6))
                    solution['end_times'][(task, pipeline_idx)] = safe_float(model[end_times[task]].as_decimal(6))
                else:
                    # For subsequent instances, add appropriate offset
                    offset = solution['total_time'] * pipeline_idx / num_pipelines
                    solution['start_times'][(task, pipeline_idx)] = solution['start_times'][(task, 0)] + offset
                    solution['end_times'][(task, pipeline_idx)] = solution['end_times'][(task, 0)] + offset
        
        # Calculate core execution times and utilization
        for core_type in core_configs.keys():
            total_core_time = sum(base_times[task]
                                for task in pipeline_sequence
                                if base_assignments[task][0] == core_type)
            solution['core_execution_times'][core_type] = total_core_time
            solution['core_utilization'][core_type] = total_core_time / solution['total_time']
        
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
            # Calculate single pipeline time from first instance
            first_pipeline_start = min(solution['start_times'][(task, 0)] 
                                     for task in pipeline_sequence)
            first_pipeline_end = max(solution['end_times'][(task, 0)] 
                                   for task in pipeline_sequence)
            single_pipeline_time = first_pipeline_end - first_pipeline_start
            
            print(f"Single Pipeline Time: {single_pipeline_time:.6f} ms")
            print(f"Total Time for {num_pipelines} iterations: {solution['total_time']:.6f} ms")
            print(f"Effective throughput: {num_pipelines / solution['total_time']:.6f} iterations/ms")
            
            print("\nCore Utilization:")
            for core_type, utilization in solution['core_utilization'].items():
                print(f"{core_type}: {utilization*100:.2f}%")
            
            print("\nTask Assignments and Timing:")
            for pipeline_idx in range(num_pipelines):
                print(f"\nPipeline Instance {pipeline_idx + 1}:")
                pipeline_start = min(solution['start_times'][(task, pipeline_idx)] 
                                   for task in pipeline_sequence)
                pipeline_end = max(solution['end_times'][(task, pipeline_idx)] 
                                 for task in pipeline_sequence)
                
                print(f"Pipeline start: {pipeline_start:.6f} ms, end: {pipeline_end:.6f} ms")
                print("-" * 40)
                
                for task in pipeline_sequence:
                    core_type, count = solution['assignments'][(task, pipeline_idx)]
                    start_time = solution['start_times'][(task, pipeline_idx)]
                    end_time = solution['end_times'][(task, pipeline_idx)]
                    exec_time = solution['execution_times'][(task, pipeline_idx)]
                    
                    print(f"{task:<20} -> {core_type} [{count}] "
                          f"(Start: {start_time:.6f} ms, "
                          f"Exec: {exec_time:.6f} ms, "
                          f"End: {end_time:.6f} ms)")

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

            print("\nCore Execution Times:")
            for core_type, time in solution['core_execution_times'].items():
                print(f"{core_type}: {time:.6f} ms")
        else:
            print("No feasible solution found!")
            print("Please check task names and ensure all dependencies exist in benchmark data.")

        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
