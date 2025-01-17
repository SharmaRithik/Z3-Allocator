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
python3 Alpha-Z3-Allocator.py <cpu_benchmark_file> <gpu_benchmark_file>
python3 Beta-Z3-Allocator.py <cpu_benchmark_file> <gpu_benchmark_file>
```

### For Android:

```bash
python3 Z3-Allocator.py android_tree_cpu.csv android_tree_vk.csv
python3 Alpha-Z3-Allocator.py android_cifar_dense_cpu.csv android_cifar_dense_vk.csv
python3 Beta-Z3-Allocator.py android_cifar_sparse_cpu.csv android_cifar_sparse_vk.csv
```

### For Jetson:

```bash
python3 Z3-Allocator.py jetson_tree_cpu.csv jetson_tree_cuda.csv
jetson_cifar_dense_cpu.csv coming soon
jetson_cifar_sparse_cpu.csv coming soon
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
(base) LLVM19@Rithik Z3-Allocator % python3 Z3-Allocator.py android_tree_cpu.csv android_tree_vk.csv
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
run_stage3           -> big [2 cores] (Start: 3.694070 ms, Exec: 0.335994 ms, End: 4.030064 ms)
run_stage4           -> gpu [1 cores] (Start: 4.030064 ms, Exec: 1.490740 ms, End: 5.520804 ms)
run_stage5           -> small [4 cores] (Start: 5.520804 ms, Exec: 0.845846 ms, End: 6.366650 ms)
run_stage6           -> small [4 cores] (Start: 6.366650 ms, Exec: 0.220950 ms, End: 6.587600 ms)
run_stage7           -> small [4 cores] (Start: 6.587600 ms, Exec: 0.503149 ms, End: 7.090749 ms)

Pipeline Instance 1 Total Time: 7.090749 ms
(Start: 0.000000 ms, End: 7.090749 ms)

Pipeline Instance 2:
----------------------------------------
run_stage1           -> medium [2 cores] (Start: 1.473960 ms, Exec: 1.473960 ms, End: 2.947920 ms)
run_stage2           -> big [2 cores] (Start: 3.694070 ms, Exec: 2.220110 ms, End: 5.914180 ms)
run_stage3           -> big [2 cores] (Start: 5.914180 ms, Exec: 0.335994 ms, End: 6.250174 ms)
run_stage4           -> gpu [1 cores] (Start: 6.250174 ms, Exec: 1.490740 ms, End: 7.740914 ms)
run_stage5           -> small [4 cores] (Start: 7.740914 ms, Exec: 0.845846 ms, End: 8.586760 ms)
run_stage6           -> small [4 cores] (Start: 8.586760 ms, Exec: 0.220950 ms, End: 8.807710 ms)
run_stage7           -> small [4 cores] (Start: 8.807710 ms, Exec: 0.503149 ms, End: 9.310859 ms)

Pipeline Instance 2 Total Time: 7.836899 ms
(Start: 1.473960 ms, End: 9.310859 ms)

Pipeline Instance 3:
----------------------------------------
run_stage1           -> medium [2 cores] (Start: 2.947920 ms, Exec: 1.473960 ms, End: 4.421880 ms)
run_stage2           -> big [2 cores] (Start: 5.914180 ms, Exec: 2.220110 ms, End: 8.134290 ms)
run_stage3           -> big [2 cores] (Start: 8.134290 ms, Exec: 0.335994 ms, End: 8.470284 ms)
run_stage4           -> gpu [1 cores] (Start: 8.470284 ms, Exec: 1.490740 ms, End: 9.961024 ms)
run_stage5           -> small [4 cores] (Start: 9.961024 ms, Exec: 0.845846 ms, End: 10.806870 ms)
run_stage6           -> small [4 cores] (Start: 10.806870 ms, Exec: 0.220950 ms, End: 11.027820 ms)
run_stage7           -> small [4 cores] (Start: 11.027820 ms, Exec: 0.503149 ms, End: 11.530969 ms)

Pipeline Instance 3 Total Time: 8.583049 ms
(Start: 2.947920 ms, End: 11.530969 ms)

Pipeline Instance 4:
----------------------------------------
run_stage1           -> medium [2 cores] (Start: 4.421880 ms, Exec: 1.473960 ms, End: 5.895840 ms)
run_stage2           -> big [2 cores] (Start: 8.134290 ms, Exec: 2.220110 ms, End: 10.354400 ms)
run_stage3           -> big [2 cores] (Start: 10.354400 ms, Exec: 0.335994 ms, End: 10.690394 ms)
run_stage4           -> gpu [1 cores] (Start: 10.690394 ms, Exec: 1.490740 ms, End: 12.181134 ms)
run_stage5           -> small [4 cores] (Start: 12.181134 ms, Exec: 0.845846 ms, End: 13.026980 ms)
run_stage6           -> small [4 cores] (Start: 13.026980 ms, Exec: 0.220950 ms, End: 13.247930 ms)
run_stage7           -> small [4 cores] (Start: 13.247930 ms, Exec: 0.503149 ms, End: 13.751079 ms)

Pipeline Instance 4 Total Time: 9.329199 ms
(Start: 4.421880 ms, End: 13.751079 ms)

Pipeline Instance 5:
----------------------------------------
run_stage1           -> medium [2 cores] (Start: 5.895840 ms, Exec: 1.473960 ms, End: 7.369800 ms)
run_stage2           -> big [2 cores] (Start: 10.354400 ms, Exec: 2.220110 ms, End: 12.574510 ms)
run_stage3           -> big [2 cores] (Start: 12.574510 ms, Exec: 0.335994 ms, End: 12.910504 ms)
run_stage4           -> gpu [1 cores] (Start: 12.910504 ms, Exec: 1.490740 ms, End: 14.401244 ms)
run_stage5           -> small [4 cores] (Start: 14.401244 ms, Exec: 0.845846 ms, End: 15.247090 ms)
run_stage6           -> small [4 cores] (Start: 15.247090 ms, Exec: 0.220950 ms, End: 15.468040 ms)
run_stage7           -> small [4 cores] (Start: 15.468040 ms, Exec: 0.503149 ms, End: 15.971189 ms)

Pipeline Instance 5 Total Time: 10.075349 ms
(Start: 5.895840 ms, End: 15.971189 ms)

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
Total Pipeline Time: 15.971189 ms

Task Distribution by Core Type:

Pipeline Instance 1:
small cores: run_stage5 (4 cores), run_stage6 (4 cores), run_stage7 (4 cores)
medium cores: run_stage1 (2 cores)
big cores: run_stage2 (2 cores), run_stage3 (2 cores)
gpu cores: run_stage4 (1 cores)

Pipeline Instance 2:
small cores: run_stage5 (4 cores), run_stage6 (4 cores), run_stage7 (4 cores)
medium cores: run_stage1 (2 cores)
big cores: run_stage2 (2 cores), run_stage3 (2 cores)
gpu cores: run_stage4 (1 cores)

Pipeline Instance 3:
small cores: run_stage5 (4 cores), run_stage6 (4 cores), run_stage7 (4 cores)
medium cores: run_stage1 (2 cores)
big cores: run_stage2 (2 cores), run_stage3 (2 cores)
gpu cores: run_stage4 (1 cores)

Pipeline Instance 4:
small cores: run_stage5 (4 cores), run_stage6 (4 cores), run_stage7 (4 cores)
medium cores: run_stage1 (2 cores)
big cores: run_stage2 (2 cores), run_stage3 (2 cores)
gpu cores: run_stage4 (1 cores)

Pipeline Instance 5:
small cores: run_stage5 (4 cores), run_stage6 (4 cores), run_stage7 (4 cores)
medium cores: run_stage1 (2 cores)
big cores: run_stage2 (2 cores), run_stage3 (2 cores)
gpu cores: run_stage4 (1 cores)

================================================================================
```

# Example Output for Jetson Platform

```bash
(base) LLVM19@Rithik Z3-Allocator % python3 Z3-Allocator.py jetson_tree_cpu.csv jetson_tree_cuda.csv
Enter the number of times to run the pipeline: 5

Analyzing benchmark data from:
CPU File: jetson_tree_cpu.csv
GPU File: jetson_tree_cuda.csv

Pipeline Sequence:
run_stage1 -> run_stage2 -> run_stage3 -> run_stage4 -> run_stage5 -> run_stage6 -> run_stage7

Pipeline will be executed 5 times

Results for Device: jetson

Core Configuration:
Small cores: [1, 2, 3, 4, 5, 6] (Available counts: [1, 2, 3, 4, 5, 6])
Gpu cores: [1] (Available counts: [1])

Calculating optimal task allocation with CPU and GPU support...

Optimal Pipeline Allocation:
--------------------------------------------------------------------------------

Pipeline Instance 1:
----------------------------------------
run_stage1           -> gpu [1 cores] (Start: 0.000000 ms, Exec: 1.644090 ms, End: 1.644090 ms)
run_stage2           -> gpu [1 cores] (Start: 1.644090 ms, Exec: 3.466720 ms, End: 5.110810 ms)
run_stage3           -> small [6 cores] (Start: 5.110810 ms, Exec: 0.313267 ms, End: 5.424077 ms)
run_stage4           -> small [6 cores] (Start: 5.424077 ms, Exec: 3.078340 ms, End: 8.502417 ms)
run_stage5           -> small [6 cores] (Start: 8.502417 ms, Exec: 0.286578 ms, End: 8.788995 ms)
run_stage6           -> small [6 cores] (Start: 21.867083 ms, Exec: 0.191093 ms, End: 22.058176 ms)
run_stage7           -> small [6 cores] (Start: 22.058176 ms, Exec: 0.197198 ms, End: 22.255374 ms)

Pipeline Instance 1 Total Time: 22.255374 ms
(Start: 0.000000 ms, End: 22.255374 ms)

Pipeline Instance 2:
----------------------------------------
run_stage1           -> gpu [1 cores] (Start: 3.466720 ms, Exec: 1.644090 ms, End: 5.110810 ms)
run_stage2           -> gpu [1 cores] (Start: 5.110810 ms, Exec: 3.466720 ms, End: 8.577530 ms)
run_stage3           -> small [6 cores] (Start: 8.577530 ms, Exec: 0.313267 ms, End: 8.890797 ms)
run_stage4           -> small [6 cores] (Start: 8.890797 ms, Exec: 3.078340 ms, End: 11.969137 ms)
run_stage5           -> small [6 cores] (Start: 21.509563 ms, Exec: 0.286578 ms, End: 21.796141 ms)
run_stage6           -> small [6 cores] (Start: 22.064281 ms, Exec: 0.191093 ms, End: 22.255374 ms)
run_stage7           -> small [6 cores] (Start: 22.255374 ms, Exec: 0.197198 ms, End: 22.452572 ms)

Pipeline Instance 2 Total Time: 18.985852 ms
(Start: 3.466720 ms, End: 22.452572 ms)

Pipeline Instance 3:
----------------------------------------
run_stage1           -> gpu [1 cores] (Start: 6.933440 ms, Exec: 1.644090 ms, End: 8.577530 ms)
run_stage2           -> gpu [1 cores] (Start: 8.577530 ms, Exec: 3.466720 ms, End: 12.044250 ms)
run_stage3           -> small [6 cores] (Start: 12.044250 ms, Exec: 0.313267 ms, End: 12.357517 ms)
run_stage4           -> small [6 cores] (Start: 12.357517 ms, Exec: 3.078340 ms, End: 15.435857 ms)
run_stage5           -> small [6 cores] (Start: 21.796141 ms, Exec: 0.286578 ms, End: 22.082719 ms)
run_stage6           -> small [6 cores] (Start: 22.261479 ms, Exec: 0.191093 ms, End: 22.452572 ms)
run_stage7           -> small [6 cores] (Start: 22.452572 ms, Exec: 0.197198 ms, End: 22.649770 ms)

Pipeline Instance 3 Total Time: 15.716330 ms
(Start: 6.933440 ms, End: 22.649770 ms)

Pipeline Instance 4:
----------------------------------------
run_stage1           -> gpu [1 cores] (Start: 8.577530 ms, Exec: 1.644090 ms, End: 10.221620 ms)
run_stage2           -> gpu [1 cores] (Start: 12.044250 ms, Exec: 3.466720 ms, End: 15.510970 ms)
run_stage3           -> small [6 cores] (Start: 15.510970 ms, Exec: 0.313267 ms, End: 15.824237 ms)
run_stage4           -> small [6 cores] (Start: 15.824237 ms, Exec: 3.078340 ms, End: 18.902577 ms)
run_stage5           -> small [6 cores] (Start: 22.082719 ms, Exec: 0.286578 ms, End: 22.369297 ms)
run_stage6           -> small [6 cores] (Start: 22.458677 ms, Exec: 0.191093 ms, End: 22.649770 ms)
run_stage7           -> small [6 cores] (Start: 22.649770 ms, Exec: 0.197198 ms, End: 22.846968 ms)

Pipeline Instance 4 Total Time: 14.269438 ms
(Start: 8.577530 ms, End: 22.846968 ms)

Pipeline Instance 5:
----------------------------------------
run_stage1           -> gpu [1 cores] (Start: 10.221620 ms, Exec: 1.644090 ms, End: 11.865710 ms)
run_stage2           -> gpu [1 cores] (Start: 15.510970 ms, Exec: 3.466720 ms, End: 18.977690 ms)
run_stage3           -> small [6 cores] (Start: 18.977690 ms, Exec: 0.313267 ms, End: 19.290957 ms)
run_stage4           -> small [6 cores] (Start: 19.290957 ms, Exec: 3.078340 ms, End: 22.369297 ms)
run_stage5           -> small [6 cores] (Start: 22.369297 ms, Exec: 0.286578 ms, End: 22.655875 ms)
run_stage6           -> small [6 cores] (Start: 22.655875 ms, Exec: 0.191093 ms, End: 22.846968 ms)
run_stage7           -> small [6 cores] (Start: 22.846968 ms, Exec: 0.197198 ms, End: 23.044166 ms)

Pipeline Instance 5 Total Time: 12.822546 ms
(Start: 10.221620 ms, End: 23.044166 ms)

Core Type Transitions:
Pipeline 1: gpu -> small at run_stage3
Pipeline 2: gpu -> small at run_stage3
Pipeline 3: gpu -> small at run_stage3
Pipeline 4: gpu -> small at run_stage3
Pipeline 5: gpu -> small at run_stage3

Total Core Type Transitions: 5
Total Pipeline Time: 23.044166 ms

Task Distribution by Core Type:

Pipeline Instance 1:
small cores: run_stage3 (6 cores), run_stage4 (6 cores), run_stage5 (6 cores), run_stage6 (6 cores), run_stage7 (6 cores)
gpu cores: run_stage1 (1 cores), run_stage2 (1 cores)

Pipeline Instance 2:
small cores: run_stage3 (6 cores), run_stage4 (6 cores), run_stage5 (6 cores), run_stage6 (6 cores), run_stage7 (6 cores)
gpu cores: run_stage1 (1 cores), run_stage2 (1 cores)

Pipeline Instance 3:
small cores: run_stage3 (6 cores), run_stage4 (6 cores), run_stage5 (6 cores), run_stage6 (6 cores), run_stage7 (6 cores)
gpu cores: run_stage1 (1 cores), run_stage2 (1 cores)

Pipeline Instance 4:
small cores: run_stage3 (6 cores), run_stage4 (6 cores), run_stage5 (6 cores), run_stage6 (6 cores), run_stage7 (6 cores)
gpu cores: run_stage1 (1 cores), run_stage2 (1 cores)

Pipeline Instance 5:
small cores: run_stage3 (6 cores), run_stage4 (6 cores), run_stage5 (6 cores), run_stage6 (6 cores), run_stage7 (6 cores)
gpu cores: run_stage1 (1 cores), run_stage2 (1 cores)

================================================================================
```
