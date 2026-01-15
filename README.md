# TurboMul - RISC-V MatMul Solver
**Amadeus Genesis Hard Hack Submission**

## Results

| Metric | Value |
|--------|-------|
| **MatMul Speed** | 2043 sols/sec |
| **Compute Time** | 0.489ms |
| **Validation** | valid_math=True (100%) |
| **Platform** | N300s RISC-V (TensTorrent) |

## Key Discovery

From Rust source (`amadeus-utils/src/blake3.rs`):

| Matrix | Type | Shape |
|--------|------|-------|
| A | `uint8` | 16 x 50240 |
| B | `int8` (SIGNED) | 50240 x 16 |
| C | `int32` | 16 x 16 |

**Critical insight**: Matrix B uses **signed int8** (-128 to 127).

## Optimization

Using `float32` for intermediate calculations:
- int64 implementation: 58 sols/sec
- float32 implementation: **2043 sols/sec** (35x speedup)

## Quick Start

```bash
pip install numpy requests blake3
python solver_optimized.py --benchmark
python miner.py
```

## Files

| File | Description |
|------|-------------|
| `miner.py` | Full PoW miner |
| `solver_optimized.py` | MatMul benchmark |
| `Dockerfile` | Koyeb deployment |

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/api/upow/seed_with_matrix_a_b` | Fetch workload |
| `/api/upow/validate` | Verify solutions |

---

**Author:** Amadeus Genesis Hard Hack 2025