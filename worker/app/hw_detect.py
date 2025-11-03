"""Hardware acceleration detection and codec mapping."""
import os
import subprocess
from typing import Dict, Optional


def detect_hw_accel() -> Dict[str, any]:
    """
    Detect available hardware acceleration.
    Returns dict with: type (nvidia/intel/amd/cpu), encoders available, etc.
    """
    result = {
        "type": "cpu",
        "available_encoders": {},
        "decode_method": None,
        "upload_method": None,
    }
    
    # Check for NVIDIA
    if _check_nvidia():
        result["type"] = "nvidia"
        result["decode_method"] = "cuda"
        result["available_encoders"] = {
            "h264": "h264_nvenc",
            "hevc": "hevc_nvenc",
            "av1": "av1_nvenc",
        }
        return result
    
    # Check for Intel QSV
    if _check_intel_qsv():
        result["type"] = "intel"
        result["decode_method"] = "qsv"
        result["available_encoders"] = {
            "h264": "h264_qsv",
            "hevc": "hevc_qsv",
            "av1": "av1_qsv",  # Available on Arc and newer
        }
        return result
    
    # Check for AMD AMF (Windows) or VAAPI (Linux)
    if _check_amd():
        result["type"] = "amd"
        if os.name == 'nt':
            result["decode_method"] = "d3d11va"
            result["available_encoders"] = {
                "h264": "h264_amf",
                "hevc": "hevc_amf",
                "av1": "av1_amf",
            }
        else:
            result["decode_method"] = "vaapi"
            result["available_encoders"] = {
                "h264": "h264_vaapi",
                "hevc": "hevc_vaapi",
                "av1": "av1_vaapi",
            }
        return result
    
    # CPU fallback
    result["available_encoders"] = {
        "h264": "libx264",
        "hevc": "libx265",
        "av1": "libsvtav1",  # or libaom-av1
    }
    
    return result


def _check_nvidia() -> bool:
    """Check if NVIDIA GPU is available."""
    try:
        # Check nvidia-smi
        result = subprocess.run(
            ["nvidia-smi"], 
            capture_output=True, 
            timeout=2
        )
        if result.returncode == 0:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check for CUDA device via ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-hwaccels"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if "cuda" in result.stdout.lower():
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return False


def _check_intel_qsv() -> bool:
    """Check if Intel QSV is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-hwaccels"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if "qsv" in result.stdout.lower():
            # Verify encoder is available
            encoders = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if "h264_qsv" in encoders.stdout:
                return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return False


def _check_amd() -> bool:
    """Check if AMD GPU acceleration is available."""
    try:
        # Check for AMF (Windows) or VAAPI (Linux)
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-hwaccels"],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if os.name == 'nt' and "d3d11va" in result.stdout.lower():
            # Check for AMF encoder
            encoders = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if "h264_amf" in encoders.stdout:
                return True
        elif "vaapi" in result.stdout.lower():
            # Check for VAAPI encoder
            encoders = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if "h264_vaapi" in encoders.stdout:
                return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return False


def map_codec_to_hw(requested_codec: str, hw_info: Dict) -> tuple[str, list]:
    """
    Map user-requested codec to appropriate hardware encoder.
    Returns: (encoder_name, extra_flags)
    """
    # Extract base codec name
    if "h264" in requested_codec:
        base = "h264"
    elif "hevc" in requested_codec or "h265" in requested_codec:
        base = "hevc"
    elif "av1" in requested_codec:
        base = "av1"
    else:
        base = "h264"  # default
    
    encoder = hw_info["available_encoders"].get(base, "libx264")
    flags = []
    
    # Add hardware-specific flags
    if encoder.endswith("_nvenc"):
        flags = ["-pix_fmt", "yuv420p"]
        if base == "h264":
            flags += ["-profile:v", "high"]
        elif base == "hevc":
            flags += ["-profile:v", "main"]
    elif encoder.endswith("_qsv"):
        flags = ["-pix_fmt", "nv12"]
        if base == "h264":
            flags += ["-profile:v", "high"]
    elif encoder.endswith("_amf"):
        flags = ["-pix_fmt", "yuv420p"]
    elif encoder.endswith("_vaapi"):
        flags = ["-pix_fmt", "nv12"]
    elif encoder == "libx264":
        flags = ["-pix_fmt", "yuv420p", "-profile:v", "high"]
    elif encoder == "libx265":
        flags = ["-pix_fmt", "yuv420p"]
    
    return encoder, flags


# Cache hardware detection on module load
_HW_INFO = None


def get_hw_info() -> Dict:
    """Get cached hardware info."""
    global _HW_INFO
    if _HW_INFO is None:
        _HW_INFO = detect_hw_accel()
    return _HW_INFO
