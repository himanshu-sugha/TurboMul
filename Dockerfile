# Base image - TensTorrent RISC-V compatible
FROM ghcr.io/tenstorrent/tt-xla/tt-xla-ird-ubuntu-22-04:latest

# Install Python dependencies
RUN pip3 install numpy requests

# Set working directory
WORKDIR /app

# Copy project files
COPY solver_optimized.py .
COPY solver.py .
COPY README.md .
COPY matmul_optimized.cpp .
COPY matmul_naive.cpp .
COPY matmul.h .
COPY main.cpp .
COPY CMakeLists.txt .

# Run benchmark on start
CMD ["python3.11", "solver_optimized.py", "--benchmark"]
