"""Memory detection and model auto-selection."""

import psutil
import torch
from typing import Tuple


def get_system_memory() -> float:
    """Get available system memory in GB."""
    memory = psutil.virtual_memory()
    return memory.available / (1024 ** 3)


def get_worker_count() -> int:
    """Get optimal worker count, reserving 1 core for system."""
    total_cores = psutil.cpu_count(logical=False) or 1
    available_cores = max(1, total_cores - 1)
    return min(available_cores, int(available_cores * 0.75))


def select_best_model(available_ram_gb: float) -> str:
    """Select the best Whisper model based on available RAM."""
    # Reserve 20% for system operations
    usable_ram = available_ram_gb * 0.8
    
    if usable_ram >= 8:
        return "large-v3"
    elif usable_ram >= 5:
        return "medium"
    elif usable_ram >= 3:
        return "small"
    elif usable_ram >= 2:
        return "base"
    else:
        return "tiny"


def get_model_info(model_name: str) -> Tuple[str, float]:
    """Get model description and estimated RAM usage."""
    models = {
        "tiny": ("Fastest, lowest quality", 1.0),
        "base": ("Good balance of speed/quality", 1.5),
        "small": ("Better quality, slower", 2.0),
        "medium": ("High quality, moderate speed", 4.0),
        "large-v3": ("Best quality, slowest", 6.0),
    }
    return models.get(model_name, ("Unknown model", 1.0))


def setup_cpu_optimization():
    """Configure PyTorch for optimal CPU usage."""
    worker_count = get_worker_count()
    torch.set_num_threads(worker_count)
    
    # Disable GPU usage completely
    import os
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    
    return worker_count