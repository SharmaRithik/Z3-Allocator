import unittest
from z3 import *
import json

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
        # Setup that runs before each test
        self.filename = 'benchmark_data.json'
        self.times = read_benchmark_data(self.filename)
        self.tasks = ["BM_Morton", "BM_Sort", "BM_RemoveDup", "BM_RadixTree", "BM_EdgeCount", "BM_Octree"]

    def run_optimizer(self, times, max_blocks=3):
        # Define the optimizer
        opt = Optimize()

        # Variables for each task's core type
        task_cores = [Int(f"task_{i}_core") for i in range(len(times))]  # Adjust for the number of tasks

        # Variables to hold the total time for each core type
        time_small_cores = Real("time_small_cores")
        time_medium_cores = Real("time_medium_cores")
        time_big_cores = Real("time_big_cores")

        # Constraint for valid core choices and calculating total times
        for var in task_cores:
            opt.add(Or(var == 0, var == 1, var == 2))

        opt.add(time_small_cores == Sum([If(task_cores[i] == 0, times[i][0], 0) for i in range(len(times))]))
        opt.add(time_medium_cores == Sum([If(task_cores[i] == 1, times[i][1], 0) for i in range(len(times))]))
        opt.add(time_big_cores == Sum([If(task_cores[i] == 2, times[i][2], 0) for i in range(len(times))]))

        # Ensure contiguous allocation of cores by blocks
        block_start = [Bool(f"block_start_{i}") for i in range(len(times))]
        opt.add(block_start[0] == True)  # First task is always the start of a block

        for i in range(1, len(times)):
            opt.add(Implies(block_start[i], task_cores[i] != task_cores[i-1]))  # New block starts when core type changes
            opt.add(Implies(Not(block_start[i]), task_cores[i] == task_cores[i-1]))  # Same block means same core type

        # Allow only a limited number of blocks (contiguous segments)
        opt.add(Sum([If(block_start[i], 1, 0) for i in range(len(times))]) <= max_blocks)

        # Define a helper function to calculate the maximum of three real numbers
        def max3(x, y, z):
            return If(x > y, If(x > z, x, z), If(y > z, y, z))

        # Objective: minimize the maximum execution time among the cores
        max_time = max3(time_small_cores, time_medium_cores, time_big_cores)
        opt.minimize(max_time)

        # Solve the problem
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

    def test_optimal_solution(self):
        result = self.run_optimizer(self.times)
        self.assertIsNotNone(result, "Solver failed to find an optimal solution")
        self.assertTrue(result["optimal_max_time"] > 0, "Optimal max time should be greater than zero")

    def test_max_blocks_constraint(self):
        result = self.run_optimizer(self.times, max_blocks=2)
        self.assertIsNotNone(result, "Solver failed to find an optimal solution with max_blocks=2")

    def test_all_tasks_allocated(self):
        result = self.run_optimizer(self.times)
        self.assertIsNotNone(result, "Solver failed to find an optimal solution")
        self.assertEqual(len(result["core_allocations"]), len(self.tasks), "All tasks should be allocated")

    def test_block_start_constraints(self):
        result = self.run_optimizer(self.times)
        self.assertIsNotNone(result, "Solver failed to find an optimal solution")
        block_starts = [result["core_allocations"][i] != result["core_allocations"][i-1] for i in range(1, len(self.times))]
        block_starts = [True] + block_starts  # First task is always the start of a block
        self.assertLessEqual(sum(block_starts), 3, "Number of blocks should not exceed max_blocks")

if __name__ == '__main__':
    unittest.main()

