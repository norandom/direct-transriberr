"""RAG-specific optimizations for transcription output."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..core.models import TranscriptionResult
from .chunking import Chunk, ChunkingStrategy, SemanticChunking


@dataclass
class RAGChunk:
    """Enhanced chunk with RAG-specific metadata."""
    text: str
    start_time: float
    end_time: float
    duration: float
    word_count: int
    char_count: int
    confidence: float
    
    # RAG-specific enhancements
    chunk_id: str
    keywords: List[str]
    summary: str
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    entities: List[Dict[str, Any]] = None
    topics: List[str] = None
    quality_score: float = 1.0
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = []
        if self.topics is None:
            self.topics = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'chunk_id': self.chunk_id,
            'text': self.text,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'word_count': self.word_count,
            'char_count': self.char_count,
            'confidence': self.confidence,
            'keywords': self.keywords,
            'summary': self.summary,
            'context_before': self.context_before,
            'context_after': self.context_after,
            'entities': self.entities,
            'topics': self.topics,
            'quality_score': self.quality_score
        }


class RAGOptimizer:
    """Optimize transcription results for RAG systems."""
    
    def __init__(self, chunking_strategy: Optional[ChunkingStrategy] = None):
        self.chunking_strategy = chunking_strategy or SemanticChunking()
    
    def optimize(self, result: TranscriptionResult) -> List[RAGChunk]:
        """
        Convert transcription result to RAG-optimized chunks.
        
        Args:
            result: Original transcription result
            
        Returns:
            List of RAG-optimized chunks
        """
        # Create base chunks using chunking strategy
        base_chunks = self.chunking_strategy.chunk(result)
        
        # Enhance each chunk with RAG-specific metadata
        rag_chunks = []
        for i, chunk in enumerate(base_chunks):
            rag_chunk = self._enhance_chunk(chunk, i, result)
            rag_chunks.append(rag_chunk)
        
        # Add inter-chunk context
        self._add_context_links(rag_chunks)
        
        return rag_chunks
    
    def _enhance_chunk(self, chunk: Chunk, index: int, result: TranscriptionResult) -> RAGChunk:
        """Enhance a basic chunk with RAG-specific metadata."""
        
        # Generate unique chunk ID
        chunk_id = f"{result.metadata.file_path.split('/')[-1]}_{index:03d}"
        
        # Extract keywords
        keywords = self._extract_keywords(chunk.text)
        
        # Generate summary
        summary = self._generate_summary(chunk.text)
        
        # Extract entities
        entities = self._extract_entities(chunk.text)
        
        # Identify topics
        topics = self._identify_topics(chunk.text)
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(chunk)
        
        return RAGChunk(
            text=chunk.text,
            start_time=chunk.start_time,
            end_time=chunk.end_time,
            duration=chunk.duration,
            word_count=chunk.word_count,
            char_count=chunk.char_count,
            confidence=chunk.confidence,
            chunk_id=chunk_id,
            keywords=keywords,
            summary=summary,
            entities=entities,
            topics=topics,
            quality_score=quality_score
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        # Simple keyword extraction - can be enhanced with NLP libraries
        words = text.lower().split()
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'this', 'that',
            'these', 'those', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
            'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he',
            'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
            'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what',
            'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is',
            'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'having', 'do', 'does', 'did', 'doing', 'will', 'would', 'should',
            'could', 'can', 'may', 'might', 'must', 'shall'
        }
        
        # Filter and count words
        word_freq = {}
        for word in words:
            # Clean word (remove punctuation)
            clean_word = ''.join(c for c in word if c.isalnum()).lower()
            if len(clean_word) > 2 and clean_word not in stop_words:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        # Return top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in keywords[:10] if freq > 1]
    
    def _generate_summary(self, text: str) -> str:
        """Generate a brief summary of the text."""
        sentences = text.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return text[:100] + "..." if len(text) > 100 else text
        
        # Take first sentence as summary, or combine first two if very short
        summary = sentences[0]
        if len(summary) < 50 and len(sentences) > 1:
            summary += ". " + sentences[1]
        
        return summary[:200] + "..." if len(summary) > 200 else summary
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text."""
        # Simple entity extraction - can be enhanced with NLP libraries
        entities = []
        
        # Look for common patterns
        import re
        
        # Time patterns
        time_patterns = [
            r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b',
            r'\b\d{1,2}\s*(?:AM|PM|am|pm)\b'
        ]
        for pattern in time_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'type': 'TIME',
                    'start': match.start(),
                    'end': match.end()
                })
        
        # Number patterns
        number_patterns = [
            r'\b\d+(?:,\d{3})*(?:\.\d+)?\b',
            r'\b\d+(?:\.\d+)?%\b'
        ]
        for pattern in number_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'type': 'NUMBER',
                    'start': match.start(),
                    'end': match.end()
                })
        
        # Capitalized words (potential proper nouns)
        proper_noun_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.finditer(proper_noun_pattern, text)
        for match in matches:
            # Skip common words that happen to be capitalized
            word = match.group()
            if word not in {'The', 'This', 'That', 'And', 'But', 'So', 'Now', 'Then'}:
                entities.append({
                    'text': word,
                    'type': 'PROPER_NOUN',
                    'start': match.start(),
                    'end': match.end()
                })
        
        return entities
    
    def _identify_topics(self, text: str) -> List[str]:
        """Identify main topics in the text."""
        # Simple topic identification based on domain keywords
        topic_keywords = {
            'technology': ['software', 'computer', 'digital', 'algorithm', 'data', 'system', 'program', 'code', 'tech', 'AI', 'machine learning'],
            'business': ['company', 'market', 'revenue', 'profit', 'strategy', 'customer', 'sales', 'business', 'corporate', 'financial'],
            'education': ['learn', 'teach', 'student', 'school', 'university', 'education', 'study', 'course', 'knowledge', 'academic'],
            'health': ['health', 'medical', 'doctor', 'patient', 'treatment', 'medicine', 'hospital', 'care', 'disease', 'therapy'],
            'science': ['research', 'study', 'experiment', 'theory', 'analysis', 'scientific', 'hypothesis', 'method', 'result', 'data'],
            'finance': ['money', 'investment', 'bank', 'financial', 'economic', 'budget', 'cost', 'price', 'funding', 'capital']
        }
        
        text_lower = text.lower()
        topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _calculate_quality_score(self, chunk: Chunk) -> float:
        """Calculate quality score for the chunk."""
        score = 1.0
        
        # Factor in transcription confidence
        score *= chunk.confidence
        
        # Penalize very short chunks
        if chunk.word_count < 10:
            score *= 0.7
        
        # Penalize chunks with very low confidence
        if chunk.confidence < 0.5:
            score *= 0.6
        
        # Bonus for good length chunks
        if 50 <= chunk.word_count <= 200:
            score *= 1.1
        
        return min(score, 1.0)
    
    def _add_context_links(self, chunks: List[RAGChunk]) -> None:
        """Add contextual links between chunks."""
        for i, chunk in enumerate(chunks):
            # Add context from previous chunk
            if i > 0:
                prev_chunk = chunks[i - 1]
                # Take last 20 words from previous chunk
                prev_words = prev_chunk.text.split()[-20:]
                chunk.context_before = ' '.join(prev_words)
            
            # Add context from next chunk
            if i < len(chunks) - 1:
                next_chunk = chunks[i + 1]
                # Take first 20 words from next chunk
                next_words = next_chunk.text.split()[:20]
                chunk.context_after = ' '.join(next_words)