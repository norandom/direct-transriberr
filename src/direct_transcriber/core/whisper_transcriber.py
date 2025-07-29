"""Whisper-based transcription implementation."""

import os
import time
import warnings
from pathlib import Path
from typing import Optional
import whisper
from rich.console import Console
from rich.progress import Progress, TaskID

from .interfaces import TranscriberInterface
from .models import TranscriptionResult

console = Console()

# Suppress FP16 warnings for CPU processing
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")


class WhisperTranscriber(TranscriberInterface):
    """Local CPU-only transcriber using OpenAI Whisper."""
    
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model locally."""
        try:
            console.print(f"📥 Loading Whisper model: {self.model_name}")
            
            # Use custom model directory if set
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
    
    def transcribe(self, audio_path: Path, 
                  progress: Optional[Progress] = None,
                  task_id: Optional[TaskID] = None) -> TranscriptionResult:
        """
        Transcribe an audio file using Whisper.
        
        Args:
            audio_path: Path to WAV audio file
            progress: Optional progress tracker
            task_id: Optional task ID for progress updates
            
        Returns:
            TranscriptionResult with text and metadata
        """
        console.print(f"🎙️  Starting transcription with {self.model_name} model...")
        
        if progress and task_id:
            progress.update(task_id, advance=10, description=f"Loading audio: {audio_path.name}")
        
        start_time = time.time()
        
        try:
            # Transcribe using Whisper with CPU-specific settings
            result = self.model.transcribe(
                str(audio_path), 
                verbose=False,
                fp16=False  # Disable FP16 for CPU processing
            )
            
            if progress and task_id:
                progress.update(task_id, advance=70, description=f"Processing segments: {audio_path.name}")
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            console.print(f"✨ Transcription completed in {processing_time:.1f}s")
            
            # Convert to our TranscriptionResult format
            transcription_result = TranscriptionResult.from_whisper_result(
                whisper_result=result,
                file_path=str(audio_path),
                model=self.model_name,
                source_type='audio',  # Will be updated by caller if video
                processing_time=processing_time
            )
            
            if progress and task_id:
                progress.update(task_id, advance=20, description=f"Completed {audio_path.name} ({processing_time:.1f}s)")
            
            return transcription_result
            
        except Exception as e:
            console.print(f"❌ Error transcribing {audio_path}: {e}")
            raise
    
    def get_model_name(self) -> str:
        """Get the name of the transcription model."""
        return self.model_name
    
    def estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        # Rough estimates based on model size
        memory_map = {
            "tiny": 1 * 1024 * 1024 * 1024,      # 1GB
            "base": 1.5 * 1024 * 1024 * 1024,    # 1.5GB
            "small": 2 * 1024 * 1024 * 1024,     # 2GB
            "medium": 4 * 1024 * 1024 * 1024,    # 4GB
            "large-v3": 6 * 1024 * 1024 * 1024,  # 6GB
        }
        return int(memory_map.get(self.model_name, 1 * 1024 * 1024 * 1024))