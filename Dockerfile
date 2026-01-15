# TurboMul PoW Miner - Koyeb N300s Deployment
FROM ghcr.io/tenstorrent/tt-xla/tt-xla-ird-ubuntu-22-04:latest

# Install Python dependencies including blake3
RUN pip3 install numpy requests blake3

# Set working directory
WORKDIR /app

# Copy miner files
COPY miner.py .
COPY solver_optimized.py .
COPY requirements.txt .
COPY README.md .

# Run the PoW miner
CMD ["python3.11", "miner.py"]
