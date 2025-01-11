import pandas as pd
import re
from z3 import *

"""
Technical Specification: Task Allocation Solver with Z3 Optimization

This solver implements an optimal task allocation strategy for heterogeneous computing systems
using the Z3 SMT solver with optimization capabilities. It addresses the challenge of mapping
multiple computational tasks to different types of processing cores while minimizing the overall
execution time.

Key Features:
1. Multi-Core Configuration Support
   - Handles various core types (CPU, GPU, NPU, etc.)
   - Supports different core counts for each type
   - Allows for heterogeneous processing capabilities

2. Constraint Satisfaction
   - Ensures each task is assigned to exactly one core configuration
   - Maintains exclusive task assignments
   - Considers core-specific execution times

3. Optimization Objectives
   - Minimizes the maximum execution time across all core types
   - Balances workload distribution
   - Considers parallel execution capabilities

Input Parameters:
- device_df: DataFrame containing benchmark results for tasks on different core configurations
- tasks: List of tasks to be allocated
- core_configs: Dictionary mapping core types to available core counts

Output:
Returns a solution dictionary containing:
- assignments: Optimal task-to-core assignments
- execution_times: Execution time for each core type
- total_time: Overall execution time of the solution

Algorithm Complexity:
- Time: NP-hard (depends on Z3 solver implementation)
- Space: O(T * C * N) where T = tasks, C = core types, N = max core count

Usage Notes:
- Suitable for static task allocation in heterogeneous computing systems
- Can be extended for dynamic scheduling scenarios
- Provides deterministic solutions for identical inputs
"""
def solve_task_allocation(device_df, tasks, core_configs):
    solver = Optimize()
    
    task_vars = {}
    for task in tasks:
        for core_type, counts in core_configs.items():
            for count in counts:
                var_name = f"{task}_{core_type}_{count}"
                task_vars[var_name] = Int(var_name)
                solver.add(Or(task_vars[var_name] == 0, task_vars[var_name] == 1))

    for task in tasks:
        assignment_sum = Sum([task_vars[f"{task}_{core_type}_{count}"]
                            for core_type, counts in core_configs.items()
                            for count in counts])
        solver.add(assignment_sum == 1)

    exec_times = {}
    for core_type in core_configs.keys():
        exec_times[core_type] = Real(f'exec_time_{core_type}')
        
        time_sum = Sum([
            task_vars[f"{task}_{core_type}_{count}"] * 
            device_df[(device_df['Task'] == task) & 
                     (device_df['Core_Type'] == core_type) & 
                     (device_df['Core_Count'] == str(count))]['Real_Time'].iloc[0]
            for task in tasks
            for count in core_configs[core_type]
        ])
        
        solver.add(exec_times[core_type] == time_sum)

    total_time = Real('total_time')
    for core_type in core_configs.keys():
        solver.add(total_time >= exec_times[core_type])

    solver.add(Or([total_time == exec_times[core_type] for core_type in core_configs.keys()]))

    solver.minimize(total_time)

    if solver.check() == sat:
        model = solver.model()
        
        solution = {
            'assignments': {},
            'execution_times': {},
            'total_time': 0
        }
        
        for task in tasks:
            for core_type, counts in core_configs.items():
                for count in counts:
                    var_name = f"{task}_{core_type}_{count}"
                    if model[task_vars[var_name]].as_long() == 1:
                        solution['assignments'][task] = (core_type, count)
        
        for core_type in core_configs.keys():
            solution['execution_times'][core_type] = float(model[exec_times[core_type]].as_decimal(6))
        
        solution['total_time'] = float(model[total_time].as_decimal(6))
        
        return solution
    else:
        return None

file_path = 'tmp.out'
try:
    with open(file_path, 'r') as file:
        lines = file.readlines()
except FileNotFoundError:
    print(f"File {file_path} not found.")
    exit()

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
        
        if len(task_details) == 5:
            device_data.append([current_device_id] + task_details[:4] + [iterations, real_time, cpu_time, time_unit])

if not device_data:
    print("No data parsed from file.")
    exit()

df = pd.DataFrame(device_data, columns=['Device_ID', 'Category', 'Task', 'Core_Type', 'Core_Count', 
                                      'Iterations', 'Real_Time', 'CPU_Time', 'Time_Unit'])

print("Data successfully parsed into DataFrame.")

for device_id, device_df in df.groupby('Device_ID'):
    print(f"\nResults for Device: {device_id}")
    
    core_configs = {}
    for core_type in sorted(device_df['Core_Type'].unique()):
        core_counts = sorted([int(x) for x in device_df[device_df['Core_Type'] == core_type]['Core_Count'].unique()])
        if len(core_counts) > 0:
            core_configs[core_type] = core_counts
    
    for core_type, counts in core_configs.items():
        print(f"{core_type} {counts}")
    
    print("\n")

    tasks = sorted(device_df['Task'].unique())
    
    print("Execution Times per Task and Core Configuration:")
    print("\n{:<15}{:<12}".format("Config Index", "Core Config"), end="")
    for task in tasks:
        print("{:<15}".format(task), end="")
    print("{:<15}".format("Total Time"))
    print("-" * (27 + 15 * (len(tasks) + 1)))

    all_configs = []
    for core_type, counts in core_configs.items():
        for count in counts:
            all_configs.append((core_type, count))

    best_configs = {}
    best_times = {}

    for idx, (core_type, count) in enumerate(all_configs, 1):
        index_label = f"Config {idx}"
        core_label = f"{core_type} [{count}]"
        print("{:<15}{:<12}".format(index_label, core_label), end="")
        
        total_time = 0
        
        for task in tasks:
            mask = (device_df['Core_Type'] == core_type) & \
                  (device_df['Core_Count'] == str(count)) & \
                  (device_df['Task'] == task)
            if mask.any():
                exec_time = device_df[mask]['Real_Time'].iloc[0]
                total_time += exec_time
                print("{:<15}".format(f"{core_type} [{count}]"), end="")
                
                if task not in best_times or exec_time < best_times[task]:
                    best_times[task] = exec_time
                    best_configs[task] = (core_type, count)
            else:
                print("{:<15}".format("N/A"), end="")
        
        print("{:<15.6f}".format(total_time))

    print("{:<15}{:<12}".format("Config Best", "Best"), end="")
    total_best_time = 0
    for task in tasks:
        if task in best_configs:
            core_type, count = best_configs[task]
            print("{:<15}".format(f"{core_type} [{count}]"), end="")
            total_best_time += best_times[task]
        else:
            print("{:<15}".format("N/A"), end="")
    print("{:<15.6f}".format(total_best_time))

    print("\n")
    
    print("\nCalculating optimal task allocation...")
    solution = solve_task_allocation(device_df, tasks, core_configs)
    
    if solution:
        print("\nOptimal Task Allocation:")
        print("-" * 50)
        print("Task Assignments:")
        for task, (core_type, count) in sorted(solution['assignments'].items()):
            print(f"{task:<20} -> {core_type} [{count}]")
        
        print("\nExecution Times per Core Type:")
        for core_type in sorted(solution['execution_times'].keys()):
            print(f"{core_type:<10} : {solution['execution_times'][core_type]:.6f} ms")
        
        print(f"\nTotal Execution Time: {solution['total_time']:.6f} ms")
        speedup = total_best_time / solution['total_time']
        speedup_percent = (speedup - 1) * 100
        print(f"Speedup vs Config Best: {speedup:.2f}x ({speedup_percent:+.1f}%)")
    else:
        print("No feasible solution found!")
    
    print("\n")
    print(device_df)
    print("\n" + "="*50 + "\n")
