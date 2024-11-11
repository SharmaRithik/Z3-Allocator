import unittest
from z3 import *
import json
import itertools

def generate_benchmark_data(num_tasks=6):
    tasks = ["BM_Morton", "BM_Sort", "BM_RemoveDup", "BM_RadixTree", "BM_EdgeCount", "BM_Octree"]
    benchmark_data = {"small_cores": [], "medium_cores": [], "big_cores": []}

    for i in range(num_tasks):
        benchmark_data["small_cores"].append({
            "task": tasks[i % len(tasks)],
            "threads": 4,
            "time": round(10 + i * 0.5, 2)
        })
        benchmark_data["medium_cores"].append({
            "task": tasks[i % len(tasks)],
            "threads": 2,
            "time": round(5 + i * 0.3, 2)
        })
        benchmark_data["big_cores"].append({
            "task": tasks[i % len(tasks)],
            "threads": 2,
            "time": round(3 + i * 0.1, 2)
        })
    
    return benchmark_data

def save_benchmark_data(benchmark_data, filename='benchmark_data.json'):
    with open(filename, 'w') as f:
        json.dump(benchmark_data, f, indent=2)

def read_benchmark_data(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    tasks = ["BM_Morton", "BM_Sort", "BM_RemoveDup", "BM_RadixTree", "BM_EdgeCount", "BM_Octree"]
    times = []
    for task in tasks:
        task_times = []
        for core_type in ["small_cores", "medium_cores", "big_cores"]:
            core_times = next((item["time"] for item in data[core_type] if item["task"] == task), None)
            task_times.append(core_times)
        times.append(task_times)
    return times

class TestBasicAllocator(unittest.TestCase):

    def setUp(self):
        self.tasks = ["BM_Morton", "BM_Sort", "BM_RemoveDup", "BM_RadixTree", "BM_EdgeCount", "BM_Octree"]

    def run_optimizer(self, times, max_blocks=3):
        opt = Optimize()
        task_cores = [Int(f"task_{i}_core") for i in range(len(times))]
        time_small_cores = Real("time_small_cores")
        time_medium_cores = Real("time_medium_cores")
        time_big_cores = Real("time_big_cores")

        for var in task_cores:
            opt.add(Or(var == 0, var == 1, var == 2))

        opt.add(time_small_cores == Sum([If(task_cores[i] == 0, times[i][0], 0) for i in range(len(times))]))
        opt.add(time_medium_cores == Sum([If(task_cores[i] == 1, times[i][1], 0) for i in range(len(times))]))
        opt.add(time_big_cores == Sum([If(task_cores[i] == 2, times[i][2], 0) for i in range(len(times))]))

        block_start = [Bool(f"block_start_{i}") for i in range(len(times))]
        opt.add(block_start[0] == True)

        for i in range(1, len(times)):
            opt.add(Implies(block_start[i], task_cores[i] != task_cores[i-1]))
            opt.add(Implies(Not(block_start[i]), task_cores[i] == task_cores[i-1]))

        opt.add(Sum([If(block_start[i], 1, 0) for i in range(len(times))]) <= max_blocks)

        def max3(x, y, z):
            return If(x > y, If(x > z, x, z), If(y > z, y, z))

        max_time = max3(time_small_cores, time_medium_cores, time_big_cores)
        opt.minimize(max_time)

        if opt.check() == sat:
            model = opt.model()
            core_allocations = [model.eval(task_cores[i]).as_long() for i in range(len(times))]
            times_small = model.eval(time_small_cores).as_decimal(2)
            times_medium = model.eval(time_medium_cores).as_decimal(2)
            times_big = model.eval(time_big_cores).as_decimal(2)
            optimal_max_time = model.eval(max_time).as_decimal(2)
            return {
                "core_allocations": core_allocations,
                "times_small": float(times_small),
                "times_medium": float(times_medium),
                "times_big": float(times_big),
                "optimal_max_time": float(optimal_max_time)
            }
        else:
            return None

def create_test_case(benchmark_data, max_blocks):

    def test_case(self):
        save_benchmark_data(benchmark_data)
        times = read_benchmark_data('benchmark_data.json')
        result = self.run_optimizer(times, max_blocks)
        self.assertIsNotNone(result, "Solver failed to find an optimal solution")
        self.assertTrue(result["optimal_max_time"] > 0, "Optimal max time should be greater than zero")
        self.assertEqual(len(result["core_allocations"]), len(self.tasks), "All tasks should be allocated")
        block_starts = [result["core_allocations"][i] != result["core_allocations"][i-1] for i in range(1, len(times))]
        block_starts = [True] + block_starts
        self.assertLessEqual(sum(block_starts), max_blocks, f"Number of blocks should not exceed {max_blocks}")

    return test_case

def add_test_cases():
    test_id = 1
    for _ in range(50):
        benchmark_data = generate_benchmark_data()
        test_name = f'test_optimizer_max_blocks_3_case_{test_id}'
        test_case = create_test_case(benchmark_data, 3)
        setattr(TestBasicAllocator, test_name, test_case)
        test_id += 1

    for _ in range(30):
        benchmark_data = generate_benchmark_data()
        test_name = f'test_optimizer_max_blocks_2_case_{test_id}'
        test_case = create_test_case(benchmark_data, 2)
        setattr(TestBasicAllocator, test_name, test_case)
        test_id += 1

    for _ in range(20):
        benchmark_data = generate_benchmark_data()
        test_name = f'test_optimizer_max_blocks_1_case_{test_id}'
        test_case = create_test_case(benchmark_data, 1)
        setattr(TestBasicAllocator, test_name, test_case)
        test_id += 1

if __name__ == '__main__':
    add_test_cases()
    unittest.main()

