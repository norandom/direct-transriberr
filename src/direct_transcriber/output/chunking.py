"""Intelligent chunking strategies for RAG optimization."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple
from ..core.models import TranscriptionResult, Segment


@dataclass
class Chunk:
    """A chunk of transcribed content optimized for RAG."""
    text: str
    start_time: float
    end_time: float
    segment_indices: List[int]  # Which original segments this chunk contains
    confidence: float
    word_count: int
    char_count: int
    overlap_prev: Optional[str] = None  # Overlapping text with previous chunk
    overlap_next: Optional[str] = None  # Overlapping text with next chunk
    
    @property
    def duration(self) -> float:
        """Duration of this chunk in seconds."""
        return self.end_time - self.start_time
    
    def to_dict(self) -> dict:
        """Convert chunk to dictionary for serialization."""
        return {
            'text': self.text,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'word_count': self.word_count,
            'char_count': self.char_count,
            'confidence': self.confidence,
            'segment_indices': self.segment_indices,
            'overlap_prev': self.overlap_prev,
            'overlap_next': self.overlap_next
        }


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""
    
    @abstractmethod
    def chunk(self, result: TranscriptionResult) -> List[Chunk]:
        """
        Split transcription result into optimized chunks.
        
        Args:
            result: Transcription result to chunk
            
        Returns:
            List of chunks optimized for RAG retrieval
        """
        pass
    
    def _calculate_confidence(self, segments: List[Segment]) -> float:
        """Calculate average confidence for a group of segments."""
        if not segments:
            return 0.0
        
        confidences = [seg.confidence for seg in segments if seg.confidence > 0]
        return sum(confidences) / len(confidences) if confidences else 1.0
    
    def _add_overlap(self, chunks: List[Chunk], overlap_words: int = 20) -> List[Chunk]:
        """Add overlapping context between chunks."""
        if len(chunks) <= 1:
            return chunks
        
        for i, chunk in enumerate(chunks):
            # Add overlap with previous chunk
            if i > 0:
                prev_words = chunks[i-1].text.split()[-overlap_words:]
                chunk.overlap_prev = ' '.join(prev_words)
            
            # Add overlap with next chunk  
            if i < len(chunks) - 1:
                next_words = chunks[i+1].text.split()[:overlap_words]
                chunk.overlap_next = ' '.join(next_words)
        
        return chunks


class FixedSizeChunking(ChunkingStrategy):
    """Simple fixed-size chunking by character count."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, result: TranscriptionResult) -> List[Chunk]:
        """Split text into fixed-size chunks with overlap."""
        text = result.text
        segments = result.segments
        
        if not text or not segments:
            return []
        
        chunks = []
        start_pos = 0
        
        while start_pos < len(text):
            end_pos = min(start_pos + self.chunk_size, len(text))
            
            # Try to break at sentence boundary
            if end_pos < len(text):
                sentence_end = text.rfind('.', start_pos, end_pos)
                if sentence_end > start_pos + self.chunk_size // 2:
                    end_pos = sentence_end + 1
            
            chunk_text = text[start_pos:end_pos].strip()
            
            if chunk_text:
                # Find segments that overlap with this text chunk
                chunk_segments = self._find_segments_for_text(segments, start_pos, end_pos, text)
                
                if chunk_segments:
                    chunk = Chunk(
                        text=chunk_text,
                        start_time=chunk_segments[0].start,
                        end_time=chunk_segments[-1].end,
                        segment_indices=[segments.index(seg) for seg in chunk_segments],
                        confidence=self._calculate_confidence(chunk_segments),
                        word_count=len(chunk_text.split()),
                        char_count=len(chunk_text)
                    )
                    chunks.append(chunk)
            
            # Move start position with overlap
            start_pos = max(end_pos - self.overlap, start_pos + 1)
            if start_pos >= end_pos:
                break
        
        return self._add_overlap(chunks)
    
    def _find_segments_for_text(self, segments: List[Segment], start_pos: int, end_pos: int, full_text: str) -> List[Segment]:
        """Find segments that contribute to a text chunk."""
        # This is a simplified approach - in practice you'd want more sophisticated mapping
        chunk_text = full_text[start_pos:end_pos]
        result_segments = []
        
        text_pos = 0
        for segment in segments:
            segment_start = full_text.find(segment.text.strip(), text_pos)
            if segment_start >= start_pos and segment_start < end_pos:
                result_segments.append(segment)
            text_pos = segment_start + len(segment.text) if segment_start >= 0 else text_pos
        
        return result_segments or segments[:1]  # Fallback to first segment


class SentenceChunking(ChunkingStrategy):
    """Chunk by sentences with intelligent boundary detection."""
    
    def __init__(self, max_sentences: int = 5, max_chars: int = 1500):
        self.max_sentences = max_sentences
        self.max_chars = max_chars
    
    def chunk(self, result: TranscriptionResult) -> List[Chunk]:
        """Split into chunks at sentence boundaries."""
        text = result.text
        segments = result.segments
        
        if not text or not segments:
            return []
        
        # Split into sentences using multiple delimiters
        sentences = self._split_sentences(text)
        chunks = []
        current_sentences = []
        current_chars = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check if adding this sentence would exceed limits
            would_exceed = (
                len(current_sentences) >= self.max_sentences or
                current_chars + len(sentence) > self.max_chars
            )
            
            if would_exceed and current_sentences:
                # Create chunk from current sentences
                chunk_text = ' '.join(current_sentences)
                chunk_segments = self._find_segments_for_sentences(segments, current_sentences, text)
                
                if chunk_segments:
                    chunk = Chunk(
                        text=chunk_text,
                        start_time=chunk_segments[0].start,
                        end_time=chunk_segments[-1].end,
                        segment_indices=[segments.index(seg) for seg in chunk_segments],
                        confidence=self._calculate_confidence(chunk_segments),
                        word_count=len(chunk_text.split()),
                        char_count=len(chunk_text)
                    )
                    chunks.append(chunk)
                
                # Start new chunk
                current_sentences = [sentence]
                current_chars = len(sentence)
            else:
                current_sentences.append(sentence)
                current_chars += len(sentence)
        
        # Add final chunk
        if current_sentences:
            chunk_text = ' '.join(current_sentences)
            chunk_segments = self._find_segments_for_sentences(segments, current_sentences, text)
            
            if chunk_segments:
                chunk = Chunk(
                    text=chunk_text,
                    start_time=chunk_segments[0].start,
                    end_time=chunk_segments[-1].end,
                    segment_indices=[segments.index(seg) for seg in chunk_segments],
                    confidence=self._calculate_confidence(chunk_segments),
                    word_count=len(chunk_text.split()),
                    char_count=len(chunk_text)
                )
                chunks.append(chunk)
        
        return self._add_overlap(chunks)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Enhanced sentence splitting pattern
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _find_segments_for_sentences(self, segments: List[Segment], sentences: List[str], full_text: str) -> List[Segment]:
        """Find segments that contain the given sentences."""
        sentence_text = ' '.join(sentences)
        result_segments = []
        
        for segment in segments:
            if any(sent.lower() in segment.text.lower() for sent in sentences):
                result_segments.append(segment)
        
        return result_segments or segments[:1]


class SemanticChunking(ChunkingStrategy):
    """Advanced semantic chunking based on topic shifts and natural breaks."""
    
    def __init__(self, target_size: int = 1000, min_size: int = 200, max_size: int = 2000):
        self.target_size = target_size
        self.min_size = min_size
        self.max_size = max_size
        
        # Keywords that indicate topic shifts
        self.topic_shift_keywords = {
            'however', 'but', 'meanwhile', 'furthermore', 'moreover', 'additionally',
            'in contrast', 'on the other hand', 'similarly', 'likewise', 'therefore',
            'consequently', 'as a result', 'in conclusion', 'to summarize', 'finally',
            'first', 'second', 'third', 'next', 'then', 'afterwards', 'previously',
            'moving on', 'turning to', 'regarding', 'concerning', 'speaking of'
        }
    
    def chunk(self, result: TranscriptionResult) -> List[Chunk]:
        """Create semantic chunks based on content analysis."""
        segments = result.segments
        
        if not segments:
            return []
        
        chunks = []
        current_segments = []
        current_chars = 0
        
        for i, segment in enumerate(segments):
            segment_text = segment.text.strip()
            segment_chars = len(segment_text)
            
            # Check for natural break points
            is_natural_break = self._is_natural_break(segment, segments, i)
            would_exceed_max = current_chars + segment_chars > self.max_size
            is_good_size = current_chars >= self.min_size
            
            # Decide whether to break here
            should_break = (
                (is_natural_break and is_good_size) or
                would_exceed_max or
                (current_chars >= self.target_size and self._is_sentence_end(segment_text))
            )
            
            if should_break and current_segments:
                # Create chunk from current segments
                chunk = self._create_chunk_from_segments(current_segments, segments)
                chunks.append(chunk)
                
                # Start new chunk
                current_segments = [segment]
                current_chars = segment_chars
            else:
                current_segments.append(segment)
                current_chars += segment_chars
        
        # Add final chunk
        if current_segments:
            chunk = self._create_chunk_from_segments(current_segments, segments)
            chunks.append(chunk)
        
        return self._add_overlap(chunks)
    
    def _is_natural_break(self, segment: Segment, all_segments: List[Segment], index: int) -> bool:
        """Detect natural breaking points in the transcription."""
        text = segment.text.lower().strip()
        
        # Check for topic shift keywords
        if any(keyword in text for keyword in self.topic_shift_keywords):
            return True
        
        # Check for long pauses (if we have timing info)
        if index > 0:
            prev_segment = all_segments[index - 1]
            pause_duration = segment.start - prev_segment.end
            if pause_duration > 2.0:  # 2+ second pause
                return True
        
        # Check for question-answer patterns
        if text.endswith('?') and index < len(all_segments) - 1:
            return True
        
        # Check for enumeration patterns
        enumeration_patterns = [r'^\d+\.', r'^first', r'^second', r'^third', r'^finally']
        if any(re.match(pattern, text) for pattern in enumeration_patterns):
            return True
        
        return False
    
    def _is_sentence_end(self, text: str) -> bool:
        """Check if text ends with sentence-ending punctuation."""
        return text.rstrip().endswith(('.', '!', '?'))
    
    def _create_chunk_from_segments(self, segments: List[Segment], all_segments: List[Segment]) -> Chunk:
        """Create a chunk from a list of segments."""
        if not segments:
            raise ValueError("Cannot create chunk from empty segments")
        
        chunk_text = ' '.join(seg.text.strip() for seg in segments)
        
        return Chunk(
            text=chunk_text,
            start_time=segments[0].start,
            end_time=segments[-1].end,
            segment_indices=[all_segments.index(seg) for seg in segments],
            confidence=self._calculate_confidence(segments),
            word_count=len(chunk_text.split()),
            char_count=len(chunk_text)
        )