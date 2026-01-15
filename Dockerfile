# TurboMul PoW Miner - Koyeb N300s Deployment
FROM ghcr.io/tenstorrent/tt-xla/tt-xla-ird-ubuntu-22-04:latest

# Install Python dependencies
RUN pip3 install --no-cache-dir numpy requests blake3

# Create working directory
RUN mkdir -p /app
WORKDIR /app

# Copy all Python files
COPY *.py /app/
COPY requirements.txt /app/
COPY README.md /app/

# Verify files exist
RUN ls -la /app/

# Run the PoW miner
ENTRYPOINT ["python3"]
CMD ["miner.py"]
