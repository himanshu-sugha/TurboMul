#include "matmul.h"
#include <random>
#include <cmath>
#include <iostream>

template <typename T>
void matmul_naive(const T* A, const T* B, T* C, int M, int N, int K) {
    // Naive O(N^3) implementation
    // Row-major assumption for all matrices
    for (int i = 0; i < M; ++i) {
        for (int j = 0; j < N; ++j) {
            T sum = 0;
            for (int k = 0; k < K; ++k) {
                // A[i][k] * B[k][j]
                sum += A[i * K + k] * B[k * N + j];
            }
            C[i * N + j] = sum;
        }
    }
}

// Explicit Instantiations for likely types
template void matmul_naive<float>(const float* A, const float* B, float* C, int M, int N, int K);
template void matmul_naive<double>(const double* A, const double* B, double* C, int M, int N, int K);
template void matmul_naive<int8_t>(const int8_t* A, const int8_t* B, int8_t* C, int M, int N, int K);
// Note: FP16 usually requires _Float16 or similar, waiting for toolchain details.

template <typename T>
void randomize_matrix(T* mat, int rows, int cols) {
    static std::mt19937 gen(42); // Fixed seed for reproducibility per rules
    std::uniform_real_distribution<> dis(-1.0, 1.0);
    for (int i = 0; i < rows * cols; ++i) {
        mat[i] = static_cast<T>(dis(gen));
    }
}

// Specialization for int8
template <>
void randomize_matrix<int8_t>(int8_t* mat, int rows, int cols) {
    static std::mt19937 gen(42);
    std::uniform_int_distribution<> dis(-127, 127);
    for (int i = 0; i < rows * cols; ++i) {
        mat[i] = static_cast<int8_t>(dis(gen));
    }
}

template <typename T>
void zero_matrix(T* mat, int rows, int cols) {
    for (int i = 0; i < rows * cols; ++i) {
        mat[i] = 0;
    }
}

template <typename T>
bool compare_matrices(const T* C_ref, const T* C_opt, int rows, int cols, double epsilon) {
    for (int i = 0; i < rows * cols; ++i) {
        double diff = std::abs(static_cast<double>(C_ref[i]) - static_cast<double>(C_opt[i]));
        if (diff > epsilon) {
            std::cerr << "Mismatch at index " << i << ": Ref=" << (double)C_ref[i] 
                      << ", Opt=" << (double)C_opt[i] << ", Diff=" << diff << std::endl;
            return false;
        }
    }
    return true;
}

// Instantiations helpers
template void randomize_matrix<float>(float* mat, int rows, int cols);
template void zero_matrix<float>(float* mat, int rows, int cols);
template bool compare_matrices<float>(const float* C_ref, const float* C_opt, int rows, int cols, double epsilon);

template void randomize_matrix<int8_t>(int8_t* mat, int rows, int cols);
template void zero_matrix<int8_t>(int8_t* mat, int rows, int cols);
template bool compare_matrices<int8_t>(const int8_t* C_ref, const int8_t* C_opt, int rows, int cols, double epsilon);
