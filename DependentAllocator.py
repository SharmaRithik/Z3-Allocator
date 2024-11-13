import pandas as pd
import re
from z3 import *

class TaskDependencyGraph:
    def __init__(self, dependencies):
        self.dependencies = dependencies
        self.graph = self._build_graph()
        self.ordered_tasks = self._topological_sort()
        
    def _build_graph(self):
        graph = {}
        all_tasks = set()
        for task, deps in self.dependencies.items():
            all_tasks.add(task)
            all_tasks.update(deps)
        for task in all_tasks:
            graph[task] = []
        for task, deps in self.dependencies.items():
            for dep in deps:
                graph[task].extend([dep])
        return graph
    
    def _topological_sort(self):
        def dfs(node, visited, temp, order):
            if node in temp:
                raise ValueError(f"Cycle detected in task dependencies at {node}")
            if node in visited:
                return
            temp.add(node)
            for neighbor in self.graph.get(node, []):
                dfs(neighbor, visited, temp, order)
            temp.remove(node)
            visited.add(node)
            order.append(node)
            
        visited = set()
        temp = set()
        order = []
        for node in self.graph:
            if node not in visited:
                dfs(node, visited, temp, order)
        return list(reversed(order))
    
    def get_dependencies(self, task):
        return self.dependencies.get(task, [])
    
    def get_ordered_tasks(self):
        return self.ordered_tasks

def solve_task_allocation(device_df, tasks, core_configs, task_dependencies, pipeline_sequence, num_pipelines, transfer_penalty=1.2):
    solver = Optimize()
    task_vars = {}
    for pipeline_idx in range(num_pipelines):
        for task in tasks:
            for core_type, counts in core_configs.items():
                for count in counts:
                    var_name = f"{task}_{pipeline_idx}_{core_type}_{count}"
                    task_vars[var_name] = Int(var_name)
                    solver.add(Or(task_vars[var_name] == 0, task_vars[var_name] == 1))
    for pipeline_idx in range(num_pipelines):
        for task in tasks:
            assignment_sum = Sum([task_vars[f"{task}_{pipeline_idx}_{core_type}_{count}"]
                                for core_type, counts in core_configs.items()
                                for count in counts])
            solver.add(assignment_sum == 1)
    task_times = {}
    for pipeline_idx in range(num_pipelines):
        for task in tasks:
            task_times[f"{task}_{pipeline_idx}"] = Real(f'time_{task}_{pipeline_idx}')
            time_expr = Sum([
                task_vars[f"{task}_{pipeline_idx}_{core_type}_{count}"] * 
                device_df[(device_df['Task'] == task) & 
                         (device_df['Core_Type'] == core_type) & 
                         (device_df['Core_Count'] == str(count))]['Real_Time'].iloc[0]
                for core_type, counts in core_configs.items()
                for count in counts
            ])
            solver.add(task_times[f"{task}_{pipeline_idx}"] == time_expr)
    start_times = {}
    end_times = {}
    for pipeline_idx in range(num_pipelines):
        for task in tasks:
            start_times[f"{task}_{pipeline_idx}"] = Real(f'start_{task}_{pipeline_idx}')
            end_times[f"{task}_{pipeline_idx}"] = Real(f'end_{task}_{pipeline_idx}')
            solver.add(start_times[f"{task}_{pipeline_idx}"] >= 0)
            solver.add(end_times[f"{task}_{pipeline_idx}"] == 
                      start_times[f"{task}_{pipeline_idx}"] + 
                      task_times[f"{task}_{pipeline_idx}"])
    for pipeline_idx in range(num_pipelines):
        for i in range(len(pipeline_sequence) - 1):
            current_task = pipeline_sequence[i]
            next_task = pipeline_sequence[i + 1]
            if current_task in tasks and next_task in tasks:
                solver.add(start_times[f"{next_task}_{pipeline_idx}"] >= 
                          end_times[f"{current_task}_{pipeline_idx}"])
    for task_idx, task in enumerate(pipeline_sequence):
        for pipeline_idx in range(num_pipelines - 1):
            solver.add(start_times[f"{task}_{pipeline_idx + 1}"] >= 
                      end_times[f"{task}_{pipeline_idx}"])
            for core_type1, counts1 in core_configs.items():
                for count1 in counts1:
                    for core_type2, counts2 in core_configs.items():
                        for count2 in counts2:
                            if core_type1 != core_type2:
                                penalty_condition = And(
                                    task_vars[f"{task}_{pipeline_idx + 1}_{core_type1}_{count1}"] == 1,
                                    task_vars[f"{task}_{pipeline_idx}_{core_type2}_{count2}"] == 1
                                )
                                solver.add(
                                    Implies(
                                        penalty_condition,
                                        start_times[f"{task}_{pipeline_idx + 1}"] >= 
                                        end_times[f"{task}_{pipeline_idx}"] + 
                                        (task_times[f"{task}_{pipeline_idx + 1}"] * (transfer_penalty - 1))
                                    )
                                )
    total_time = Real('total_time')
    for pipeline_idx in range(num_pipelines):
        for task in tasks:
            solver.add(total_time >= end_times[f"{task}_{pipeline_idx}"])
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
            'pipeline_sequence': pipeline_sequence
        }
        for pipeline_idx in range(num_pipelines):
            for task in tasks:
                for core_type, counts in core_configs.items():
                    for count in counts:
                        var_name = f"{task}_{pipeline_idx}_{core_type}_{count}"
                        if model[task_vars[var_name]].as_long() == 1:
                            solution['assignments'][(task, pipeline_idx)] = (core_type, count)
                task_key = f"{task}_{pipeline_idx}"
                solution['execution_times'][(task, pipeline_idx)] = safe_float(model[task_times[task_key]].as_decimal(6))
                solution['start_times'][(task, pipeline_idx)] = safe_float(model[start_times[task_key]].as_decimal(6))
                solution['end_times'][(task, pipeline_idx)] = safe_float(model[end_times[task_key]].as_decimal(6))
        return solution
    else:
        return None

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
            if len(task_details) == 5:
                device_data.append([current_device_id] + task_details[:4] + 
                                 [iterations, real_time, cpu_time, time_unit])
    if not device_data:
        print("No data parsed from file.")
        return None
    return pd.DataFrame(device_data, columns=['Device_ID', 'Category', 'Task', 'Core_Type', 
                                            'Core_Count', 'Iterations', 'Real_Time', 
                                            'CPU_Time', 'Time_Unit'])

def main():
    task_dependencies = {
        'BuildOctree': ['EdgeOffset'],
        'EdgeOffset': ['EdgeCount'],
        'EdgeCount': ['BuildRadixTree'],
        'BuildRadixTree': ['RemoveDuplicates'],
        'RemoveDuplicates': ['RadixSort'],
        'RadixSort': ['MortonCode'],
        'MortonCode': []
    }
    pipeline_sequence = [
        'MortonCode',
        'RadixSort',
        'RemoveDuplicates',
        'BuildRadixTree',
        'EdgeCount',
        'EdgeOffset',
        'BuildOctree'
    ]
    num_pipelines = int(input("Enter the number of times to run the pipeline: "))
    df = parse_benchmark_file('tmp.out')
    if df is None:
        return
    print("Data successfully parsed into DataFrame.")
    print("\nAvailable tasks in benchmark data:")
    print(sorted(df['Task'].unique()))
    print(f"\nPipeline will be executed {num_pipelines} times")
    print("Pipeline Sequence:")
    print(" -> ".join(pipeline_sequence))
    for device_id, device_df in df.groupby('Device_ID'):
        print(f"\nResults for Device: {device_id}")
        core_configs = {}
        for core_type in sorted(device_df['Core_Type'].unique()):
            core_counts = sorted([int(x) for x in device_df[device_df['Core_Type'] == 
                                                          core_type]['Core_Count'].unique()])
            if len(core_counts) > 0:
                core_configs[core_type] = core_counts
        for core_type, counts in core_configs.items():
            print(f"{core_type}: {counts}")
        tasks = sorted(device_df['Task'].unique())
        print("\nTasks to be allocated:", tasks)
        print("\nCalculating optimal task allocation with dependencies...")
        solution = solve_task_allocation(device_df, tasks, core_configs, task_dependencies, 
                                      pipeline_sequence, num_pipelines)
        if solution:
            print("\nOptimal Pipeline Allocation:")
            print("-" * 80)
            for pipeline_idx in range(num_pipelines):
                pipeline_start = float('inf')
                pipeline_end = 0
                print(f"\nPipeline Instance {pipeline_idx + 1}:")
                print("-" * 40)
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
        else:
            print("No feasible solution found!")
            print("Please check task names and ensure all dependencies exist in benchmark data.")
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()

