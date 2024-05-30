import sys
import re
import json

def read_benchmarks(filename):
    with open(filename, 'r') as f:
        content = f.read().strip()
    benchmarks = content.split('\n\n')  # Split by double newlines
    return [bench.strip().split('\n') for bench in benchmarks if bench.strip()]

def filter_full_core_benchmarks(benchmarks):
    full_core_benchmarks = []

    #print("Benchmark sections found:", len(benchmarks))
    #for i, section in enumerate(benchmarks):
        #print(f"Section {i}:", section)

    # For small cores (4 threads)
    small_cores_full = [line for line in benchmarks[0] if "Threads:4" in line]
    full_core_benchmarks.append(small_cores_full)
    #print("Small cores:", small_cores_full)

    # For medium cores (2 threads)
    medium_cores_full = [line for line in benchmarks[1] if "Threads:2" in line]
    full_core_benchmarks.append(medium_cores_full)
    #print("Medium cores:", medium_cores_full)

    # For big cores (2 threads)
    big_cores_full = [line for line in benchmarks[2] if "Threads:2" in line]
    full_core_benchmarks.append(big_cores_full)
    #print("Big cores:", big_cores_full)

    return full_core_benchmarks

def extract_info(line):
    #print(f"Extracting info from line: {line}")
    match = re.match(r'CPU/([^/]+)/Threads:(\d+)/iterations:\d+\s+(\d+\.\d+)\s+ms', line)
    if match:
        task_name = match.group(1)
        num_threads = int(match.group(2))
        exec_time = float(match.group(3))
        info = {
            "task": task_name,
            "threads": num_threads,
            "time": exec_time
        }
        #print(f"Extracted info: {info}")
        return info
    print("No match found")
    return None

def print_full_core_benchmarks(full_core_benchmarks, output_filename):
    benchmark_data = {"small_cores": [], "medium_cores": [], "big_cores": []}
    for bench in full_core_benchmarks:
        for line in bench:
            info = extract_info(line)
            if info:
                if info["threads"] == 4:
                    benchmark_data["small_cores"].append(info)
                elif info["threads"] == 2:
                    if line in full_core_benchmarks[1]:  # from medium cores section
                        benchmark_data["medium_cores"].append(info)
                    elif line in full_core_benchmarks[2]:  # from big cores section
                        benchmark_data["big_cores"].append(info)
    
    #print("Benchmark data to be written:", json.dumps(benchmark_data, indent=2))
    with open(output_filename, 'w') as f:
        json.dump(benchmark_data, f, indent=2)

def main():
    if len(sys.argv) != 2 or sys.argv[1] != 'full':
        print("Usage: python3 run.py full")
        return

    filename = 'cpu_benchmark.txt'
    output_filename = 'benchmark_data.json'
    benchmarks = read_benchmarks(filename)
    full_core_benchmarks = filter_full_core_benchmarks(benchmarks)
    print_full_core_benchmarks(full_core_benchmarks, output_filename)

if __name__ == "__main__":
    main()

