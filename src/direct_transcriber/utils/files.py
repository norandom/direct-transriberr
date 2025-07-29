"""File utility functions."""

from pathlib import Path
from typing import List

from ..media.formats import ALL_EXTENSIONS


def get_media_files(directory: Path) -> List[Path]:
    """
    Get all audio and video files from directory.
    
    Args:
        directory: Directory to search
        
    Returns:
        List of media file paths
    """
    files = []
    for ext in ALL_EXTENSIONS:
        files.extend(directory.glob(f"**/*{ext}"))
        files.extend(directory.glob(f"**/*{ext.upper()}"))
    
    return sorted(files)