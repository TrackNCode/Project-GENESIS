# Project GENESIS - Complete Containerized Image
# Runs identically on any Windows (via Docker Desktop / WSL2), Linux, or macOS host.

FROM python:3.11-slim

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for scientific libraries & 3D visualization
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install AutoDock Vina Linux 64-bit binary
RUN mkdir -p /app/backend/bin && \
    wget -q https://github.com/ccsb-scripps/AutoDock-Vina/releases/download/v1.2.5/vina_1.2.5_linux_x86_64 -O /app/backend/bin/vina && \
    chmod +x /app/backend/bin/vina

# Install Python scientific dependencies
COPY requirements_full.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_full.txt

# Copy application source code, pre-built frontend distribution, and data
COPY backend /app/backend
COPY frontend/dist /app/frontend/dist
COPY genesis_dev.db /app/genesis_dev.db
COPY vector_store.json /app/vector_store.json

# Expose standard web port
EXPOSE 8000

# Start unified FastAPI backend serving both API and complete React UI
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
