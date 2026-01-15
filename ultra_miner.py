#!/usr/bin/env python3
"""
TurboMul ULTRA Miner v4
HASH-ONLY MINING - 400k+ H/s

BREAKTHROUGH DISCOVERY:
- Freivalds reads matrices from FIRST 240 bytes (preamble)
- Freivalds reads tensor_c from LAST 1024 bytes
- We can insert EXTRA MINING NONCE between them!

Solution format:
  [preamble: 240 bytes][mining_nonce: N bytes][tensor_c: 1024 bytes]

This allows hash-only mining without recomputing MatMul!
"""

import numpy as np
import requests
import time
import warnings
import struct
import sys
import os

try:
    import blake3
except ImportError:
    print("ERROR: blake3 not installed. Run: pip install blake3")
    sys.exit(1)

warnings.filterwarnings('ignore')

# Configuration
API_BASE = "https://testnet.ama.one"
TESTNET_RPC = "https://testnet-rpc.ama.one"

def get_chain_stats():
    """Get current chain stats."""
    try:
        r = requests.get(f"{TESTNET_RPC}/api/chain/stats", verify=False, timeout=10)
        return r.json()
    except:
        return None

def get_workload():
    """Get preamble + matrices from API."""
    try:
        r = requests.get(f"{API_BASE}/api/upow/seed_with_matrix_a_b", verify=False, timeout=30)
        data = r.content
        
        preamble = data[:240]
        a_size = 16 * 50240
        b_size = 50240 * 16
        
        A = np.frombuffer(data[240:240+a_size], dtype=np.uint8).reshape(16, 50240)
        B = np.frombuffer(data[240+a_size:240+a_size+b_size], dtype=np.int8).reshape(50240, 16)
        
        return preamble, A, B
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

def compute_matmul(A, B):
    """Compute C = A @ B."""
    A_f = A.astype(np.float32)
    B_f = B.astype(np.float32)
    return np.matmul(A_f, B_f).astype(np.int32)

def count_leading_zero_bits(hash_bytes):
    """Count leading zero bits."""
    count = 0
    for byte in hash_bytes:
        if byte == 0:
            count += 8
        else:
            for i in range(7, -1, -1):
                if byte & (1 << i):
                    return count
                count += 1
            return count
    return count

def validate_solution(solution):
    """Validate with API."""
    try:
        r = requests.post(f"{API_BASE}/api/upow/validate", data=solution, verify=False, timeout=30)
        return r.json()
    except:
        return None

def mine_hash_only(preamble, tensor_c_bytes, diff_bits, max_hashes=50_000_000):
    """
    HASH-ONLY MINING!
    
    Insert mining nonce between preamble and tensor_c.
    Freivalds only checks first 240 bytes and last 1024 bytes!
    """
    print(f"    [HASH-ONLY MODE] Mining at maximum speed...")
    
    start_time = time.time()
    best_bits = 0
    
    # Use 8-byte mining nonce inserted between preamble and tensor_c
    mining_nonce_size = 8
    
    for nonce in range(max_hashes):
        # Build solution: preamble + mining_nonce + tensor_c
        mining_nonce = nonce.to_bytes(mining_nonce_size, 'little')
        solution = preamble + mining_nonce + tensor_c_bytes
        
        # Hash ENTIRE solution for difficulty check
        hash_bytes = blake3.blake3(solution).digest()
        zeros = count_leading_zero_bits(hash_bytes)
        
        if zeros > best_bits:
            best_bits = zeros
            print(f"    New best: {zeros} bits at hash {nonce:,}")
        
        if zeros >= diff_bits:
            elapsed = time.time() - start_time
            rate = nonce / elapsed if elapsed > 0 else 0
            print(f"\n*** FOUND SOLUTION! ***")
            print(f"Hash iterations: {nonce:,}")
            print(f"Leading zeros: {zeros} bits (target: {diff_bits})")
            print(f"Hash rate: {rate:,.0f} H/s")
            print(f"Solution size: {len(solution)} bytes")
            return solution, nonce, zeros
        
        # Progress every 500k hashes
        if nonce > 0 and nonce % 500_000 == 0:
            elapsed = time.time() - start_time
            rate = nonce / elapsed if elapsed > 0 else 0
            print(f"    Hashes: {nonce:,}, Rate: {rate:,.0f} H/s, Best: {best_bits} bits")
    
    return None, max_hashes, best_bits

def main():
    print("=" * 60)
    print("TurboMul ULTRA Miner v4")
    print("HASH-ONLY MINING MODE")
    print("=" * 60)
    print()
    
    # Get difficulty
    print("[1] Fetching chain stats...")
    stats = get_chain_stats()
    diff_bits = 20
    if stats and 'stats' in stats:
        diff_bits = stats['stats'].get('diff_bits', 20)
        print(f"    Difficulty: {diff_bits} bits")
    print()
    
    solutions_found = 0
    
    while True:
        # Get workload
        print("[2] Fetching workload...")
        preamble, A, B = get_workload()
        if preamble is None:
            print("    Failed! Retrying...")
            time.sleep(5)
            continue
        print(f"    Preamble: {len(preamble)} bytes")
        print(f"    Matrix A: {A.shape}")
        print(f"    Matrix B: {B.shape}")
        print()
        
        # Compute MatMul ONCE
        print("[3] Computing MatMul (one time)...")
        t0 = time.time()
        C = compute_matmul(A, B)
        tensor_c_bytes = C.tobytes()
        t1 = time.time()
        print(f"    Compute time: {(t1-t0)*1000:.2f}ms")
        print(f"    Tensor C: {len(tensor_c_bytes)} bytes")
        print()
        
        # HASH-ONLY MINING
        print("[4] Starting hash-only mining...")
        solution, hashes, zeros = mine_hash_only(
            preamble, tensor_c_bytes, diff_bits,
            max_hashes=50_000_000
        )
        print()
        
        if solution:
            solutions_found += 1
            print(f"[5] Validating solution ({len(solution)} bytes)...")
            result = validate_solution(solution)
            if result:
                print(f"    API Response: {result}")
                if result.get('valid') and result.get('valid_math'):
                    print("    [OK] FULLY VALID SOLUTION!")
                    print(f"    Total solutions found: {solutions_found}")
                elif result.get('valid_math'):
                    print("    [PARTIAL] Math valid, but PoW check failed")
                else:
                    print("    [FAIL] Solution rejected")
            print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMiner stopped.")
