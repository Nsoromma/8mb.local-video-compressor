import os


def get_gpu_env() -> dict:
    """
    Construct an environment with NVIDIA GPU variables and CUDA/NVIDIA library/bin paths
    for subprocess calls (ffmpeg, nvidia-smi, ffprobe, etc.).

    - Preserves existing variables and appends required paths
    - Covers CUDA inside containers and WSL2 libcuda path
    """
    env = os.environ.copy()

    # Ensure NVIDIA visibility/capabilities (non-destructive defaults)
    env["NVIDIA_VISIBLE_DEVICES"] = env.get("NVIDIA_VISIBLE_DEVICES", "all")
    env["NVIDIA_DRIVER_CAPABILITIES"] = env.get("NVIDIA_DRIVER_CAPABILITIES", "compute,video,utility")

    # CUDA locations
    cuda_home = env.get("CUDA_HOME", "/usr/local/cuda")
    env["CUDA_HOME"] = cuda_home

    # LD_LIBRARY_PATH additions (don't clobber existing)
    lib_paths = [
        "/usr/local/nvidia/lib64",
        "/usr/local/nvidia/lib",
        f"{cuda_home}/lib64",
        f"{cuda_home}/lib",
        "/usr/local/cuda/targets/x86_64-linux/lib",
        "/usr/lib/wsl/lib",  # WSL2 libcuda.so location
        "/usr/lib/x86_64-linux-gnu",
    ]
    existing = env.get("LD_LIBRARY_PATH", "")
    add = ":".join(p for p in lib_paths if p)
    env["LD_LIBRARY_PATH"] = (existing + (":" if existing and add else "") + add) if (existing or add) else ""

    # PATH additions for CUDA/NVIDIA tools
    bin_paths = [
        f"{cuda_home}/bin",
        "/usr/local/nvidia/bin",
    ]
    existing_path = env.get("PATH", "")
    add_path = ":".join(p for p in bin_paths if p)
    env["PATH"] = (existing_path + (":" if existing_path and add_path else "") + add_path) if (existing_path or add_path) else ""

    return env
