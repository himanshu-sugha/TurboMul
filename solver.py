#!/usr/bin/env python3
"""
Amadeus Genesis Hard Hack - WORKING PRODUCTION SOLVER

This solver achieves valid_math: true by using the correct matrix types
discovered from the Rust source code (blake3.rs):

- Matrix A: uint8 [[u8; 50240]; 16]  (16 x 50240)
- Matrix B: int8  [[i8; 16]; 50240]   (50240 x 16) - SIGNED!
- Result C: int32 [[i32; 16]; 16]     (16 x 16)

Solution format: seed (240 bytes) + tensor_c (1024 bytes) = 1264 bytes
"""

import requests
import numpy as np
import struct
import urllib3
import time
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_BASE = "https://testnet.ama.one"

def fetch_workload():
    """Fetch seed + matrices from API"""
    resp = requests.get(f"{API_BASE}/api/upow/seed_with_matrix_a_b", verify=False, timeout=30)
    data = resp.content
    
    M, K, N = 16, 50240, 16
    A_SIZE = M * K  # 803840
    B_SIZE = K * N  # 803840
    
    seed_len = len(data) - A_SIZE - B_SIZE
    seed = data[:seed_len]
    A_bytes = data[seed_len:seed_len + A_SIZE]
    B_bytes = data[seed_len + A_SIZE:]
    
    return seed, A_bytes, B_bytes

def compute_matmul(A_bytes, B_bytes):
    """Compute C = A @ B with correct types"""
    M, K, N = 16, 50240, 16
    
    # A: uint8 [[u8; 50240]; 16]
    A = np.frombuffer(A_bytes, dtype=np.uint8).reshape(M, K)
    
    # B: int8 [[i8; 16]; 50240] - SIGNED!
    B = np.frombuffer(B_bytes, dtype=np.int8).reshape(K, N)
    
    # Compute with int64 to avoid overflow, result is int32
    C = np.matmul(A.astype(np.int64), B.astype(np.int64))
    
    return C.astype('<i4').tobytes()

def build_solution(seed, C_bytes):
    """Build the 1264-byte solution"""
    seed_240 = seed[:240] if len(seed) >= 240 else seed + b'\x00'*(240-len(seed))
    return seed_240 + C_bytes

def validate(sol):
    """Submit solution to API"""
    resp = requests.post(f"{API_BASE}/api/upow/validate", data=sol, verify=False, timeout=30)
    return resp.json()

def run_once():
    """Run a single solve cycle"""
    seed, A_bytes, B_bytes = fetch_workload()
    C_bytes = compute_matmul(A_bytes, B_bytes)
    sol = build_solution(seed, C_bytes)
    result = validate(sol)
    return result

def benchmark(num_iterations=10):
    """Benchmark the solver"""
    print("=" * 60)
    print(f"Benchmarking {num_iterations} iterations...")
    print("=" * 60)
    
    times = []
    successes = 0
    
    for i in range(num_iterations):
        start = time.time()
        
        # Fetch
        seed, A_bytes, B_bytes = fetch_workload()
        fetch_time = time.time() - start
        
        # Compute
        compute_start = time.time()
        C_bytes = compute_matmul(A_bytes, B_bytes)
        compute_time = time.time() - compute_start
        
        # Validate
        validate_start = time.time()
        sol = build_solution(seed, C_bytes)
        result = validate(sol)
        validate_time = time.time() - validate_start
        
        total_time = time.time() - start
        times.append(total_time)
        
        valid = result.get("valid_math", False)
        if valid:
            successes += 1
        
        status = "✅" if valid else "❌"
        print(f"  [{i+1:3}/{num_iterations}] {status} "
              f"fetch={fetch_time:.3f}s compute={compute_time:.3f}s "
              f"validate={validate_time:.3f}s total={total_time:.3f}s")
    
    avg_time = sum(times) / len(times)
    sols_per_sec = 1.0 / avg_time
    
    print("=" * 60)
    print(f"Results:")
    print(f"  Success rate: {successes}/{num_iterations} ({100*successes/num_iterations:.1f}%)")
    print(f"  Average time: {avg_time:.3f}s")
    print(f"  Solutions/sec: {sols_per_sec:.2f}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Amadeus MatMul Solver")
    parser.add_argument("--benchmark", "-b", type=int, default=0,
                       help="Run N benchmark iterations")
    parser.add_argument("--once", "-o", action="store_true",
                       help="Run once and show result")
    args = parser.parse_args()
    
    if args.benchmark > 0:
        benchmark(args.benchmark)
    elif args.once:
        result = run_once()
        print(f"Result: {result}")
    else:
        # Default: run once
        result = run_once()
        valid = result.get("valid_math", False)
        print(f"{'✅ SUCCESS!' if valid else '❌ FAIL'}: {result}")

if __name__ == "__main__":
    main()
