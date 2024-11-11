from z3 import *

# Define the optimizer
opt = Optimize()

# Variables for each task's core type
task_cores = [Int(f"task_{i}_core") for i in range(6)]  # 6 tasks

# Variables to hold the total time for each core type
time_small_cores = Real("time_small_cores")
time_medium_cores = Real("time_medium_cores")
time_big_cores = Real("time_big_cores")

# Time matrices from your data
times = [
    [11.8, 9.05, 5.61],  # Morton
    [20.0, 21.5, 9.21],  # Sort
    [12.0, 2.8, 1.83],   # Remove Duplicates
    [56.1, 45.6, 36.0],  # Radix tree
    [3.8, 2.26, 1.06],   # Edge count
    [28.3, 19.7, 12.2]   # Octree
]

# Constraint for valid core choices and calculating total times
for var in task_cores:
    opt.add(Or(var == 0, var == 1, var == 2))

opt.add(time_small_cores == Sum([If(task_cores[i] == 0, times[i][0], 0) for i in range(6)]))
opt.add(time_medium_cores == Sum([If(task_cores[i] == 1, times[i][1], 0) for i in range(6)]))
opt.add(time_big_cores == Sum([If(task_cores[i] == 2, times[i][2], 0) for i in range(6)]))

# Ensure contiguous allocation of cores by blocks
block_start = [Bool(f"block_start_{i}") for i in range(6)]
opt.add(block_start[0] == True)  # First task is always the start of a block

for i in range(1, 6):
    opt.add(Implies(block_start[i], task_cores[i] != task_cores[i-1]))  # New block starts when core type changes
    opt.add(Implies(Not(block_start[i]), task_cores[i] == task_cores[i-1]))  # Same block means same core type

# Allow only a limited number of blocks (contiguous segments)
max_blocks = 3  # Adjust this number as needed
opt.add(Sum([If(block_start[i], 1, 0) for i in range(6)]) <= max_blocks)

# Define a helper function to calculate the maximum of three real numbers
def max3(x, y, z):
    return If(x > y, If(x > z, x, z), If(y > z, y, z))

# Objective: minimize the maximum execution time among the cores
max_time = max3(time_small_cores, time_medium_cores, time_big_cores)
opt.minimize(max_time)

# Solve the problem
if opt.check() == sat:
    model = opt.model()
    core_allocations = [model.eval(task_cores[i]) for i in range(6)]
    times_small = model.eval(time_small_cores)
    times_medium = model.eval(time_medium_cores)
    times_big = model.eval(time_big_cores)
    optimal_max_time = model.eval(max_time)
    print("Optimal core allocations:", core_allocations)
    print("Total time on 4 small cores:", times_small)
    print("Total time on 2 medium cores:", times_medium)
    print("Total time on 2 big cores:", times_big)
    print("Optimal total time to complete all tasks:", optimal_max_time)
else:
    print("Failed to find an optimal solution")

