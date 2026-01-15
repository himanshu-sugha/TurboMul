# TurboMul - Production-Ready Amadeus PoW Miner
**Amadeus Genesis Hard Hack - Sub-Track A: RISCV Computer Prototype**

## What Makes This Different

Unlike generic MatMul benchmarks, **TurboMul actually connects to the Amadeus testnet API and produces verified solutions**:

```
API Response: {'valid': True, 'valid_math': True}
```

## Key Results

| Metric | Value | Proof |
|--------|-------|-------|
| MatMul Speed | **2043 sols/sec** | ![Benchmark](benchmark_result.png) |
| PoW Miner | **227 sols/sec** | Valid solutions submitted |
| Validation | `valid: True, valid_math: True` | ![Proof](validation_proof.png) |
| Platform | N300s RISC-V (Koyeb) | TensTorrent hardware |

## Critical Discovery

By analyzing the Amadeus source code (`amadeus-utils/src/blake3.rs`), I discovered:

| Matrix | Type | Critical Insight |
|--------|------|------------------|
| A | `uint8` | Standard unsigned |
| B | **`int8` (SIGNED)** | **-128 to 127, NOT 0-255!** |
| C | `int32` | Little-endian output |

This insight enabled correct solution computation that passes `valid_math: True`.

## Production PoW Miner

Full mining implementation with:
1. **Blake3 XOF** for matrix derivation
2. **Float32 optimization** (35x speedup)
3. **Difficulty 20 bits** (20 leading zeros)
4. **API validation** endpoint integration

```bash
# Run the miner
pip install numpy requests blake3
python miner.py
```

## Solution Format (1264 bytes)

| Component | Bytes | Description |
|-----------|-------|-------------|
| epoch | 4 | Little-endian uint32 |
| segment_vr_hash | 32 | Current chain VR |
| pk | 48 | Validator public key |
| pop | 96 | Proof of possession |
| computor | 48 | Same as pk |
| nonce | 12 | Mining nonce |
| **tensor_c** | 1024 | MatMul result (int32 LE) |

## Files

| File | Purpose |
|------|---------|
| `miner.py` | Full PoW miner (production) |
| `solver_optimized.py` | MatMul benchmark (2043/sec) |
| `ultra_miner.py` | Hash-speed test (230k H/s) |

## Technical Approach

### Mining Algorithm
```python
while True:
    nonce = random_bytes(12)
    preamble = build_preamble(epoch, vr_hash, pk, pop, nonce)
    A, B = blake3_xof(preamble)  # Derive matrices
    C = matmul(A.float32(), B.float32()).int32()
    solution = preamble + C.tobytes()
    if leading_zeros(blake3(solution)) >= 20:
        submit(solution)  # valid: True!
```

### Optimization Journey
| Version | Speed | Method |
|---------|-------|--------|
| Naive int64 | 58/sec | Standard int64 |
| Float32 | **2043/sec** | BLAS-accelerated |
| PoW Miner | 227/sec | Full mining loop |

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `/api/chain/stats` | Get difficulty (diff_bits: 20) |
| `/api/upow/seed_with_matrix_a_b` | Fetch workload |
| `/api/upow/validate` | Verify solutions |

---

**Author:** Amadeus Genesis Hard Hack 2025

**Repository:** https://github.com/himanshu-sugha/TurboMul