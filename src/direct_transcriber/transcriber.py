"""Audio transcription using local Whisper models."""

import os
import tempfile
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import whisper
import ffmpeg
from rich.console import Console
from rich.progress import Progress, TaskID

# Import new modules
from .core.whisper_transcriber import WhisperTranscriber
from .core.models import TranscriptionResult
from .media.extractor import MediaExtractor
from .media.formats import is_video_file
from .utils.files import get_media_files

console = Console()

# Suppress FP16 warnings for CPU processing
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


class LocalTranscriber:
    """Local CPU-only audio transcriber using Whisper.
    
    This class maintains backward compatibility while using new modular components internally.
    """
    
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model = None
        # Use new WhisperTranscriber internally
        self._transcriber = WhisperTranscriber(model_name)
        self._media_extractor = MediaExtractor()
        # Keep model reference for backward compatibility
        self.model = self._transcriber.model
    
    def _extract_audio(self, input_path: Path, output_path: Path) -> bool:
        """Extract audio using ffmpeg."""
        try:
            self._media_extractor.extract_audio(input_path, output_path)
            return True
        except Exception as e:
            console.print(f"❌ Error extracting audio: {e}")
            return False
    
    def transcribe_file(self, file_path: Path, progress: Progress, task_id: TaskID) -> Optional[Dict]:
        """Transcribe a single audio or video file."""
        try:
            # Check if it's a video file
            source_type = 'video' if is_video_file(file_path) else 'audio'
            
            if source_type == 'video':
                console.print(f"🎥 Extracting audio from video: {file_path.name}")
                progress.update(task_id, description=f"Extracting audio from {file_path.name}")
            else:
                console.print(f"🎵 Processing audio: {file_path.name}")
                progress.update(task_id, description=f"Processing {file_path.name}")
            
            # Handle different audio/video formats
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            try:
                # Extract audio to temporary WAV file
                if not self._extract_audio(file_path, temp_path):
                    return None
                
                progress.update(task_id, advance=30)
                
                # Use new transcriber
                transcription_result = self._transcriber.transcribe(temp_path, progress, task_id)
                
                # Convert back to old format for backward compatibility
                result = {
                    'text': transcription_result.text,
                    'segments': [
                        {
                            'start': seg.start,
                            'end': seg.end,
                            'text': seg.text
                        }
                        for seg in transcription_result.segments
                    ],
                    'language': transcription_result.language,
                    'file_path': str(file_path.absolute()),
                    'model': self.model_name,
                    'source_type': source_type
                }
                
                return result
                
            finally:
                # Clean up temporary file
                if temp_path.exists():
                    temp_path.unlink()
                    
        except Exception as e:
            console.print(f"❌ Error transcribing {file_path}: {e}")
            return None
    
    def get_audio_files(self, directory: Path) -> List[Path]:
        """Get all audio and video files from directory."""
        return get_media_files(directory)
    
    def estimate_duration(self, file_path: Path) -> float:
        """Estimate audio duration in seconds."""
        try:
            return self._media_extractor.estimate_duration(file_path)
        except:
            return 0.0