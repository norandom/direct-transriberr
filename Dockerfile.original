FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install the application with CPU-only PyTorch
RUN uv pip install --system \
    --index-url https://download.pytorch.org/whl/cpu \
    torch torchaudio \
    && uv pip install --system -e . \
    && rm -rf ~/.cache/uv

# Create directories for input/output/models
RUN mkdir -p /input /output /models

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=""
ENV TORCH_CUDA_VERSION=None
ENV WHISPER_MODEL_DIR=/models

# Default command
CMD ["direct-transcriber", "--help"]