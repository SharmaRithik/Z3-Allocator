# Z3-Allocator

## Task Allocation Results for Device Performance Benchmarking using the independent approach.
## Parsed Data

The data has been successfully parsed into a structured format. Below, we present task allocation and execution time results for two example devices.

---

## Device: `3A021JEHN02756`

### Core Configurations Available
- **Big**: [1, 2]
- **Medium**: [1, 2]
- **Small**: [1, 2, 3, 4]

```plaintext
Execution Times per Task and Core Configuration
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
| Config Best  | Best        | Big [2]     | Big [2]        | Medium [2]| Medium [2] | Medium [2] | Medium [2]| Big [2]          | 15.306021   |

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

```
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

```plaintext
Execution Times per Task and Core Configuration
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
| Config Best  | Best        | Medium [3]  | Medium [3]     | Small [4] | Medium [3] | Medium [3] | Medium [3]| Big [1]          | 23.089679   |

Optimal Task Allocation
| Task             | Assigned Core |
|------------------|---------------|
| BuildOctree      | Medium [3]    |
| BuildRadixTree   | Small [4]     |
| EdgeCount        | Medium [3]    |
| EdgeOffset       | Medium [1]    |
| MortonCode       | Big [1]       |
| RadixSort        | Big [1]       |
| RemoveDuplicates | Medium [1]    |
```

#### Execution Times per Core Type
- **Big**: 11.501730 ms
- **Medium**: 11.016574 ms
- **Small**: 11.671800 ms

- **Total Execution Time**: 11.671800 ms  
- **Speedup vs Config Best**: 1.98x (+97.8%)

```plaintext
Detailed Benchmark Data

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
```

## Task Allocation Results for Device Performance Benchmarking using the dependent sequence iterative approach.

```plaintext
(base) rithik@Rithik-2 Z3-Allocator % python3 test.py
Enter the number of times to run the pipeline: 5
Data successfully parsed into DataFrame.

Available tasks in benchmark data:
['BuildOctree', 'BuildRadixTree', 'EdgeCount', 'EdgeOffset', 'MortonCode', 'RadixSort', 'RemoveDuplicates']

Pipeline will be executed 5 times
Pipeline Sequence:
MortonCode -> RadixSort -> RemoveDuplicates -> BuildRadixTree -> EdgeCount -> EdgeOffset -> BuildOctree

Results for Device: 3A021JEHN02756
Big: [1, 2]
Medium: [1, 2]
Small: [1, 2, 3, 4]

Tasks to be allocated: ['BuildOctree', 'BuildRadixTree', 'EdgeCount', 'EdgeOffset', 'MortonCode', 'RadixSort', 'RemoveDuplicates']

Calculating optimal task allocation with dependencies...

Optimal Pipeline Allocation:
--------------------------------------------------------------------------------

Pipeline Instance 1:
----------------------------------------
MortonCode           -> Medium [2] (Start: 0.000000 ms, Exec: 1.747090 ms, End: 1.747090 ms)
RadixSort            -> Medium [2] (Start: 1.747090 ms, Exec: 1.852280 ms, End: 3.599370 ms)
RemoveDuplicates     -> Big [2] (Start: 3.599370 ms, Exec: 0.330083 ms, End: 3.929453 ms)
BuildRadixTree       -> Big [2] (Start: 3.929453 ms, Exec: 5.341300 ms, End: 9.270753 ms)
EdgeCount            -> Small [4] (Start: 9.270753 ms, Exec: 0.961618 ms, End: 10.232371 ms)
EdgeOffset           -> Big [1] (Start: 10.232371 ms, Exec: 0.393834 ms, End: 10.626205 ms)
BuildOctree          -> Big [2] (Start: 10.626205 ms, Exec: 4.779700 ms, End: 15.405905 ms)

Pipeline Instance 1 Total Time: 15.405905 ms
(Start: 0.000000 ms, End: 15.405905 ms)

Pipeline Instance 2:
----------------------------------------
MortonCode           -> Medium [2] (Start: 2.096507 ms, Exec: 1.747090 ms, End: 3.843597 ms)
RadixSort            -> Medium [2] (Start: 5.801371 ms, Exec: 1.852280 ms, End: 7.653651 ms)
RemoveDuplicates     -> Medium [1] (Start: 8.809424 ms, Exec: 0.461329 ms, End: 9.270753 ms)
BuildRadixTree       -> Big [2] (Start: 9.270753 ms, Exec: 5.341300 ms, End: 14.612053 ms)
EdgeCount            -> Big [2] (Start: 14.612053 ms, Exec: 1.244050 ms, End: 15.856103 ms)
EdgeOffset           -> Medium [2] (Start: 15.856103 ms, Exec: 0.321214 ms, End: 16.177317 ms)
BuildOctree          -> Big [2] (Start: 16.361844 ms, Exec: 4.779700 ms, End: 21.141544 ms)

Pipeline Instance 2 Total Time: 19.045037 ms
(Start: 2.096507 ms, End: 21.141544 ms)

Pipeline Instance 3:
----------------------------------------
MortonCode           -> Big [1] (Start: 4.642503 ms, Exec: 3.994530 ms, End: 8.637033 ms)
RadixSort            -> Medium [1] (Start: 8.637033 ms, Exec: 4.916910 ms, End: 13.553943 ms)
RemoveDuplicates     -> Small [4] (Start: 14.097532 ms, Exec: 0.514521 ms, End: 14.612053 ms)
BuildRadixTree       -> Big [2] (Start: 14.612053 ms, Exec: 5.341300 ms, End: 19.953353 ms)
EdgeCount            -> Small [4] (Start: 19.953353 ms, Exec: 0.961618 ms, End: 20.914971 ms)
EdgeOffset           -> Medium [2] (Start: 20.914971 ms, Exec: 0.321214 ms, End: 21.236185 ms)
BuildOctree          -> Big [2] (Start: 21.376181 ms, Exec: 4.779700 ms, End: 26.155881 ms)

Pipeline Instance 3 Total Time: 21.513378 ms
(Start: 4.642503 ms, End: 26.155881 ms)

Pipeline Instance 4:
----------------------------------------
MortonCode           -> Medium [2] (Start: 8.986451 ms, Exec: 1.747090 ms, End: 10.733541 ms)
RadixSort            -> Medium [2] (Start: 13.553943 ms, Exec: 1.852280 ms, End: 15.406223 ms)
RemoveDuplicates     -> Medium [2] (Start: 19.521145 ms, Exec: 0.432208 ms, End: 19.953353 ms)
BuildRadixTree       -> Big [2] (Start: 19.953353 ms, Exec: 5.341300 ms, End: 25.294653 ms)
EdgeCount            -> Medium [2] (Start: 25.294653 ms, Exec: 0.934354 ms, End: 26.229007 ms)
EdgeOffset           -> Medium [2] (Start: 26.229007 ms, Exec: 0.321214 ms, End: 26.550221 ms)
BuildOctree          -> Big [2] (Start: 27.111821 ms, Exec: 4.779700 ms, End: 31.891521 ms)

Pipeline Instance 4 Total Time: 22.905070 ms
(Start: 8.986451 ms, End: 31.891521 ms)

Pipeline Instance 5:
----------------------------------------
MortonCode           -> Medium [1] (Start: 10.733541 ms, Exec: 4.796840 ms, End: 15.530381 ms)
RadixSort            -> Medium [1] (Start: 15.530381 ms, Exec: 4.916910 ms, End: 20.447291 ms)
RemoveDuplicates     -> Medium [1] (Start: 20.447291 ms, Exec: 0.461329 ms, End: 20.908620 ms)
BuildRadixTree       -> Big [2] (Start: 25.294653 ms, Exec: 5.341300 ms, End: 30.635953 ms)
EdgeCount            -> Medium [2] (Start: 30.635953 ms, Exec: 0.934354 ms, End: 31.570307 ms)
EdgeOffset           -> Medium [2] (Start: 31.570307 ms, Exec: 0.321214 ms, End: 31.891521 ms)
BuildOctree          -> Big [2] (Start: 31.891521 ms, Exec: 4.779700 ms, End: 36.671221 ms)

Pipeline Instance 5 Total Time: 25.937680 ms
(Start: 10.733541 ms, End: 36.671221 ms)

Core Type Transitions:
Pipeline 1: Medium -> Big at RemoveDuplicates
Pipeline 1: Big -> Small at EdgeCount
Pipeline 1: Small -> Big at EdgeOffset
Pipeline 2: Medium -> Big at BuildRadixTree
Pipeline 2: Big -> Medium at EdgeOffset
Pipeline 2: Medium -> Big at BuildOctree
Pipeline 3: Big -> Medium at RadixSort
Pipeline 3: Medium -> Small at RemoveDuplicates
Pipeline 3: Small -> Big at BuildRadixTree
Pipeline 3: Big -> Small at EdgeCount
Pipeline 3: Small -> Medium at EdgeOffset
Pipeline 3: Medium -> Big at BuildOctree
Pipeline 4: Medium -> Big at BuildRadixTree
Pipeline 4: Big -> Medium at EdgeCount
Pipeline 4: Medium -> Big at BuildOctree
Pipeline 5: Medium -> Big at BuildRadixTree
Pipeline 5: Big -> Medium at EdgeCount
Pipeline 5: Medium -> Big at BuildOctree

Total Core Type Transitions: 18
Total Pipeline Time: 36.671221 ms

================================================================================

Results for Device: RFCT80DAADN
Big: [1]
Medium: [1, 2, 3]
Small: [1, 2, 3, 4]

Tasks to be allocated: ['BuildOctree', 'BuildRadixTree', 'EdgeCount', 'EdgeOffset', 'MortonCode', 'RadixSort', 'RemoveDuplicates']

Calculating optimal task allocation with dependencies...

Optimal Pipeline Allocation:
--------------------------------------------------------------------------------

Pipeline Instance 1:
----------------------------------------
MortonCode           -> Medium [3] (Start: 0.000000 ms, Exec: 2.762660 ms, End: 2.762660 ms)
RadixSort            -> Medium [3] (Start: 2.762660 ms, Exec: 3.122770 ms, End: 5.885430 ms)
RemoveDuplicates     -> Big [1] (Start: 5.885430 ms, Exec: 0.590511 ms, End: 6.475941 ms)
BuildRadixTree       -> Medium [3] (Start: 6.475941 ms, Exec: 6.722450 ms, End: 13.198391 ms)
EdgeCount            -> Small [4] (Start: 13.198391 ms, Exec: 1.224460 ms, End: 14.422851 ms)
EdgeOffset           -> Medium [3] (Start: 14.422851 ms, Exec: 0.756928 ms, End: 15.179779 ms)
BuildOctree          -> Medium [3] (Start: 15.179779 ms, Exec: 7.909900 ms, End: 23.089679 ms)

Pipeline Instance 1 Total Time: 23.089679 ms
(Start: 0.000000 ms, End: 23.089679 ms)

Pipeline Instance 2:
----------------------------------------
MortonCode           -> Medium [3] (Start: 2.762660 ms, Exec: 2.762660 ms, End: 5.525320 ms)
RadixSort            -> Medium [3] (Start: 5.885430 ms, Exec: 3.122770 ms, End: 9.008200 ms)
RemoveDuplicates     -> Medium [2] (Start: 12.590996 ms, Exec: 0.607395 ms, End: 13.198391 ms)
BuildRadixTree       -> Medium [3] (Start: 13.198391 ms, Exec: 6.722450 ms, End: 19.920841 ms)
EdgeCount            -> Medium [3] (Start: 20.859461 ms, Exec: 1.473290 ms, End: 22.332751 ms)
EdgeOffset           -> Medium [3] (Start: 22.332751 ms, Exec: 0.756928 ms, End: 23.089679 ms)
BuildOctree          -> Medium [3] (Start: 23.089679 ms, Exec: 7.909900 ms, End: 30.999579 ms)

Pipeline Instance 2 Total Time: 28.236919 ms
(Start: 2.762660 ms, End: 30.999579 ms)

Pipeline Instance 3:
----------------------------------------
MortonCode           -> Medium [2] (Start: 5.525320 ms, Exec: 4.213410 ms, End: 9.738730 ms)
RadixSort            -> Medium [2] (Start: 9.738730 ms, Exec: 7.751490 ms, End: 17.490220 ms)
RemoveDuplicates     -> Medium [2] (Start: 19.313446 ms, Exec: 0.607395 ms, End: 19.920841 ms)
BuildRadixTree       -> Medium [3] (Start: 19.920841 ms, Exec: 6.722450 ms, End: 26.643291 ms)
EdgeCount            -> Small [3] (Start: 28.747081 ms, Exec: 1.495570 ms, End: 30.242651 ms)
EdgeOffset           -> Medium [3] (Start: 30.242651 ms, Exec: 0.756928 ms, End: 30.999579 ms)
BuildOctree          -> Medium [3] (Start: 30.999579 ms, Exec: 7.909900 ms, End: 38.909479 ms)

Pipeline Instance 3 Total Time: 33.384159 ms
(Start: 5.525320 ms, End: 38.909479 ms)

Pipeline Instance 4:
----------------------------------------
MortonCode           -> Medium [3] (Start: 9.738730 ms, Exec: 2.762660 ms, End: 12.501390 ms)
RadixSort            -> Medium [3] (Start: 18.114773 ms, Exec: 3.122770 ms, End: 21.237543 ms)
RemoveDuplicates     -> Small [3] (Start: 26.021392 ms, Exec: 0.621899 ms, End: 26.643291 ms)
BuildRadixTree       -> Medium [3] (Start: 26.643291 ms, Exec: 6.722450 ms, End: 33.365741 ms)
EdgeCount            -> Small [2] (Start: 35.168858 ms, Exec: 2.806390 ms, End: 37.975248 ms)
EdgeOffset           -> Small [3] (Start: 37.975248 ms, Exec: 0.934231 ms, End: 38.909479 ms)
BuildOctree          -> Medium [3] (Start: 38.909479 ms, Exec: 7.909900 ms, End: 46.819379 ms)

Pipeline Instance 4 Total Time: 37.080649 ms
(Start: 9.738730 ms, End: 46.819379 ms)

Pipeline Instance 5:
----------------------------------------
MortonCode           -> Big [1] (Start: 16.206847 ms, Exec: 5.655250 ms, End: 21.862097 ms)
RadixSort            -> Medium [3] (Start: 21.862097 ms, Exec: 3.122770 ms, End: 24.984867 ms)
RemoveDuplicates     -> Small [2] (Start: 26.841348 ms, Exec: 0.990287 ms, End: 27.831635 ms)
BuildRadixTree       -> Medium [3] (Start: 33.365741 ms, Exec: 6.722450 ms, End: 40.088191 ms)
EdgeCount            -> Medium [3] (Start: 40.088191 ms, Exec: 1.473290 ms, End: 41.561481 ms)
EdgeOffset           -> Small [3] (Start: 45.885148 ms, Exec: 0.934231 ms, End: 46.819379 ms)
BuildOctree          -> Medium [3] (Start: 46.819379 ms, Exec: 7.909900 ms, End: 54.729279 ms)

Pipeline Instance 5 Total Time: 38.522432 ms
(Start: 16.206847 ms, End: 54.729279 ms)

Core Type Transitions:
Pipeline 1: Medium -> Big at RemoveDuplicates
Pipeline 1: Big -> Medium at BuildRadixTree
Pipeline 1: Medium -> Small at EdgeCount
Pipeline 1: Small -> Medium at EdgeOffset
Pipeline 3: Medium -> Small at EdgeCount
Pipeline 3: Small -> Medium at EdgeOffset
Pipeline 4: Medium -> Small at RemoveDuplicates
Pipeline 4: Small -> Medium at BuildRadixTree
Pipeline 4: Medium -> Small at EdgeCount
Pipeline 4: Small -> Medium at BuildOctree
Pipeline 5: Big -> Medium at RadixSort
Pipeline 5: Medium -> Small at RemoveDuplicates
Pipeline 5: Small -> Medium at BuildRadixTree
Pipeline 5: Medium -> Small at EdgeOffset
Pipeline 5: Small -> Medium at BuildOctree

Total Core Type Transitions: 15
Total Pipeline Time: 54.729279 ms

================================================================================
```
