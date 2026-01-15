#include "matmul.h"
#include <cstdint>
#include <cstring>
#include <algorithm>

// Tile sizes tuned for L1 cache
constexpr int TILE_SIZE = 64;

/**
 * Amadeus-specific MatMul: A (uint8) @ B (int8) -> C (int32)
 * 
 * From Rust source (amadeus-utils/src/blake3.rs):
 *   A: [[u8; 50240]; 16]   - shape 16 x 50240, dtype uint8
 *   B: [[i8; 16]; 50240]   - shape 50240 x 16, dtype int8 (SIGNED!)
 *   C: [[i32; 16]; 16]     - shape 16 x 16, dtype int32
 */
void matmul_amadeus(const uint8_t* A, const int8_t* B, int32_t* C, 
                    int M, int K, int N) {
    // Zero output first
    std::memset(C, 0, M * N * sizeof(int32_t));
    
    // Tiled matrix multiplication for cache efficiency
    for (int i0 = 0; i0 < M; i0 += TILE_SIZE) {
        int i_max = std::min(i0 + TILE_SIZE, M);
        
        for (int k0 = 0; k0 < K; k0 += TILE_SIZE) {
            int k_max = std::min(k0 + TILE_SIZE, K);
            
            for (int j0 = 0; j0 < N; j0 += TILE_SIZE) {
                int j_max = std::min(j0 + TILE_SIZE, N);
                
                // IKJ order for best cache pattern
                for (int i = i0; i < i_max; ++i) {
                    for (int k = k0; k < k_max; ++k) {
                        // A is uint8, need to widen to int32
                        int32_t a_ik = static_cast<int32_t>(A[i * K + k]);
                        
                        // Unroll by 4 for ILP
                        int j = j0;
                        for (; j + 4 <= j_max; j += 4) {
                            // B is int8 (signed!), widen to int32
                            C[i * N + j]     += a_ik * static_cast<int32_t>(B[k * N + j]);
                            C[i * N + j + 1] += a_ik * static_cast<int32_t>(B[k * N + j + 1]);
                            C[i * N + j + 2] += a_ik * static_cast<int32_t>(B[k * N + j + 2]);
                            C[i * N + j + 3] += a_ik * static_cast<int32_t>(B[k * N + j + 3]);
                        }
                        // Handle remainder
                        for (; j < j_max; ++j) {
                            C[i * N + j] += a_ik * static_cast<int32_t>(B[k * N + j]);
                        }
                    }
                }
            }
        }
    }
}

// Original template implementation for generic usage
template <typename T>
void matmul_optimized(const T* A, const T* B, T* C, int M, int N, int K) {
    std::memset(C, 0, M * N * sizeof(T));
    
    for (int i0 = 0; i0 < M; i0 += TILE_SIZE) {
        int i_max = std::min(i0 + TILE_SIZE, M);
        
        for (int k0 = 0; k0 < K; k0 += TILE_SIZE) {
            int k_max = std::min(k0 + TILE_SIZE, K);
            
            for (int j0 = 0; j0 < N; j0 += TILE_SIZE) {
                int j_max = std::min(j0 + TILE_SIZE, N);
                
                for (int i = i0; i < i_max; ++i) {
                    for (int k = k0; k < k_max; ++k) {
                        T a_ik = A[i * K + k];
                        
                        int j = j0;
                        for (; j + 4 <= j_max; j += 4) {
                            C[i * N + j]     += a_ik * B[k * N + j];
                            C[i * N + j + 1] += a_ik * B[k * N + j + 1];
                            C[i * N + j + 2] += a_ik * B[k * N + j + 2];
                            C[i * N + j + 3] += a_ik * B[k * N + j + 3];
                        }
                        for (; j < j_max; ++j) {
                            C[i * N + j] += a_ik * B[k * N + j];
                        }
                    }
                }
            }
        }
    }
}

// Explicit instantiations
template void matmul_optimized<float>(const float* A, const float* B, float* C, int M, int N, int K);
template void matmul_optimized<double>(const double* A, const double* B, double* C, int M, int N, int K);
template void matmul_optimized<int32_t>(const int32_t* A, const int32_t* B, int32_t* C, int M, int N, int K);
