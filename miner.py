#!/usr/bin/env python3
"""
TurboMul Full PoW Miner v2
Amadeus Genesis Hard Hack

Fixed: Now derives A,B locally using Blake3 XOF for each nonce,
so the solution is valid when submitted.
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
    """Get current chain stats including difficulty."""
    try:
        r = requests.get(f"{TESTNET_RPC}/api/chain/stats", verify=False, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Error getting chain stats: {e}")
        return None

def get_seed_info():
    """Get seed components from API."""
    try:
        r = requests.get(f"{API_BASE}/api/upow/seed_with_matrix_a_b", verify=False, timeout=30)
        data = r.content
        
        # Extract preamble components
        preamble = data[:240]
        epoch = struct.unpack('<I', preamble[0:4])[0]
        segment_vr_hash = preamble[4:36]
        pk = preamble[36:84]
        pop = preamble[84:180]
        computor = preamble[180:228]
        original_nonce = preamble[228:240]
        
        return {
            'epoch': epoch,
            'segment_vr_hash': segment_vr_hash,
            'pk': pk,
            'pop': pop,
            'computor': computor,
            'original_nonce': original_nonce
        }
    except Exception as e:
        print(f"Error getting seed info: {e}")
        return None

def derive_matrices_from_preamble(preamble):
    """Derive matrices A, B from preamble using Blake3 XOF."""
    hasher = blake3.blake3(preamble)
    
    # Generate A (16 x 50240 uint8) + B (50240 x 16 int8)
    a_size = 16 * 50240
    b_size = 50240 * 16
    total_size = a_size + b_size
    
    # Use Blake3 XOF to generate bytes
    xof_output = hasher.digest(length=total_size)
    
    # Parse matrices
    A = np.frombuffer(xof_output[:a_size], dtype=np.uint8).reshape(16, 50240)
    B = np.frombuffer(xof_output[a_size:], dtype=np.int8).reshape(50240, 16)
    
    return A, B

def build_preamble(epoch, segment_vr_hash, pk, pop, computor, nonce):
    """Build 240-byte preamble."""
    preamble = struct.pack('<I', epoch)  # 4 bytes
    preamble += segment_vr_hash           # 32 bytes
    preamble += pk                         # 48 bytes
    preamble += pop                        # 96 bytes
    preamble += computor                   # 48 bytes
    preamble += nonce                      # 12 bytes
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
        print(f"Validation error: {e}")
        return None

def submit_solution(solution):
    """Submit valid solution to testnet chain for scoring."""
    try:
        # Submit to chain using submit_and_wait endpoint
        r = requests.post(
            f"{TESTNET_RPC}/api/tx/submit_and_wait",
            data=solution,
            verify=False,
            timeout=60
        )
        return r.json()
    except Exception as e:
        print(f"Submission error: {e}")
        return None

def check_score():
    """Check current epoch score."""
    try:
        r = requests.get(f"{TESTNET_RPC}/api/epoch/score", verify=False, timeout=10)
        return r.json()
    except:
        return None

def mine_with_local_derivation(seed_info, diff_bits, max_attempts=1000):
    """Mine by deriving matrices locally for each nonce."""
    epoch = seed_info['epoch']
    segment_vr_hash = seed_info['segment_vr_hash']
    pk = seed_info['pk']
    pop = seed_info['pop']
    computor = seed_info['computor']
    
    start_time = time.time()
    best_bits = 0
    
    for attempt in range(max_attempts):
        # Generate new nonce
        nonce = os.urandom(12)
        
        # Build preamble
        preamble = build_preamble(epoch, segment_vr_hash, pk, pop, computor, nonce)
        
        # Derive matrices from preamble
        A, B = derive_matrices_from_preamble(preamble)
        
        # Compute MatMul
        C = compute_matmul(A, B)
        tensor_c_bytes = C.tobytes()
        
        # Build solution
        solution = preamble + tensor_c_bytes
        
        # Hash and check difficulty
        hash_bytes = blake3.blake3(solution).digest()
        zeros = count_leading_zero_bits(hash_bytes)
        
        if zeros > best_bits:
            best_bits = zeros
            print(f"New best: {zeros} bits at attempt {attempt}")
        
        if zeros >= diff_bits:
            elapsed = time.time() - start_time
            rate = attempt / elapsed if elapsed > 0 else 0
            print(f"\n*** FOUND VALID SOLUTION! ***")
            print(f"Attempt: {attempt}")
            print(f"Leading zeros: {zeros} bits")
            print(f"Rate: {rate:.1f} solutions/sec")
            return solution, attempt, zeros
        
        # Progress
        if attempt > 0 and attempt % 100 == 0:
            elapsed = time.time() - start_time
            rate = attempt / elapsed if elapsed > 0 else 0
            print(f"Attempts: {attempt}, Rate: {rate:.1f}/sec, Best: {best_bits} bits")
    
    return None, max_attempts, best_bits

def main():
    print("=" * 60)
    print("TurboMul Full PoW Miner v2")
    print("(With local matrix derivation)")
    print("=" * 60)
    print()
    
    # Get chain stats
    print("[1] Fetching chain stats...")
    stats = get_chain_stats()
    if stats and 'stats' in stats:
        diff_bits = stats['stats'].get('diff_bits', 20)
        height = stats['stats'].get('height', 0)
        print(f"    Height: {height}")
        print(f"    Difficulty: {diff_bits} bits")
    else:
        diff_bits = 20
        print(f"    Using default difficulty: {diff_bits} bits")
    print()
    
    # Get seed info
    print("[2] Fetching seed info from API...")
    seed_info = get_seed_info()
    if seed_info is None:
        print("    Failed to get seed info!")
        return
    print(f"    Epoch: {seed_info['epoch']}")
    print(f"    PK length: {len(seed_info['pk'])} bytes")
    print()
    
    # Mining loop
    solutions_found = 0
    
    while True:
        print(f"[3] Mining (target: {diff_bits} leading zero bits)...")
        print("    (Each attempt: derive matrices + compute MatMul + check hash)")
        print()
        
        solution, attempts, zeros = mine_with_local_derivation(
            seed_info, diff_bits, 
            max_attempts=100000
        )
        
        if solution:
            solutions_found += 1
            print(f"\n[4] Validating solution...")
            result = validate_solution(solution)
            if result:
                print(f"    API Response: {result}")
                if result.get('valid') and result.get('valid_math'):
                    print("    [OK] VALID SOLUTION!")
                    
                    # SUBMIT TO CHAIN FOR SCORING
                    print("\n[5] Submitting to testnet chain...")
                    submit_result = submit_solution(solution)
                    if submit_result:
                        print(f"    Submit Response: {submit_result}")
                        if submit_result.get('error') == 'ok':
                            print("    [SUCCESS] Solution submitted to chain!")
                        else:
                            print(f"    [INFO] Submit result: {submit_result}")
                    else:
                        print("    [WARN] Submission failed, continuing...")
                    
                    # Check current score
                    print("\n[6] Checking epoch score...")
                    score = check_score()
                    if score:
                        print(f"    Score: {score}")
                        
                elif result.get('valid_math'):
                    print("    [OK] Math valid, but difficulty check failed")
                    print("    (Solution may have become stale - new epoch)")
                else:
                    print("    [FAIL] Math check failed - investigating...")
            
            # Get fresh seed info for next round
            print("\n[7] Getting fresh seed info for next round...")
            seed_info = get_seed_info()
            if seed_info is None:
                print("    Failed to get seed info!")
                return
            print()
        else:
            print(f"    No solution found in batch, continuing...")
            print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMiner stopped by user.")
