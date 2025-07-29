"""Audio extraction from media files."""

import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import ffmpeg
from rich.console import Console

from ..core.models import MediaInfo
from .formats import is_video_file

console = Console()


class MediaExtractor:
    """Extract audio from various media formats."""
    
    def __init__(self):
        self.temp_dir = None
    
    def extract_audio(self, input_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Extract audio from media file to WAV format.
        
        Args:
            input_path: Path to input media file
            output_path: Optional output path. If not provided, creates temp file.
            
        Returns:
            Path to extracted WAV file
        """
        if output_path is None:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                output_path = Path(temp_file.name)
        
        try:
            (
                ffmpeg
                .input(str(input_path))
                .output(str(output_path), acodec='pcm_s16le', ac=1, ar='16000')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return output_path
        except ffmpeg.Error as e:
            console.print(f"❌ FFmpeg error extracting audio: {e.stderr.decode() if e.stderr else 'Unknown error'}")
            raise
        except Exception as e:
            console.print(f"❌ Error extracting audio: {e}")
            raise
    
    def get_media_info(self, file_path: Path) -> MediaInfo:
        """
        Get information about a media file.
        
        Args:
            file_path: Path to media file
            
        Returns:
            MediaInfo object with file details
        """
        try:
            probe = ffmpeg.probe(str(file_path))
            
            # Extract basic info
            format_info = probe.get('format', {})
            duration = float(format_info.get('duration', 0))
            size_bytes = int(format_info.get('size', 0))
            format_name = format_info.get('format_name', '').split(',')[0]
            
            # Check streams for codecs
            audio_codec = None
            video_codec = None
            has_video = False
            
            for stream in probe.get('streams', []):
                if stream['codec_type'] == 'audio' and not audio_codec:
                    audio_codec = stream.get('codec_name')
                elif stream['codec_type'] == 'video':
                    has_video = True
                    if not video_codec:
                        video_codec = stream.get('codec_name')
            
            return MediaInfo(
                file_path=file_path,
                duration=duration,
                format=format_name,
                size_bytes=size_bytes,
                is_video=has_video or is_video_file(file_path),
                audio_codec=audio_codec,
                video_codec=video_codec
            )
            
        except ffmpeg.Error as e:
            console.print(f"❌ Error probing media file: {e}")
            raise
        except Exception as e:
            console.print(f"❌ Error getting media info: {e}")
            raise
    
    def estimate_duration(self, file_path: Path) -> float:
        """
        Estimate audio duration in seconds.
        
        Args:
            file_path: Path to media file
            
        Returns:
            Duration in seconds
        """
        try:
            probe = ffmpeg.probe(str(file_path))
            duration = float(probe['format']['duration'])
            return duration
        except:
            return 0.0