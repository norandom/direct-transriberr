"""Supported media formats."""

# Audio formats
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma', '.aac'}

# Video formats
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}

# All supported extensions
ALL_EXTENSIONS = AUDIO_EXTENSIONS | VIDEO_EXTENSIONS

def is_video_file(file_path) -> bool:
    """Check if file is a video format."""
    return file_path.suffix.lower() in VIDEO_EXTENSIONS

def is_audio_file(file_path) -> bool:
    """Check if file is an audio format."""
    return file_path.suffix.lower() in AUDIO_EXTENSIONS

def is_media_file(file_path) -> bool:
    """Check if file is a supported media format."""
    return file_path.suffix.lower() in ALL_EXTENSIONS