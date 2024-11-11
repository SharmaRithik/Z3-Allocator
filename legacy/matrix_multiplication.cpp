#include <iostream>
#include <vector>
#include <chrono>
#include <thread>
#include <sched.h>
#include <unistd.h>
#include <cstring>

using namespace std;
using namespace chrono;

// Function to perform matrix multiplication using a specified range of rows
void matrixMultiplyPartial(const vector<vector<float>>& A, const vector<vector<float>>& B, vector<vector<float>>& C, int startRow, int endRow) {
    int n = A.size();
    for (int i = startRow; i < endRow; ++i) {
        for (int j = 0; j < n; ++j) {
            C[i][j] = 0;
            for (int k = 0; k < n; ++k) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}

// Function to perform matrix multiplication using a thread pool
void matrixMultiplyThreadPool(const vector<vector<float>>& A, const vector<vector<float>>& B, vector<vector<float>>& C, int numThreads) {
    int n = A.size();
    vector<thread> threads;
    int rowsPerThread = n / numThreads;

    for (int i = 0; i < numThreads; ++i) {
        int startRow = i * rowsPerThread;
        int endRow = (i == numThreads - 1) ? n : startRow + rowsPerThread;
        threads.emplace_back(matrixMultiplyPartial, cref(A), cref(B), ref(C), startRow, endRow);
    }

    for (auto& th : threads) {
        th.join();
    }
}

// Function to benchmark matrix multiplication using a thread pool
double benchmark(int size, int numThreads) {
    vector<vector<float>> A(size, vector<float>(size, 1.0));
    vector<vector<float>> B(size, vector<float>(size, 1.0));
    vector<vector<float>> C(size, vector<float>(size, 0.0));

    auto start = high_resolution_clock::now();
    matrixMultiplyThreadPool(A, B, C, numThreads);
    auto end = high_resolution_clock::now();

    duration<double> duration = end - start;
    return duration.count();
}

// Function to set CPU affinity
void setCpuAffinity(const vector<int>& cores) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    for (int core : cores) {
        CPU_SET(core, &cpuset);
    }

    int result = sched_setaffinity(0, sizeof(cpu_set_t), &cpuset);
    if (result != 0) {
        cerr << "Error setting CPU affinity: " << strerror(errno) << endl;
    }
}

void benchmarkCoreType(const vector<int>& cores, const string& coreType) {
    vector<int> sizes = {100, 200, 300, 400, 500, 600, 700, 800, 900, 1000};

    for (int numThreads = 1; numThreads <= cores.size(); ++numThreads) {
        cout << "Benchmarking " << coreType << " cores with " << numThreads << " threads" << endl;
        vector<int> activeCores(cores.begin(), cores.begin() + numThreads);
        setCpuAffinity(activeCores);
        for (int size : sizes) {
            double time = benchmark(size, numThreads);
            cout << "Cores: ";
            for (int core : activeCores) {
                cout << core << " ";
            }
            cout << ", Size: " << size << "x" << size << ", Threads: " << numThreads << ", Time: " << time << " seconds" << endl;
        }
    }
}

int main() {
    vector<int> efficiency_cores = {0, 1, 2, 3}; // Cortex-A55
    vector<int> performance_cores = {4, 5}; // Cortex-A78
    vector<int> prime_cores = {6, 7}; // Cortex-X1

    benchmarkCoreType(efficiency_cores, "high-efficiency (Cortex-A55)");
    benchmarkCoreType(performance_cores, "high-performance (Cortex-A78)");
    benchmarkCoreType(prime_cores, "prime (Cortex-X1)");

    return 0;
}

