# RISC-V MatMul Solver
**Amadeus Genesis Hard Hack Submission**

## 🏆 Results

| Metric | Value |
|--------|-------|
| **valid_math** | ✅ True (100%) |
| **Compute Time** | 0.489ms |
| **Solutions/sec** | **2043** |
| **Platform** | N300s RISC-V (TensTorrent) |

---

## Key Discovery

From Rust source (`amadeus-utils/src/blake3.rs`):

| Matrix | Type | Shape |
|--------|------|-------|
| A | `uint8` | 16 × 50240 |
| B | `int8` (SIGNED!) | 50240 × 16 |
| C | `int32` | 16 × 16 |

**Critical insight**: Matrix B uses **signed int8** (-128 to 127)!

---

## Optimization: Float32

Using `float32` instead of `int64` gives **35x speedup**:
- int64: 58 sols/sec
- float32: **2043 sols/sec**

---

## Quick Start

### Python Solver (Fastest)
```bash
pip install numpy requests
python solver_optimized.py
python solver_optimized.py --benchmark
```

### C++ Build
```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j4
```

---

## Benchmark Metadata

| Item | Value |
|------|-------|
| **Hardware** | Koyeb N300s (TensTorrent RISC-V) |
| **Instance** | 4 vCPU, 32GB RAM |
| **Python** | 3.11 |
| **NumPy** | 2.2.6 |
| **Docker Image** | `ghcr.io/tenstorrent/tt-xla/tt-xla-ird-ubuntu-22-04:latest` |
| **Optimization** | float32 matmul, NumPy BLAS |

---

## Files

| File | Description |
|------|-------------|
| `solver_optimized.py` | 🏆 Winning solver (2043/sec) |
| `solver.py` | Original int64 solver |
| `matmul_optimized.cpp` | C++ tiled implementation |
| `Dockerfile` | RISC-V cross-compile |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upow/seed_with_matrix_a_b` | GET | Fetch workload |
| `/api/upow/validate` | POST | Submit solution |

---

## Compiler Flags (C++)

```
-O3 -march=rv64gcv -mabi=lp64d
```

---

## Author

Amadeus Genesis Hard Hack 2025
