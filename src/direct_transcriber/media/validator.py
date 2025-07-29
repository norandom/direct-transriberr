"""Media file validation."""

from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
import ffmpeg

from .formats import is_media_file, ALL_EXTENSIONS


@dataclass
class ValidationResult:
    """Result of media file validation."""
    is_valid: bool
    error: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class MediaValidator:
    """Validate media files before processing."""
    
    def __init__(self, max_file_size_gb: float = 10.0, min_duration_seconds: float = 0.1):
        self.max_file_size_bytes = int(max_file_size_gb * 1024 * 1024 * 1024)
        self.min_duration_seconds = min_duration_seconds
    
    def validate(self, file_path: Path) -> ValidationResult:
        """
        Validate a media file.
        
        Args:
            file_path: Path to media file
            
        Returns:
            ValidationResult with status and any issues
        """
        # Check file exists
        if not file_path.exists():
            return ValidationResult(False, f"File not found: {file_path}")
        
        # Check if it's a file (not directory)
        if not file_path.is_file():
            return ValidationResult(False, f"Not a file: {file_path}")
        
        # Check file extension
        if not is_media_file(file_path):
            return ValidationResult(
                False, 
                f"Unsupported format: {file_path.suffix}. "
                f"Supported formats: {', '.join(sorted(ALL_EXTENSIONS))}"
            )
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size == 0:
            return ValidationResult(False, "File is empty")
        
        if file_size > self.max_file_size_bytes:
            size_gb = file_size / (1024 * 1024 * 1024)
            return ValidationResult(
                False, 
                f"File too large: {size_gb:.1f}GB (max: {self.max_file_size_bytes / (1024**3):.1f}GB)"
            )
        
        # Try to probe the file with ffmpeg
        try:
            probe = ffmpeg.probe(str(file_path))
            
            # Check duration
            duration = float(probe.get('format', {}).get('duration', 0))
            if duration < self.min_duration_seconds:
                return ValidationResult(
                    False, 
                    f"File too short: {duration:.1f}s (min: {self.min_duration_seconds}s)"
                )
            
            # Check for audio stream
            has_audio = any(
                stream.get('codec_type') == 'audio' 
                for stream in probe.get('streams', [])
            )
            
            if not has_audio:
                return ValidationResult(False, "No audio stream found in file")
            
            # Warnings for potential issues
            warnings = []
            
            # Warn about very long files
            if duration > 3600 * 4:  # 4 hours
                hours = duration / 3600
                warnings.append(f"Very long file ({hours:.1f} hours) may take significant time to process")
            
            # Warn about large files
            if file_size > 1024 * 1024 * 1024:  # 1GB
                size_gb = file_size / (1024 * 1024 * 1024)
                warnings.append(f"Large file ({size_gb:.1f}GB) may require significant memory")
            
            return ValidationResult(True, warnings=warnings)
            
        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else "Unknown error"
            return ValidationResult(False, f"FFmpeg error: {error_msg}")
        except Exception as e:
            return ValidationResult(False, f"Error validating file: {str(e)}")
    
    def validate_batch(self, file_paths: List[Path]) -> dict[Path, ValidationResult]:
        """
        Validate multiple files.
        
        Args:
            file_paths: List of file paths to validate
            
        Returns:
            Dictionary mapping file paths to validation results
        """
        results = {}
        for file_path in file_paths:
            results[file_path] = self.validate(file_path)
        return results