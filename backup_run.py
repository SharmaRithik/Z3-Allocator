import sys
import re

def read_benchmarks(filename):
    with open(filename, 'r') as f:
        content = f.read().strip()
    benchmarks = content.split('\n\n')
    return [bench.split('\n') for bench in benchmarks]

def filter_full_core_benchmarks(benchmarks):
    full_core_benchmarks = []

    # For small cores (4 threads)
    small_cores_full = [line for line in benchmarks[0] if "Threads:4" in line]
    full_core_benchmarks.append(small_cores_full)

    # For medium cores (2 threads)
    medium_cores_full = [line for line in benchmarks[1] if "Threads:2" in line]
    full_core_benchmarks.append(medium_cores_full)

    # For big cores (2 threads)
    big_cores_full = [line for line in benchmarks[2] if "Threads:2" in line]
    full_core_benchmarks.append(big_cores_full)

    return full_core_benchmarks

def extract_info(line):
    match = re.match(r'(CPU/[A-Za-z_]+)/Threads:(\d+)/iterations:\d+\s+(\d+\.\d+\s+ms)', line)
    if match:
        device_name = match.group(1)
        num_threads = match.group(2)
        exec_time = match.group(3)
        return f"{device_name}/Threads:{num_threads} {exec_time}"
    return None

def print_full_core_benchmarks(full_core_benchmarks):
    for bench in full_core_benchmarks:
        for line in bench:
            info = extract_info(line)
            if info:
                print(info)
            else:
                print(f"Line didn't match: {line}")  # Debugging line to see which lines didn't match
        print()

def main():
    if len(sys.argv) != 2 or sys.argv[1] != 'full':
        print("Usage: python3 run.py full")
        return

    filename = 'cpu_benchmark.txt'
    benchmarks = read_benchmarks(filename)
    full_core_benchmarks = filter_full_core_benchmarks(benchmarks)
    print_full_core_benchmarks(full_core_benchmarks)

if __name__ == "__main__":
    main()

