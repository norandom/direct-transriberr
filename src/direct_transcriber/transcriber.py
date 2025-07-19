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

console = Console()

# Suppress FP16 warnings for CPU processing
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


def get_media_files(directory: Path) -> List[Path]:
    """Get all audio and video files from directory without loading models."""
    # Audio formats
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma', '.aac'}
    # Video formats
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
    
    all_extensions = audio_extensions | video_extensions
    
    files = []
    for ext in all_extensions:
        files.extend(directory.glob(f"**/*{ext}"))
        files.extend(directory.glob(f"**/*{ext.upper()}"))
    
    return sorted(files)


class LocalTranscriber:
    """Local CPU-only audio transcriber using Whisper."""
    
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model locally."""
        try:
            console.print(f"📥 Loading Whisper model: {self.model_name}")
            
            # Use custom model directory if set
            import os
            download_root = os.environ.get('WHISPER_MODEL_DIR', None)
            
            if download_root:
                console.print(f"🗂️  Using model directory: {download_root}")
                self.model = whisper.load_model(self.model_name, device="cpu", download_root=download_root)
            else:
                self.model = whisper.load_model(self.model_name, device="cpu")
            
            console.print(f"✅ Model loaded successfully")
        except Exception as e:
            console.print(f"❌ Error loading model: {e}")
            raise
    
    def _extract_audio(self, input_path: Path, output_path: Path) -> bool:
        """Extract audio using ffmpeg."""
        try:
            (
                ffmpeg
                .input(str(input_path))
                .output(str(output_path), acodec='pcm_s16le', ac=1, ar='16000')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return True
        except ffmpeg.Error as e:
            console.print(f"❌ FFmpeg error: {e}")
            return False
    
    def transcribe_file(self, file_path: Path, progress: Progress, task_id: TaskID) -> Optional[Dict]:
        """Transcribe a single audio or video file."""
        try:
            file_ext = file_path.suffix.lower()
            is_video = file_ext in {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
            
            if is_video:
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
                
                console.print(f"🎙️  Starting transcription with {self.model_name} model...")
                progress.update(task_id, advance=30, description=f"Transcribing {file_path.name}")
                
                # Transcribe using Whisper with CPU-specific settings
                import time
                start_time = time.time()
                
                # Add intermediate progress updates
                progress.update(task_id, advance=10, description=f"Loading audio: {file_path.name}")
                
                result = self.model.transcribe(
                    str(temp_path), 
                    verbose=False,
                    fp16=False  # Disable FP16 for CPU processing
                )
                
                progress.update(task_id, advance=20, description=f"Processing segments: {file_path.name}")
                
                end_time = time.time()
                
                # Calculate processing time
                processing_time = end_time - start_time
                console.print(f"✨ Transcription completed in {processing_time:.1f}s")
                progress.update(task_id, advance=30, description=f"Completed {file_path.name} ({processing_time:.1f}s)")
                
                # Add metadata
                result['file_path'] = str(file_path.absolute())
                result['model'] = self.model_name
                result['source_type'] = 'video' if is_video else 'audio'
                
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
            probe = ffmpeg.probe(str(file_path))
            duration = float(probe['format']['duration'])
            return duration
        except:
            return 0.0