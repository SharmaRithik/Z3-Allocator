# Z3-Allocator

## Task Allocation Results for Device Performance Benchmarking
## Parsed Data

The data has been successfully parsed into a structured format. Below, we present task allocation and execution time results for two example devices.

---

## Device: `3A021JEHN02756`

### Core Configurations Available
- **Big**: [1, 2]
- **Medium**: [1, 2]
- **Small**: [1, 2, 3, 4]

### Execution Times per Task and Core Configuration
| Config Index | Core Config | BuildOctree | BuildRadixTree | EdgeCount | EdgeOffset | MortonCode | RadixSort | RemoveDuplicates | Total Time  |
|--------------|-------------|-------------|----------------|-----------|------------|------------|-----------|------------------|-------------|
| Config 1     | Big [1]     | Big [1]     | Big [1]        | Big [1]   | Big [1]    | Big [1]    | Big [1]   | Big [1]          | 45.711093   |
| Config 2     | Big [2]     | Big [2]     | Big [2]        | Big [2]   | Big [2]    | Big [2]    | Big [2]   | Big [2]          | 18.733713   |
| Config 3     | Medium [1]  | Medium [1]  | Medium [1]     | Medium [1]| Medium [1] | Medium [1] | Medium [1]| Medium [1]       | 49.921399   |
| Config 4     | Medium [2]  | Medium [2]  | Medium [2]     | Medium [2]| Medium [2] | Medium [2] | Medium [2]| Medium [2]       | 16.888826   |
| Config 5     | Small [1]   | Small [1]   | Small [1]      | Small [1] | Small [1]  | Small [1]  | Small [1] | Small [1]        | 168.968541  |
| Config 6     | Small [2]   | Small [2]   | Small [2]      | Small [2] | Small [2]  | Small [2]  | Small [2] | Small [2]        | 88.750160   |
| Config 7     | Small [3]   | Small [3]   | Small [3]      | Small [3] | Small [3]  | Small [3]  | Small [3] | Small [3]        | 44.154171   |
| Config 8     | Small [4]   | Small [4]   | Small [4]      | Small [4] | Small [4]  | Small [4]  | Small [4] | Small [4]        | 36.166219   |
| **Config Best** | Best    | Big [2]     | Big [2]        | Medium [2]| Medium [2] | Medium [2] | Medium [2]| Big [2]          | **15.306021**|

### Optimal Task Allocation
| Task             | Assigned Core |
|------------------|---------------|
| BuildOctree      | Big [2]       |
| BuildRadixTree   | Medium [2]    |
| EdgeCount        | Small [4]     |
| EdgeOffset       | Medium [2]    |
| MortonCode       | Big [2]       |
| RadixSort        | Small [4]     |
| RemoveDuplicates | Small [3]     |

#### Execution Times per Core Type
- **Big**: 6.833990 ms
- **Medium**: 6.310174 ms
- **Small**: 6.198121 ms

- **Total Execution Time**: 6.833990 ms  
- **Speedup vs Config Best**: 2.24x (+124.0%)

---

## Device: `RFCT80DAADN`

### Core Configurations Available
- **Big**: [1]
- **Medium**: [1, 2, 3]
- **Small**: [1, 2, 3, 4]

### Execution Times per Task and Core Configuration
| Config Index | Core Config | BuildOctree | BuildRadixTree | EdgeCount | EdgeOffset | MortonCode | RadixSort | RemoveDuplicates | Total Time  |
|--------------|-------------|-------------|----------------|-----------|------------|------------|-----------|------------------|-------------|
| Config 1     | Big [1]     | Big [1]     | Big [1]        | Big [1]   | Big [1]    | Big [1]    | Big [1]   | Big [1]          | 50.236551   |
| Config 2     | Medium [1]  | Medium [1]  | Medium [1]     | Medium [1]| Medium [1] | Medium [1] | Medium [1]| Medium [1]       | 112.992094  |
| Config 3     | Medium [2]  | Medium [2]  | Medium [2]     | Medium [2]| Medium [2] | Medium [2] | Medium [2]| Medium [2]       | 40.148512   |
| Config 4     | Medium [3]  | Medium [3]  | Medium [3]     | Medium [3]| Medium [3] | Medium [3] | Medium [3]| Medium [3]       | 23.362199   |
| Config 5     | Small [1]   | Small [1]   | Small [1]      | Small [1] | Small [1]  | Small [1]  | Small [1] | Small [1]        | 212.388800  |
| Config 6     | Small [2]   | Small [2]   | Small [2]      | Small [2] | Small [2]  | Small [2]  | Small [2] | Small [2]        | 110.592787  |
| Config 7     | Small [3]   | Small [3]   | Small [3]      | Small [3] | Small [3]  | Small [3]  | Small [3] | Small [3]        | 60.475010   |
| Config 8     | Small [4]   | Small [4]   | Small [4]      | Small [4] | Small [4]  | Small [4]  | Small [4] | Small [4]        | 45.922029   |
| **Config Best** | Best    | Medium [3]  | Medium [3]     | Small [4] | Medium [3] | Medium [3] | Medium [3]| Big [1]          | **23.089679**|

### Optimal Task Allocation
| Task             | Assigned Core |
|------------------|---------------|
| BuildOctree      | Medium [3]    |
| BuildRadixTree   | Small [4]     |
| EdgeCount        | Medium [3]    |
| EdgeOffset       | Medium [1]    |
| MortonCode       | Big [1]       |
| RadixSort        | Big [1]       |
| RemoveDuplicates | Medium [1]    |

#### Execution Times per Core Type
- **Big**: 11.501730 ms
- **Medium**: 11.016574 ms
- **Small**: 11.671800 ms

- **Total Execution Time**: 11.671800 ms  
- **Speedup vs Config Best**: 1.98x (+97.8%)

---

## Detailed Benchmark Data

| Device_ID       | Category    | Task               | Core_Type | Core_Count | Iterations | Real_Time | CPU_Time | Time_Unit |
|-----------------|-------------|--------------------|-----------|------------|------------|-----------|----------|-----------|
| 3A021JEHN02756  | CPU_Pinned  | MortonCode         | Small     | 1          | 40         | 31.775300 | 0.503699 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | MortonCode         | Small     | 2          | 40         | 11.270300 | 0.361754 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | MortonCode         | Small     | 3          | 40         | 6.987620  | 0.576181 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | MortonCode         | Small     | 4          | 40         | 5.737550  | 0.800753 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | MortonCode         | Medium    | 1          | 40         | 4.796840  | 0.060218 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | MortonCode         | Medium    | 2          | 40         | 1.747090  | 0.073059 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | MortonCode         | Big       | 1          | 40         | 3.994530  | 0.025571 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | MortonCode         | Big       | 2          | 40         | 2.054290  | 0.016575 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RadixSort          | Small     | 1          | 40         | 38.451500 | 0.684748 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RadixSort          | Small     | 2          | 40         | 25.550700 | 0.700369 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RadixSort          | Small     | 3          | 40         | 6.180270  | 0.547096 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RadixSort          | Small     | 4          | 40         | 4.717140  | 0.408426 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RadixSort          | Medium    | 1          | 40         | 4.916910  | 0.155160 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RadixSort          | Medium    | 2          | 40         | 1.852280  | 0.156607 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RadixSort          | Big       | 1          | 40         | 4.435740  | 0.202076 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RadixSort          | Big       | 2          | 40         | 3.834350  | 0.225744 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RemoveDuplicates   | Small     | 1          | 40         | 0.758745  | 0.745595 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RemoveDuplicates   | Small     | 2          | 40         | 0.629823  | 0.621448 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RemoveDuplicates   | Small     | 3          | 40         | 0.519363  | 0.511257 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RemoveDuplicates   | Small     | 4          | 40         | 0.514521  | 0.507744 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RemoveDuplicates   | Medium    | 1          | 40         | 0.461329  | 0.455081 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RemoveDuplicates   | Medium    | 2          | 40         | 0.432208  | 0.426254 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RemoveDuplicates   | Big       | 1          | 40         | 0.338799  | 0.335183 | ms        |
| 3A021JEHN02756  | CPU_Pinned  | RemoveDuplicates   | Big       | 2          | 40         | 0.330083  | 0.328446 | ms        |

Each row represents a detailed breakdown of task execution times and CPU usage across different configurations.

