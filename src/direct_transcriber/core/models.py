"""Core data models for transcription."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any


class ProcessingStatus(Enum):
    """Status of transcription processing."""
    PENDING = "pending"
    EXTRACTING = "extracting"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    FORMATTING = "formatting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Segment:
    """A transcribed segment with timing information."""
    start: float
    end: float
    text: str
    confidence: float = 1.0
    
    @property
    def duration(self) -> float:
        """Duration of the segment in seconds."""
        return self.end - self.start
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'start': self.start,
            'end': self.end,
            'text': self.text,
            'confidence': self.confidence
        }


@dataclass
class MediaInfo:
    """Information about the media file."""
    file_path: Path
    duration: float  # in seconds
    format: str
    size_bytes: int
    is_video: bool
    audio_codec: Optional[str] = None
    video_codec: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'file_path': str(self.file_path),
            'duration': self.duration,
            'format': self.format,
            'size_bytes': self.size_bytes,
            'is_video': self.is_video,
            'audio_codec': self.audio_codec,
            'video_codec': self.video_codec
        }


@dataclass
class TranscriptionMetadata:
    """Metadata about the transcription process."""
    file_path: str
    duration: float
    model: str
    language: str
    source_type: str  # 'audio' or 'video'
    transcribed_at: datetime = field(default_factory=datetime.now)
    processing_time: Optional[float] = None
    whisper_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'file_path': self.file_path,
            'duration': self.duration,
            'model': self.model,
            'language': self.language,
            'source_type': self.source_type,
            'transcribed_at': self.transcribed_at.isoformat(),
            'processing_time': self.processing_time,
            'whisper_version': self.whisper_version
        }


@dataclass
class TranscriptionResult:
    """Complete transcription result."""
    text: str
    segments: List[Segment]
    metadata: TranscriptionMetadata
    language: str
    confidence: Optional[float] = None
    
    @classmethod
    def from_whisper_result(cls, whisper_result: Dict[str, Any], 
                           file_path: str, model: str, 
                           source_type: str, processing_time: float) -> 'TranscriptionResult':
        """Create TranscriptionResult from Whisper output."""
        segments = []
        for seg in whisper_result.get('segments', []):
            segments.append(Segment(
                start=seg['start'],
                end=seg['end'],
                text=seg['text'].strip(),
                confidence=seg.get('confidence', 1.0)
            ))
        
        # Calculate duration from last segment
        duration = segments[-1].end if segments else 0.0
        
        metadata = TranscriptionMetadata(
            file_path=file_path,
            duration=duration,
            model=model,
            language=whisper_result.get('language', 'unknown'),
            source_type=source_type,
            processing_time=processing_time
        )
        
        return cls(
            text=whisper_result.get('text', '').strip(),
            segments=segments,
            metadata=metadata,
            language=whisper_result.get('language', 'unknown')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'text': self.text,
            'segments': [seg.to_dict() for seg in self.segments],
            'metadata': self.metadata.to_dict(),
            'language': self.language,
            'confidence': self.confidence
        }