# 8mb.local – Self‑Hosted GPU Video Compressor

8mb.local is a self‑hosted, fire‑and‑forget video compressor. Drop a file, choose a target size (e.g., 8MB, 25MB, 50MB, 100MB), and let NVIDIA NVENC produce compact outputs with AV1/HEVC/H.264. The stack includes a SvelteKit UI, FastAPI backend, Celery worker, Redis broker, and real‑time progress via Server‑Sent Events (SSE).
## Screenshots

![8mb.local – initial screen](docs/images/ui-empty.png)

![8mb.local – analyze, advanced options, progress, download](docs/images/ui-job-complete.png)
## Features
- Drag‑and‑drop UI with helpful presets and advanced options (codec, container, tune, audio bitrate)
- ffprobe analysis on upload for instant estimates and warnings
- Real‑time progress and FFmpeg logs via SSE
## Architecture (technical deep dive)

```mermaid
flowchart LR
   A[Browser / SvelteKit UI] -- Upload / SSE --> B(FastAPI Backend)
   B -- Enqueue --> C[Redis]
   D[Celery Worker + FFmpeg NVENC] -- Progress / Logs --> C
   B -- Pub/Sub relay --> A
## Configuration (env)
- `AUTH_ENABLED` (true|false)
- `AUTH_USER`, `AUTH_PASS`
- `FILE_RETENTION_HOURS` (default 1)
- `REDIS_URL` (defaults to the compose redis service)
- `PUBLIC_BACKEND_URL` for the frontend (defaults to `http://localhost:8000`)
 
Example `.env` (copy from `.env.example`):

```
AUTH_ENABLED=false
Components
AUTH_PASS=changeme
## Using the app
1. Drag & drop a video or Choose File.
2. Pick a target size or enter a custom MB value, click Analyze (auto‑analyzes on drop).
3. Optional: open Advanced Options.
   - Video Codec: AV1 (best quality on newer RTX), HEVC (H.265), or H.264 (compatibility).
   - Audio Codec: Opus (default) or AAC. MP4 will auto‑fallback to AAC when Opus is chosen.
   - Speed/Quality: NVENC P1 (fast) … P7 (best). Default P6.
   - Container: MP4 (most compatible) or MKV (best with Opus).
   - Tune: Best Quality (HQ), Low Latency, Ultra‑Low Latency, or Lossless.
4. Click Compress and watch progress/logs. Download when done.

Codec/container notes
Data & files
- MP4 outputs include `+faststart` for better web playback.
- H.264/HEVC outputs are set to a compatible pixel format (yuv420p) and profiles.

Performance tips
- For very small targets, prefer AV1/HEVC and keep audio around 96–128 kbps.
- If speed matters, try Low/Ultra‑Low latency tunes with a faster preset (P1–P4). For best quality, use HQ with P6/P7.

## GPU support tips
- Windows: Docker Desktop + WSL2 with GPU enabled; install NVIDIA drivers and the NVIDIA Container Toolkit inside WSL2.
- Linux: install NVIDIA drivers and the NVIDIA Container Toolkit.
- Verify encoders inside the worker:

```bash
docker exec 8mblocal-worker bash -lc "ffmpeg -hide_banner -encoders | grep -i nvenc"
```

## Installation
Run with prebuilt images (recommended) or build locally.

### Quick Start (Docker Hub images)
If you just want to run the stack without building images locally:

```bash
docker compose -f docker-compose.hub.yml up -d
```

Frontend: http://localhost:5173  •  Backend: http://localhost:8000

Requires NVIDIA GPU runtime for the worker (Compose uses `gpus: all`).

### Build locally
1. Copy `.env.example` to `.env` and adjust values.
2. Ensure folders: `uploads/`, `outputs/` (mounted into containers).
3. Start services (first run: worker compiles FFmpeg, takes longer):

```bash
docker compose up --build -d
```

### Update to latest images

```bash
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
```

### Troubleshooting
- NVENC not listed: confirm NVIDIA drivers and Container Toolkit are installed; try restarting Docker.
- Permission denied writing uploads/outputs: ensure your OS user owns the repo folders or adjust volume permissions.
- Ports in use: change `5173`/`8000` mappings in compose.
- No progress events: ensure the frontend can reach `http://localhost:8000` directly (SSE shouldn’t be buffered by a proxy).

## Maintainers
- Images are built and published from CI on pushes to `main`. See `docs/DOCKER_HUB.md` for maintainer‑focused publishing steps.

## Notes
- AV1 (av1_nvenc) requires recent RTX GPUs and up‑to‑date drivers.
- MP4 + Opus is not supported; the worker auto‑encodes AAC in MP4.
- Consider HTTPS termination and stronger auth for public deployments.
