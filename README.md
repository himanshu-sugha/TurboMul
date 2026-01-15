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

---

## Core Implementation

### Matrix Derivation (`miner.py:66-82`)
```python
def derive_matrices_from_preamble(preamble):
    """Derive matrices A, B from preamble using Blake3 XOF."""
    hasher = blake3.blake3(preamble)
    a_size = 16 * 50240
    b_size = 50240 * 16
    xof_output = hasher.digest(length=a_size + b_size)
    
    A = np.frombuffer(xof_output[:a_size], dtype=np.uint8).reshape(16, 50240)
    B = np.frombuffer(xof_output[a_size:], dtype=np.int8).reshape(50240, 16)
    return A, B
```

### Float32 MatMul Optimization (`miner.py:94-99`)
```python
def compute_matmul(A, B):
    """Compute C = A @ B using float32 optimization."""
    A_f = A.astype(np.float32)
    B_f = B.astype(np.float32)
    C = np.matmul(A_f, B_f).astype(np.int32)
    return C
```

### API Validation (`miner.py:115-127`)
```python
def validate_solution(solution):
    """Validate solution with API."""
    r = requests.post(
        f"{API_BASE}/api/upow/validate",
        data=solution,
        verify=False
    )
    return r.json()  # {'valid': True, 'valid_math': True}
```

---

## Files

| File | Description | Key Functions |
|------|-------------|---------------|
| `miner.py` | Full PoW miner | `derive_matrices_from_preamble()`, `compute_matmul()` |
| `solver_optimized.py` | MatMul benchmark | Float32 optimization loop |
| `Dockerfile` | Koyeb deployment | N300s TensTorrent setup |

---

## Quick Start

```bash
pip install numpy requests blake3
python solver_optimized.py --benchmark  # Speed test
python miner.py                          # Full PoW miner
```

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/api/upow/seed_with_matrix_a_b` | Fetch workload (preamble + matrices) |
| `/api/upow/validate` | Verify solutions |
| `/api/chain/stats` | Get current difficulty |

---

**Author:** Amadeus Genesis Hard Hack 2025