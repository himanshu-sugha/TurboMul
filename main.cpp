#include <iostream>
#include <vector>
#include <chrono>
#include <iomanip>
#include <cstring>
#include "matmul.h"

#ifdef USE_OPENBLAS
#include <cblas.h>
#endif

void print_usage(const char* prog_name) {
    std::cerr << "Usage: " << prog_name << " <M> <N> <K> [iterations]" << std::endl;
}

int main(int argc, char** argv) {
    if (argc < 4) {
        print_usage(argv[0]);
        return 1;
    }

    int M = std::atoi(argv[1]);
    int N = std::atoi(argv[2]);
    int K = std::atoi(argv[3]);
    int iterations = (argc > 4) ? std::atoi(argv[4]) : 5;

    std::cout << "Benchmarking Matrix Multiplication:" << std::endl;
    std::cout << "Dimensions: M=" << M << ", N=" << N << ", K=" << K << std::endl;
    std::cout << "Precision: FP32 (Float)" << std::endl; // Default for now

    // Allocate memory
    std::vector<float> A(M * K);
    std::vector<float> B(K * N);
    std::vector<float> C_naive(M * N);
    std::vector<float> C_opt(M * N);
    std::vector<float> C_blas(M * N);

    // Initialize
    randomize_matrix(A.data(), M, K);
    randomize_matrix(B.data(), K, N);
    zero_matrix(C_naive.data(), M, N);
    zero_matrix(C_opt.data(), M, N);
    zero_matrix(C_blas.data(), M, N);

    // --- Benchmark Naive ---
    std::cout << "Running Naive..." << std::endl;
    auto start = std::chrono::high_resolution_clock::now();
    matmul_naive(A.data(), B.data(), C_naive.data(), M, N, K);
    auto end = std::chrono::high_resolution_clock::now();
    double naive_dur = std::chrono::duration<double>(end - start).count();
    double naive_gflops = (2.0 * M * N * K) / (naive_dur * 1e9);
    std::cout << "Naive: " << naive_dur << "s | " << naive_gflops << " GFLOPS" << std::endl;

    // --- Benchmark Optimized ---
    // Warmup
    matmul_optimized(A.data(), B.data(), C_opt.data(), M, N, K);
    zero_matrix(C_opt.data(), M, N);

    std::cout << "Running Optimized..." << std::endl;
    double total_opt_dur = 0;
    for(int i=0; i<iterations; ++i) {
        start = std::chrono::high_resolution_clock::now();
        matmul_optimized(A.data(), B.data(), C_opt.data(), M, N, K);
        end = std::chrono::high_resolution_clock::now();
        total_opt_dur += std::chrono::duration<double>(end - start).count();
        // Don't zero in between if accumulator overwrites? 
        // Our current matmul adds to C? No, it usually overwrites.
        // Let's assume overwrite for standard GEMM or we need to zero. 
        // My simple impls accumulate/assign. Naive overwrites. Opt overwrites.
        if (i < iterations - 1) zero_matrix(C_opt.data(), M, N); 
    }
    double avg_opt_dur = total_opt_dur / iterations;
    double opt_gflops = (2.0 * M * N * K) / (avg_opt_dur * 1e9);
    
    std::cout << "Optimized (Avg " << iterations << " runs): " << avg_opt_dur << "s | " << opt_gflops << " GFLOPS" << std::endl;

    // Verify Correctness
    bool pass = compare_matrices(C_naive.data(), C_opt.data(), M, N);
    std::cout << "Correctness (Naive vs Opt): " << (pass ? "PASS" : "FAIL") << std::endl;

    // --- Benchmark OpenBLAS (if available) ---
#ifdef USE_OPENBLAS
    std::cout << "Running OpenBLAS..." << std::endl;
    start = std::chrono::high_resolution_clock::now();
    cblas_sgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, 
                M, N, K, 1.0f, A.data(), K, B.data(), N, 0.0f, C_blas.data(), N);
    end = std::chrono::high_resolution_clock::now();
    double blas_dur = std::chrono::duration<double>(end - start).count();
    double blas_gflops = (2.0 * M * N * K) / (blas_dur * 1e9);
    std::cout << "OpenBLAS: " << blas_dur << "s | " << blas_gflops << " GFLOPS" << std::endl;
    
    bool pass_blas = compare_matrices(C_naive.data(), C_blas.data(), M, N);
    std::cout << "Correctness (Naive vs BLAS): " << (pass_blas ? "PASS" : "FAIL") << std::endl;
#endif

    // --- Output JSON Metrics (for Submission) ---
    std::cout << "\n{";
    std::cout << "\"latency_ms\": " << avg_opt_dur * 1000 << ",";
    std::cout << "\"throughput_gflops\": " << opt_gflops << ",";
    std::cout << "\"correctness\": " << (pass ? "true" : "false");
    std::cout << "}" << std::endl;

    return 0;
}
