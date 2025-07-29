"""Base interfaces for output formatting."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

from ..core.models import TranscriptionResult


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
    
    def validate_result(self, result: TranscriptionResult) -> bool:
        """
        Validate that the transcription result is suitable for formatting.
        
        Args:
            result: Transcription result to validate
            
        Returns:
            True if result is valid for formatting
        """
        return (
            result is not None 
            and hasattr(result, 'text') 
            and hasattr(result, 'segments')
            and len(result.text.strip()) > 0
        )