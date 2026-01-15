#!/usr/bin/env python3
"""
TurboMul Final Miner
Amadeus Genesis Hard Hack - Production Version

Best working approach:
- Derive matrices locally for each nonce
- Compute MatMul per attempt
- ~227 solutions/sec with valid results
"""

import numpy as np
import requests
import time
import warnings
import struct
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import threading

try:
    import blake3
except ImportError:
    print("ERROR: pip install blake3")
    sys.exit(1)

warnings.filterwarnings('ignore')

API_BASE = "https://testnet.ama.one"
TESTNET_RPC = "https://testnet-rpc.ama.one"

# Shared state
lock = threading.Lock()
found_solution = None
total_attempts = 0
best_bits = 0
start_time = None

def get_chain_stats():
    try:
        r = requests.get(f"{TESTNET_RPC}/api/chain/stats", verify=False, timeout=10)
        return r.json()
    except:
        return None

def get_seed_info():
    try:
        r = requests.get(f"{API_BASE}/api/upow/seed_with_matrix_a_b", verify=False, timeout=30)
        data = r.content
        preamble = data[:240]
        return {
            'epoch': struct.unpack('<I', preamble[0:4])[0],
            'segment_vr_hash': preamble[4:36],
            'pk': preamble[36:84],
            'pop': preamble[84:180],
            'computor': preamble[180:228]
        }
    except:
        return None

def build_preamble(seed_info, nonce):
    p = struct.pack('<I', seed_info['epoch'])
    p += seed_info['segment_vr_hash']
    p += seed_info['pk']
    p += seed_info['pop']
    p += seed_info['computor']
    p += nonce
    return p

def derive_and_compute(preamble):
    hasher = blake3.blake3(preamble)
    a_size = 16 * 50240
    b_size = 50240 * 16
    xof = hasher.digest(length=a_size + b_size)
    A = np.frombuffer(xof[:a_size], dtype=np.uint8).reshape(16, 50240).astype(np.float32)
    B = np.frombuffer(xof[a_size:], dtype=np.int8).reshape(50240, 16).astype(np.float32)
    C = np.matmul(A, B).astype(np.int32)
    return C.tobytes()

def count_leading_zeros(h):
    count = 0
    for byte in h:
        if byte == 0:
            count += 8
        else:
            for i in range(7, -1, -1):
                if byte & (1 << i):
                    return count
                count += 1
            return count
    return count

def mine_worker(seed_info, diff_bits, batch_size):
    global found_solution, total_attempts, best_bits
    
    for _ in range(batch_size):
        if found_solution:
            return
        
        nonce = os.urandom(12)
        preamble = build_preamble(seed_info, nonce)
        tensor_c = derive_and_compute(preamble)
        solution = preamble + tensor_c
        h = blake3.blake3(solution).digest()
        zeros = count_leading_zeros(h)
        
        with lock:
            total_attempts += 1
            if zeros > best_bits:
                best_bits = zeros
                elapsed = time.time() - start_time
                rate = total_attempts / elapsed if elapsed > 0 else 0
                print(f"  Best: {zeros} bits | {total_attempts:,} attempts | {rate:.0f}/sec")
            
            if zeros >= diff_bits:
                found_solution = solution
                print(f"\n[FOUND] {zeros} bits at attempt {total_attempts:,}")
                return

def validate(solution):
    try:
        r = requests.post(f"{API_BASE}/api/upow/validate", data=solution, verify=False, timeout=30)
        return r.json()
    except:
        return None

def main():
    global found_solution, total_attempts, best_bits, start_time
    
    print("=" * 50)
    print("TurboMul Final Miner")
    print("=" * 50)
    
    stats = get_chain_stats()
    diff_bits = stats['stats'].get('diff_bits', 20) if stats else 20
    print(f"Difficulty: {diff_bits} bits\n")
    
    num_workers = 4
    batch_per_worker = 50
    
    while True:
        seed_info = get_seed_info()
        if not seed_info:
            time.sleep(5)
            continue
        
        print(f"Epoch: {seed_info['epoch']} - Mining...")
        
        found_solution = None
        total_attempts = 0
        best_bits = 0
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            while not found_solution:
                futures = [
                    executor.submit(mine_worker, seed_info, diff_bits, batch_per_worker)
                    for _ in range(num_workers)
                ]
                for f in futures:
                    f.result()
        
        if found_solution:
            result = validate(found_solution)
            print(f"Validation: {result}")
            if result and result.get('valid') and result.get('valid_math'):
                print("[OK] VALID SOLUTION!\n")
            else:
                print("[RETRY] Getting new workload...\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
