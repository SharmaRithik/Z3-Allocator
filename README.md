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
