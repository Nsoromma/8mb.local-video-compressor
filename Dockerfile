# Multi-stage unified 8mb.local container
# Stage 1: Build FFmpeg with multi-vendor GPU support (NVIDIA NVENC, Intel QSV, AMD AMF/VAAPI)
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04 AS ffmpeg-build

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    build-essential yasm cmake pkg-config git wget \
    libnuma-dev libx264-dev libx265-dev libvpx-dev libopus-dev \
    libva-dev libdrm-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# NVIDIA NVENC headers
RUN git clone https://git.videolan.org/git/ffmpeg/nv-codec-headers.git && \
    cd nv-codec-headers && make install && cd ..

# Build FFmpeg with all hardware acceleration support
RUN wget https://ffmpeg.org/releases/ffmpeg-7.0.tar.xz && \
    tar xf ffmpeg-7.0.tar.xz && cd ffmpeg-7.0 && \
    ./configure \
      --enable-nonfree --enable-gpl \
      --enable-cuda-nvcc --enable-libnpp --enable-nvenc \
      --enable-vaapi \
      --enable-libx264 --enable-libx265 --enable-libvpx --enable-libopus \
      --extra-cflags=-I/usr/local/cuda/include \
      --extra-ldflags=-L/usr/local/cuda/lib64 && \
    make -j$(nproc) && make install && ldconfig

# Stage 2: Build Frontend
FROM node:20-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ ./
# Build with empty backend URL (same-origin deployment)
ENV PUBLIC_BACKEND_URL=""
RUN npm run build

# Stage 3: Runtime with all services
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3.10 python3-pip supervisor redis-server \
    libopus0 libx264-163 libx265-199 libvpx7 libnuma1 \
    libva2 libva-drm2 \
    && rm -rf /var/lib/apt/lists/*

# Copy FFmpeg from build stage
COPY --from=ffmpeg-build /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg-build /usr/local/bin/ffprobe /usr/local/bin/ffprobe
COPY --from=ffmpeg-build /usr/local/lib /usr/local/lib
RUN ldconfig

WORKDIR /app

# Install Python dependencies (backend + worker combined)
COPY backend-api/requirements.txt /app/backend-requirements.txt
COPY worker/requirements.txt /app/worker-requirements.txt
RUN pip3 install --no-cache-dir -r /app/backend-requirements.txt -r /app/worker-requirements.txt

# Copy application code
COPY backend-api/app /app/backend
COPY worker/app /app/worker

# Copy pre-built frontend
COPY --from=frontend-build /frontend/build /app/frontend-build

# Create necessary directories
RUN mkdir -p /app/uploads /app/outputs /var/log/supervisor /var/lib/redis /var/log/redis

# Configure supervisord
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8000

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
