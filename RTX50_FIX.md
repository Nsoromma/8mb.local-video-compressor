# RTX 50-Series NVENC Fix for Docker on WSL2

## Problem
RTX 50-series GPUs (e.g., RTX 5070 Ti) use **CUDA 13.0** with new **DXG (DirectX Graphics)** libraries that nvidia-container-toolkit doesn't automatically mount. This causes `cuInit(0)` to fail with error 500 (CUDA_ERROR_NOT_FOUND).

## Root Cause
1. **CUDA 13.0** (Blackwell architecture) requires additional WSL2-specific libraries:
   - `libnvdxgdmal.so.1` (NVIDIA DXG DirectML)
   - `libnvdxdlkernels.so` (DXG kernel libraries)
   - `libnvwgf2umx.so` (Windows Graphics Foundation)
   - `libnvidia-encode.so.1` (NVENC encoder)
   - `libnvcuvid.so.1` (NVDEC decoder)
   - Plus 8 other DXG-related libraries

2. **nvidia-container-toolkit** only mounts 5 libraries:
   - libcuda.so.1.1
   - libcuda_loader.so
   - libnvidia-ml.so.1
   - libnvidia-ml_loader.so
   - libnvidia-ptxjitcompiler.so.1

3. **Stub library conflict**: The nvidia/cuda base image includes a 172KB stub `libcuda.so.1` that takes precedence over the real 26MB WSL2 driver.

## Solution
Two changes were required:

### 1. Mount Full WSL Driver Directory
Add this volume mount to `docker-compose.yml`:
```yaml
volumes:
  - /usr/lib/wsl/drivers:/usr/lib/wsl/drivers:ro
```

This makes ALL WSL driver libraries available, including the missing DXG libraries.

### 2. Use LD_PRELOAD to Override Stub
In `entrypoint.sh`, force loading the real WSL driver:
```bash
export LD_PRELOAD="$WSL_DRV_DIR/libcuda.so.1.1:${LD_PRELOAD:-}"
```

This ensures the real 26MB WSL2 CUDA driver is loaded instead of the 172KB stub.

## Verification
All NVENC encoders now work:
- ✅ H.264 NVENC (h264_nvenc)
- ✅ HEVC NVENC (hevc_nvenc)
- ✅ AV1 NVENC (av1_nvenc)

Test command:
```bash
docker run --rm --gpus all -v /usr/lib/wsl/drivers:/usr/lib/wsl/drivers:ro \\
  8mblocal:latest ffmpeg -f lavfi -i nullsrc=s=1920x1080:d=1 \\
  -c:v h264_nvenc -f null -
```

## Technical Details
- **Hardware**: RTX 5070 Ti Laptop GPU (Blackwell architecture)
- **Driver**: 581.80
- **CUDA Version**: 13.0
- **OS**: Windows 11 with WSL2
- **Container Base**: nvidia/cuda:12.8.0-runtime-ubuntu22.04
- **FFmpeg**: 8.0 with NVENC support

## Files Modified
1. `docker-compose.yml` - Added WSL drivers volume mount
2. `entrypoint.sh` - Added LD_PRELOAD logic to override stub
3. `Dockerfile` - Removed unnecessary cuda-fix.sh wrapper

## Why This Works
WSL2's CUDA 13.0 implementation uses Microsoft's DXG (DirectX Graphics) subsystem instead of traditional CUDA device nodes (`/dev/nvidia*`). The DXG libraries dynamically load at runtime when `cuInit()` is called. Without these libraries mounted, cuInit fails with error 500, even though the base libcuda.so.1.1 is present.

By mounting the full `/usr/lib/wsl/drivers` directory and using LD_PRELOAD to force loading the real driver, we provide everything CUDA 13.0 needs to initialize successfully on RTX 50-series GPUs.

## November 6, 2025
Fixed after extensive debugging that identified:
1. nvidia-container-toolkit incomplete library mounting
2. Stub libcuda.so.1 blocking real driver
3. Missing DXG libraries causing cuInit failures

The fix enables **full NVENC/NVDEC support** for RTX 50-series GPUs in Docker containers on Windows WSL2.
