#!/usr/bin/env python3
"""
TurboMul Turbo Miner v3
Maximum Performance Edition

Key optimizations:
1. Multi-process parallel mining (use all CPU cores)
2. Batch processing to reduce API overhead
3. Optimized Blake3 hashing
"""

import numpy as np
import requests
import time
import warnings
import struct
import sys
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

try:
    import blake3
except ImportError:
    print("ERROR: blake3 not installed. Run: pip install blake3")
    sys.exit(1)

warnings.filterwarnings('ignore')

# Configuration
API_BASE = "https://testnet.ama.one"
TESTNET_RPC = "https://testnet-rpc.ama.one"
NUM_WORKERS = multiprocessing.cpu_count()

def get_chain_stats():
    """Get current chain stats including difficulty."""
    try:
        r = requests.get(f"{TESTNET_RPC}/api/chain/stats", verify=False, timeout=10)
        return r.json()
    except Exception as e:
        return None

def get_seed_info():
    """Get seed components from API."""
    try:
        r = requests.get(f"{API_BASE}/api/upow/seed_with_matrix_a_b", verify=False, timeout=30)
        data = r.content
        preamble = data[:240]
        epoch = struct.unpack('<I', preamble[0:4])[0]
        segment_vr_hash = preamble[4:36]
        pk = preamble[36:84]
        pop = preamble[84:180]
        computor = preamble[180:228]
        return {
            'epoch': epoch,
            'segment_vr_hash': segment_vr_hash,
            'pk': pk,
            'pop': pop,
            'computor': computor
        }
    except Exception as e:
        return None

def derive_matrices_from_preamble(preamble):
    """Derive matrices A, B from preamble using Blake3 XOF."""
    hasher = blake3.blake3(preamble)
    a_size = 16 * 50240
    b_size = 50240 * 16
    total_size = a_size + b_size
    xof_output = hasher.digest(length=total_size)
    A = np.frombuffer(xof_output[:a_size], dtype=np.uint8).reshape(16, 50240)
    B = np.frombuffer(xof_output[a_size:], dtype=np.int8).reshape(50240, 16)
    return A, B

def build_preamble(epoch, segment_vr_hash, pk, pop, computor, nonce):
    """Build 240-byte preamble."""
    preamble = struct.pack('<I', epoch)
    preamble += segment_vr_hash
    preamble += pk
    preamble += pop
    preamble += computor
    preamble += nonce
    return preamble

def compute_matmul(A, B):
    """Compute C = A @ B using float32 optimization."""
    A_f = A.astype(np.float32)
    B_f = B.astype(np.float32)
    C = np.matmul(A_f, B_f).astype(np.int32)
    return C

def count_leading_zero_bits(hash_bytes):
    """Count leading zero bits in hash."""
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

def mine_batch(args):
    """Worker function for parallel mining."""
    seed_info, diff_bits, batch_size, worker_id = args
    
    epoch = seed_info['epoch']
    segment_vr_hash = seed_info['segment_vr_hash']
    pk = seed_info['pk']
    pop = seed_info['pop']
    computor = seed_info['computor']
    
    best_bits = 0
    
    for i in range(batch_size):
        nonce = os.urandom(12)
        preamble = build_preamble(epoch, segment_vr_hash, pk, pop, computor, nonce)
        A, B = derive_matrices_from_preamble(preamble)
        C = compute_matmul(A, B)
        tensor_c_bytes = C.tobytes()
        solution = preamble + tensor_c_bytes
        hash_bytes = blake3.blake3(solution).digest()
        zeros = count_leading_zero_bits(hash_bytes)
        
        if zeros > best_bits:
            best_bits = zeros
        
        if zeros >= diff_bits:
            return {
                'found': True,
                'solution': solution,
                'nonce': nonce,
                'zeros': zeros,
                'attempts': i + 1,
                'worker_id': worker_id
            }
    
    return {
        'found': False,
        'best_bits': best_bits,
        'attempts': batch_size,
        'worker_id': worker_id
    }

def validate_solution(solution):
    """Validate solution with API."""
    try:
        r = requests.post(
            f"{API_BASE}/api/upow/validate",
            data=solution,
            verify=False,
            timeout=30
        )
        return r.json()
    except Exception as e:
        return None

def main():
    print("=" * 60)
    print("TurboMul TURBO Miner v3")
    print(f"Using {NUM_WORKERS} CPU cores")
    print("=" * 60)
    print()
    
    # Get chain stats
    print("[1] Fetching chain stats...")
    stats = get_chain_stats()
    if stats and 'stats' in stats:
        diff_bits = stats['stats'].get('diff_bits', 20)
        print(f"    Difficulty: {diff_bits} bits")
    else:
        diff_bits = 20
    print()
    
    # Get seed info once
    print("[2] Fetching seed info...")
    seed_info = get_seed_info()
    if seed_info is None:
        print("    Failed!")
        return
    print(f"    Epoch: {seed_info['epoch']}")
    print()
    
    # Mining loop
    batch_size = 100  # Solutions per worker per round
    total_attempts = 0
    solutions_found = 0
    start_time = time.time()
    
    print(f"[3] Mining with {NUM_WORKERS} parallel workers...")
    print(f"    Target: {diff_bits} leading zero bits")
    print()
    
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        round_num = 0
        
        while True:
            round_num += 1
            
            # Submit batch jobs to all workers
            futures = []
            for worker_id in range(NUM_WORKERS):
                args = (seed_info, diff_bits, batch_size, worker_id)
                futures.append(executor.submit(mine_batch, args))
            
            # Collect results
            round_attempts = 0
            best_in_round = 0
            
            for future in as_completed(futures):
                result = future.result()
                round_attempts += result['attempts']
                
                if result['found']:
                    solution = result['solution']
                    zeros = result['zeros']
                    
                    elapsed = time.time() - start_time
                    total_attempts += round_attempts
                    rate = total_attempts / elapsed if elapsed > 0 else 0
                    
                    print(f"\n*** FOUND SOLUTION! ***")
                    print(f"Worker: {result['worker_id']}")
                    print(f"Leading zeros: {zeros} bits")
                    print(f"Total rate: {rate:.1f} sols/sec")
                    
                    print("\n[4] Validating...")
                    valid = validate_solution(solution)
                    if valid:
                        print(f"    API Response: {valid}")
                        if valid.get('valid') and valid.get('valid_math'):
                            print("    [OK] VALID SOLUTION!")
                            solutions_found += 1
                    
                    # Refresh seed for next round
                    seed_info = get_seed_info()
                    if seed_info is None:
                        print("Failed to get new seed!")
                        return
                else:
                    if result['best_bits'] > best_in_round:
                        best_in_round = result['best_bits']
            
            total_attempts += round_attempts
            elapsed = time.time() - start_time
            rate = total_attempts / elapsed if elapsed > 0 else 0
            
            if round_num % 5 == 0:
                print(f"Round {round_num}: {total_attempts:,} attempts, {rate:.1f}/sec, Best: {best_in_round} bits")

if __name__ == "__main__":
    # Required for Windows multiprocessing
    multiprocessing.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print("\nMiner stopped.")
