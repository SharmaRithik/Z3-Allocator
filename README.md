# Z3 Task Allocator

This tool uses the **Z3 SMT Solver** to optimize task allocation across heterogeneous computing platforms (Android and Jetson). It intelligently schedules pipeline stages across different processing units (CPU cores and GPU) to minimize execution time while considering hardware constraints and dependencies.

## How it Works

The allocator:

- Takes **CPU and GPU benchmark data** as input
- Automatically detects the **target platform** (Android/Jetson) and available compute resources
- Uses the **Z3 solver** to:
  - Assign tasks to **optimal core configurations**
  - Minimize **total execution time**
  - Balance workload across cores
  - Maintain continuous core usage
  - Handle pipeline dependencies

Provides detailed execution analysis including:

- Per-stage timing and core assignments
- Core type transitions
- Total pipeline execution time
- Task distribution across cores

## Supported Platforms

### Android

- Small cores (1-4 cores)
- Medium cores (1-2 cores)
- Big cores (1-2 cores)
- GPU (Vulkan)

### Jetson

- Small cores (1-6 cores)
- GPU (CUDA)

---

## Usage:

```bash
python3 Z3-Allocator.py <cpu_benchmark_file> <gpu_benchmark_file>
```

### For Android:

```bash
python3 Z3-Allocator.py android_tree_cpu.csv android_tree_vk.csv
```

### For Jetson:

```bash
python3 Z3-Allocator.py jetson_tree_cpu.csv jetson_tree_cuda.csv
```

---

## Example Results

### Android Platform:

**Results for Device: 3A021JEHN02756**

**Core Configuration:**
- Small cores: [0, 1, 2, 3] (Available counts: [1, 2, 3, 4])
- Medium cores: [4, 5] (Available counts: [1, 2])
- Big cores: [6, 7] (Available counts: [1, 2])
- GPU cores: [8] (Available counts: [1])

**Pipeline Allocation Summary:**
- Total Pipeline Time: **15.967096 ms**
- Core Type Transitions: **15**
- Optimal Task Distribution:
  - Small cores: `run_stage5`, `run_stage6`, `run_stage7` (4 cores each)
  - Medium cores: `run_stage1` (2 cores)
  - Big cores: `run_stage2` (2 cores), `run_stage3` (1 core)
  - GPU: `run_stage4`

---

### Jetson Platform:

**Results for Device: jetson**

**Core Configuration:**
- Small cores: [1, 2, 3, 4, 5, 6] (Available counts: [1, 2, 3, 4, 5, 6])
- GPU cores: [1] (Available counts: [1])

**Pipeline Allocation Summary:**
- Total Pipeline Time: **22.970263 ms**
- Core Type Transitions: **5**
- Optimal Task Distribution:
  - Small cores: `run_stage3` (3 cores), `run_stage4-7` (5-6 cores)
  - GPU: `run_stage1`, `run_stage2`

# Example Output for Android Platform

```bash
(base) rithik@Rithik-2 Z3-Allocator % python3 Z3-Allocator.py android_tree_cpu.csv android_tree_vk.csv
Enter the number of times to run the pipeline: 5

Analyzing benchmark data from:
CPU File: android_tree_cpu.csv
GPU File: android_tree_vk.csv

Pipeline Sequence:
run_stage1 -> run_stage2 -> run_stage3 -> run_stage4 -> run_stage5 -> run_stage6 -> run_stage7

Pipeline will be executed 5 times

Results for Device: 3A021JEHN02756

Core Configuration:
Small cores: [0, 1, 2, 3] (Available counts: [1, 2, 3, 4])
Medium cores: [4, 5] (Available counts: [1, 2])
Big cores: [6, 7] (Available counts: [1, 2])
Gpu cores: [8] (Available counts: [1])

Calculating optimal task allocation with CPU and GPU support...

Optimal Pipeline Allocation:
--------------------------------------------------------------------------------

Pipeline Instance 1:
----------------------------------------
run_stage1           -> medium [2 cores] (Start: 0.000000 ms, Exec: 1.473960 ms, End: 1.473960 ms)
run_stage2           -> big [2 cores] (Start: 1.473960 ms, Exec: 2.220110 ms, End: 3.694070 ms)
run_stage3           -> big [1 cores] (Start: 3.694070 ms, Exec: 0.331901 ms, End: 4.025971 ms)
run_stage4           -> gpu [1 cores] (Start: 4.025971 ms, Exec: 1.490740 ms, End: 5.516711 ms)
run_stage5           -> small [4 cores] (Start: 5.516711 ms, Exec: 0.845846 ms, End: 6.362557 ms)
run_stage6           -> small [4 cores] (Start: 6.362557 ms, Exec: 0.220950 ms, End: 6.583507 ms)
run_stage7           -> small [4 cores] (Start: 6.583507 ms, Exec: 0.503149 ms, End: 7.086656 ms)

Pipeline Instance 1 Total Time: 7.086656 ms
(Start: 0.000000 ms, End: 7.086656 ms)

Pipeline Instance 2:
----------------------------------------
run_stage1           -> medium [2 cores] (Start: 1.473960 ms, Exec: 1.473960 ms, End: 2.947920 ms)
run_stage2           -> big [2 cores] (Start: 3.694070 ms, Exec: 2.220110 ms, End: 5.914180 ms)
run_stage3           -> big [1 cores] (Start: 5.914180 ms, Exec: 0.331901 ms, End: 6.246081 ms)
run_stage4           -> gpu [1 cores] (Start: 6.246081 ms, Exec: 1.490740 ms, End: 7.736821 ms)
run_stage5           -> small [4 cores] (Start: 7.736821 ms, Exec: 0.845846 ms, End: 8.582667 ms)
run_stage6           -> small [4 cores] (Start: 8.582667 ms, Exec: 0.220950 ms, End: 8.803617 ms)
run_stage7           -> small [4 cores] (Start: 8.803617 ms, Exec: 0.503149 ms, End: 9.306766 ms)

Pipeline Instance 2 Total Time: 7.832806 ms
(Start: 1.473960 ms, End: 9.306766 ms)

Pipeline Instance 3:
----------------------------------------
run_stage1           -> medium [2 cores] (Start: 4.440220 ms, Exec: 1.473960 ms, End: 5.914180 ms)
run_stage2           -> big [2 cores] (Start: 5.914180 ms, Exec: 2.220110 ms, End: 8.134290 ms)
run_stage3           -> big [1 cores] (Start: 8.134290 ms, Exec: 0.331901 ms, End: 8.466191 ms)
run_stage4           -> gpu [1 cores] (Start: 8.466191 ms, Exec: 1.490740 ms, End: 9.956931 ms)
run_stage5           -> small [4 cores] (Start: 9.956931 ms, Exec: 0.845846 ms, End: 10.802777 ms)
run_stage6           -> small [4 cores] (Start: 10.802777 ms, Exec: 0.220950 ms, End: 11.023727 ms)
run_stage7           -> small [4 cores] (Start: 11.023727 ms, Exec: 0.503149 ms, End: 11.526876 ms)

Pipeline Instance 3 Total Time: 7.086656 ms
(Start: 4.440220 ms, End: 11.526876 ms)

Pipeline Instance 4:
----------------------------------------
run_stage1           -> medium [2 cores] (Start: 6.660330 ms, Exec: 1.473960 ms, End: 8.134290 ms)
run_stage2           -> big [2 cores] (Start: 8.134290 ms, Exec: 2.220110 ms, End: 10.354400 ms)
run_stage3           -> big [1 cores] (Start: 11.083770 ms, Exec: 0.331901 ms, End: 11.415671 ms)
run_stage4           -> gpu [1 cores] (Start: 11.415671 ms, Exec: 1.490740 ms, End: 12.906411 ms)
run_stage5           -> small [4 cores] (Start: 13.551305 ms, Exec: 0.845846 ms, End: 14.397151 ms)
run_stage6           -> small [4 cores] (Start: 14.739848 ms, Exec: 0.220950 ms, End: 14.960798 ms)
run_stage7           -> small [4 cores] (Start: 14.960798 ms, Exec: 0.503149 ms, End: 15.463947 ms)

Pipeline Instance 4 Total Time: 8.803617 ms
(Start: 6.660330 ms, End: 15.463947 ms)

Pipeline Instance 5:
----------------------------------------
run_stage1           -> medium [2 cores] (Start: 8.880440 ms, Exec: 1.473960 ms, End: 10.354400 ms)
run_stage2           -> big [2 cores] (Start: 10.354400 ms, Exec: 2.220110 ms, End: 12.574510 ms)
run_stage3           -> big [1 cores] (Start: 12.574510 ms, Exec: 0.331901 ms, End: 12.906411 ms)
run_stage4           -> gpu [1 cores] (Start: 12.906411 ms, Exec: 1.490740 ms, End: 14.397151 ms)
run_stage5           -> small [4 cores] (Start: 14.397151 ms, Exec: 0.845846 ms, End: 15.242997 ms)
run_stage6           -> small [4 cores] (Start: 15.242997 ms, Exec: 0.220950 ms, End: 15.463947 ms)
run_stage7           -> small [4 cores] (Start: 15.463947 ms, Exec: 0.503149 ms, End: 15.967096 ms)

Pipeline Instance 5 Total Time: 7.086656 ms
(Start: 8.880440 ms, End: 15.967096 ms)

Core Type Transitions:
Pipeline 1: medium -> big at run_stage2
Pipeline 1: big -> gpu at run_stage4
Pipeline 1: gpu -> small at run_stage5
Pipeline 2: medium -> big at run_stage2
Pipeline 2: big -> gpu at run_stage4
Pipeline 2: gpu -> small at run_stage5
Pipeline 3: medium -> big at run_stage2
Pipeline 3: big -> gpu at run_stage4
Pipeline 3: gpu -> small at run_stage5
Pipeline 4: medium -> big at run_stage2
Pipeline 4: big -> gpu at run_stage4
Pipeline 4: gpu -> small at run_stage5
Pipeline 5: medium -> big at run_stage2
Pipeline 5: big -> gpu at run_stage4
Pipeline 5: gpu -> small at run_stage5

Total Core Type Transitions: 15
Total Pipeline Time: 15.967096 ms

Task Distribution by Core Type:

Pipeline Instance 1:
small cores: run_stage5 (4 cores), run_stage6 (4 cores), run_stage7 (4 cores)
medium cores: run_stage1 (2 cores)
big cores: run_stage2 (2 cores), run_stage3 (1 cores)
gpu cores: run_stage4 (1 cores)

Pipeline Instance 2:
small cores: run_stage5 (4 cores), run_stage6 (4 cores), run_stage7 (4 cores)
medium cores: run_stage1 (2 cores)
big cores: run_stage2 (2 cores), run_stage3 (1 cores)
gpu cores: run_stage4 (1 cores)

Pipeline Instance 3:
small cores: run_stage5 (4 cores), run_stage6 (4 cores), run_stage7 (4 cores)
medium cores: run_stage1 (2 cores)
big cores: run_stage2 (2 cores), run_stage3 (1 cores)
gpu cores: run_stage4 (1 cores)

Pipeline Instance 4:
small cores: run_stage5 (4 cores), run_stage6 (4 cores), run_stage7 (4 cores)
medium cores: run_stage1 (2 cores)
big cores: run_stage2 (2 cores), run_stage3 (1 cores)
gpu cores: run_stage4 (1 cores)

Pipeline Instance 5:
small cores: run_stage5 (4 cores), run_stage6 (4 cores), run_stage7 (4 cores)
medium cores: run_stage1 (2 cores)
big cores: run_stage2 (2 cores), run_stage3 (1 cores)
gpu cores: run_stage4 (1 cores)

================================================================================
```
