#pragma once

#include <vector>
#include <cstdint>

// Enumeration for allowed data types
enum class DataType {
    FP32,
    FP16,
    INT8
};

// Interface for Matrix Multiplication
// C = A * B
// A is M x K
// B is K x N
// C is M x N
// We use pointers to raw data to simulate the low-level API likely provided by the platform.

template <typename T>
void matmul_naive(const T* A, const T* B, T* C, int M, int N, int K);

template <typename T>
void matmul_optimized(const T* A, const T* B, T* C, int M, int N, int K);

// Amadeus-specific: A (uint8) @ B (int8) -> C (int32)
void matmul_amadeus(const uint8_t* A, const int8_t* B, int32_t* C, 
                    int M, int K, int N);

// Helper to fill random data
template <typename T>
void randomize_matrix(T* mat, int rows, int cols);

// Helper to zero matrix
template <typename T>
void zero_matrix(T* mat, int rows, int cols);

// Helper to compare matrices
template <typename T>
bool compare_matrices(const T* C_ref, const T* C_opt, int rows, int cols, double epsilon = 1e-4);
