"""RAG-optimized markdown formatter."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import FormatterInterface
from .rag_optimizer import RAGOptimizer, RAGChunk
from .chunking import SemanticChunking, SentenceChunking, FixedSizeChunking
from ..core.models import TranscriptionResult


class RAGMarkdownFormatter(FormatterInterface):
    """Enhanced markdown formatter optimized for RAG systems."""
    
    def __init__(self, 
                 chunking_strategy: str = "semantic",
                 include_metadata: bool = True,
                 include_context: bool = True,
                 include_entities: bool = True,
                 chunk_size: Optional[int] = None):
        """
        Initialize RAG markdown formatter.
        
        Args:
            chunking_strategy: Strategy to use ('semantic', 'sentence', 'fixed')
            include_metadata: Whether to include chunk metadata
            include_context: Whether to include inter-chunk context
            include_entities: Whether to include extracted entities
            chunk_size: Target chunk size (strategy-dependent)
        """
        self.include_metadata = include_metadata
        self.include_context = include_context
        self.include_entities = include_entities
        
        # Select chunking strategy
        if chunking_strategy == "semantic":
            strategy = SemanticChunking(
                target_size=chunk_size or 1000,
                min_size=200,
                max_size=2000
            )
        elif chunking_strategy == "sentence":
            strategy = SentenceChunking(
                max_sentences=5,
                max_chars=chunk_size or 1500
            )
        elif chunking_strategy == "fixed":
            strategy = FixedSizeChunking(
                chunk_size=chunk_size or 1000,
                overlap=200
            )
        else:
            raise ValueError(f"Unknown chunking strategy: {chunking_strategy}")
        
        self.rag_optimizer = RAGOptimizer(strategy)
    
    def format(self, result: TranscriptionResult, output_path: Path) -> None:
        """Format transcription as RAG-optimized markdown."""
        if not self.validate_result(result):
            raise ValueError("Invalid transcription result")
        
        # Generate RAG-optimized chunks
        rag_chunks = self.rag_optimizer.optimize(result)
        
        # Generate markdown content
        markdown_content = self._generate_markdown(result, rag_chunks)
        
        # Write to file
        output_path.write_text(markdown_content, encoding='utf-8')
        
        # Also save structured data as JSON sidecar
        json_path = output_path.with_suffix('.json')
        self._save_structured_data(result, rag_chunks, json_path)
    
    def get_file_extension(self) -> str:
        """Get file extension for markdown format."""
        return ".md"
    
    def _generate_markdown(self, result: TranscriptionResult, chunks: list[RAGChunk]) -> str:
        """Generate the markdown content."""
        lines = []
        
        # Document header
        source_type = "Video" if result.metadata.source_type == 'video' else "Audio"
        lines.extend([
            f"# {source_type} Transcription (RAG Optimized)",
            f"**File:** `{result.metadata.file_path}`",
            f"**Duration:** {self._format_duration(result.metadata.duration)} | **Model:** {result.metadata.model} | **Language:** {result.language}",
            f"**Source:** {result.metadata.source_type} | **Transcribed:** {result.metadata.transcribed_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Chunks:** {len(chunks)} | **Strategy:** {type(self.rag_optimizer.chunking_strategy).__name__}",
            "",
            "---",
            ""
        ])
        
        # Document summary
        if chunks:
            lines.extend([
                "## 📋 Document Summary",
                "",
                f"**Total Words:** {sum(chunk.word_count for chunk in chunks)}",
                f"**Average Quality:** {sum(chunk.quality_score for chunk in chunks) / len(chunks):.2f}",
                f"**Key Topics:** {', '.join(set().union(*(chunk.topics for chunk in chunks)))}",
                "",
                "---",
                ""
            ])
        
        # Chunks
        for i, chunk in enumerate(chunks, 1):
            lines.extend(self._format_chunk(chunk, i))
            lines.append("")
        
        # Document-level metadata
        if self.include_metadata:
            lines.extend(self._generate_document_metadata(result, chunks))
        
        return "\n".join(lines)
    
    def _format_chunk(self, chunk: RAGChunk, index: int) -> list[str]:
        """Format a single chunk as markdown."""
        lines = []
        
        # Chunk header
        start_time = self._format_time(chunk.start_time)
        end_time = self._format_time(chunk.end_time)
        
        lines.extend([
            f"## Segment {index} ({start_time} - {end_time})",
            ""
        ])
        
        # Chunk metadata (if enabled)
        if self.include_metadata:
            metadata_items = [
                f"**ID:** `{chunk.chunk_id}`",
                f"**Duration:** {chunk.duration:.1f}s",
                f"**Words:** {chunk.word_count}",
                f"**Quality:** {chunk.quality_score:.2f}"
            ]
            
            if chunk.keywords:
                metadata_items.append(f"**Keywords:** {', '.join(chunk.keywords[:5])}")
            
            if chunk.topics:
                metadata_items.append(f"**Topics:** {', '.join(chunk.topics)}")
            
            lines.extend([
                " | ".join(metadata_items),
                ""
            ])
        
        # Context before (if enabled and available)
        if self.include_context and chunk.context_before:
            lines.extend([
                f"*...{chunk.context_before}*",
                ""
            ])
        
        # Main content
        lines.extend([
            chunk.text,
            ""
        ])
        
        # Context after (if enabled and available)
        if self.include_context and chunk.context_after:
            lines.extend([
                f"*{chunk.context_after}...*",
                ""
            ])
        
        # Entities (if enabled and available)
        if self.include_entities and chunk.entities:
            entity_groups = {}
            for entity in chunk.entities:
                entity_type = entity['type']
                if entity_type not in entity_groups:
                    entity_groups[entity_type] = []
                entity_groups[entity_type].append(entity['text'])
            
            entity_lines = []
            for entity_type, entities in entity_groups.items():
                unique_entities = list(set(entities))[:5]  # Limit to 5 per type
                entity_lines.append(f"**{entity_type}:** {', '.join(unique_entities)}")
            
            if entity_lines:
                lines.extend([
                    "<details>",
                    "<summary>🏷️ Entities</summary>",
                    "",
                    *entity_lines,
                    "",
                    "</details>",
                    ""
                ])
        
        return lines
    
    def _generate_document_metadata(self, result: TranscriptionResult, chunks: list[RAGChunk]) -> list[str]:
        """Generate document-level metadata section."""
        lines = [
            "---",
            "",
            "## 🔍 Document Metadata",
            "",
            "### Processing Information",
            f"- **Processing Time:** {result.metadata.processing_time:.1f}s" if result.metadata.processing_time else "- **Processing Time:** Unknown",
            f"- **Model:** {result.metadata.model}",
            f"- **Language:** {result.language}",
            f"- **Confidence:** {result.confidence:.2f}" if result.confidence else "- **Confidence:** Not available",
            "",
            "### Content Statistics",
            f"- **Total Segments:** {len(result.segments)}",
            f"- **Total Chunks:** {len(chunks)}",
            f"- **Total Words:** {sum(chunk.word_count for chunk in chunks)}",
            f"- **Total Characters:** {sum(chunk.char_count for chunk in chunks)}",
            f"- **Average Chunk Size:** {sum(chunk.word_count for chunk in chunks) / len(chunks):.0f} words" if chunks else "- **Average Chunk Size:** 0 words",
            "",
            "### Quality Metrics",
            f"- **Overall Quality:** {sum(chunk.quality_score for chunk in chunks) / len(chunks):.2f}" if chunks else "- **Overall Quality:** N/A",
            f"- **High Quality Chunks:** {sum(1 for chunk in chunks if chunk.quality_score > 0.8)}/{len(chunks)}",
            f"- **Low Quality Chunks:** {sum(1 for chunk in chunks if chunk.quality_score < 0.5)}/{len(chunks)}",
            ""
        ]
        
        # All topics found
        all_topics = set()
        all_keywords = set()
        for chunk in chunks:
            all_topics.update(chunk.topics)
            all_keywords.update(chunk.keywords)
        
        if all_topics:
            lines.extend([
                "### Identified Topics",
                f"- {', '.join(sorted(all_topics))}",
                ""
            ])
        
        if all_keywords:
            top_keywords = sorted(all_keywords)[:20]  # Top 20 keywords
            lines.extend([
                "### Key Terms",
                f"- {', '.join(top_keywords)}",
                ""
            ])
        
        return lines
    
    def _save_structured_data(self, result: TranscriptionResult, chunks: list[RAGChunk], json_path: Path) -> None:
        """Save structured data as JSON for programmatic access."""
        data = {
            'metadata': result.metadata.to_dict(),
            'language': result.language,
            'total_chunks': len(chunks),
            'chunks': [chunk.to_dict() for chunk in chunks],
            'processing_info': {
                'chunking_strategy': type(self.rag_optimizer.chunking_strategy).__name__,
                'total_words': sum(chunk.word_count for chunk in chunks),
                'total_characters': sum(chunk.char_count for chunk in chunks),
                'average_quality': sum(chunk.quality_score for chunk in chunks) / len(chunks) if chunks else 0,
                'generated_at': datetime.now().isoformat()
            }
        }
        
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration as MM:SS."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def _format_time(self, seconds: float) -> str:
        """Format timestamp as MM:SS."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"