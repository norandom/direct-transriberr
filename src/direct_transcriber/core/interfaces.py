"""Abstract interfaces for transcription system."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from rich.progress import Progress, TaskID

from .models import TranscriptionResult


class TranscriberInterface(ABC):
    """Abstract interface for transcription engines."""
    
    @abstractmethod
    def transcribe(self, audio_path: Path, 
                  progress: Optional[Progress] = None,
                  task_id: Optional[TaskID] = None) -> TranscriptionResult:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to WAV audio file
            progress: Optional progress tracker
            task_id: Optional task ID for progress updates
            
        Returns:
            TranscriptionResult with text and metadata
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the name of the transcription model."""
        pass
    
    @abstractmethod
    def estimate_memory_usage(self) -> int:
        """Estimate memory usage in bytes."""
        pass


class FormatterInterface(ABC):
    """Abstract interface for output formatters."""
    
    @abstractmethod
    def format(self, result: TranscriptionResult, output_path: Path) -> None:
        """
        Format and save transcription result.
        
        Args:
            result: Transcription result to format
            output_path: Path to save formatted output
        """
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this format."""
        pass