"""Markdown formatting for RAGflow integration."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json


class MarkdownFormatter:
    """Format transcription results as markdown for RAGflow."""
    
    def __init__(self, include_timestamps: bool = False, chunk_size: Optional[int] = None):
        self.include_timestamps = include_timestamps
        self.chunk_size = chunk_size
    
    def format_transcription(self, result: Dict, output_path: Path) -> str:
        """Format transcription result as markdown."""
        if not result:
            return ""
        
        # Extract metadata
        file_path = result.get('file_path', 'Unknown')
        model = result.get('model', 'Unknown')
        language = result.get('language', 'Unknown')
        source_type = result.get('source_type', 'audio')
        
        # Calculate duration if available
        duration = "Unknown"
        if 'segments' in result and result['segments']:
            last_segment = result['segments'][-1]
            if 'end' in last_segment:
                total_seconds = int(last_segment['end'])
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                duration = f"{minutes}:{seconds:02d}"
        
        # Build markdown content
        transcription_type = "Video" if source_type == 'video' else "Audio"
        markdown_lines = [
            f"# {transcription_type} Transcription",
            f"**File:** `{file_path}`",
            f"**Duration:** {duration} | **Model:** {model} | **Language:** {language}",
            f"**Source:** {source_type} | **Transcribed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            ""
        ]
        
        # Add transcription content
        if self.chunk_size:
            markdown_lines.extend(self._format_chunked(result))
        elif self.include_timestamps:
            markdown_lines.extend(self._format_timestamped(result))
        else:
            markdown_lines.extend(self._format_clean(result))
        
        markdown_content = "\n".join(markdown_lines)
        
        # Write to file
        output_path.write_text(markdown_content, encoding='utf-8')
        
        return markdown_content
    
    def _format_clean(self, result: Dict) -> List[str]:
        """Format as clean text for RAGflow."""
        text = result.get('text', '').strip()
        if not text:
            return ["*No transcription available*"]
        
        # Split into paragraphs for better readability
        paragraphs = []
        sentences = text.split('. ')
        current_paragraph = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                current_paragraph.append(sentence)
                if len(current_paragraph) >= 3:  # Group 3 sentences per paragraph
                    paragraphs.append('. '.join(current_paragraph) + '.')
                    current_paragraph = []
        
        # Add remaining sentences
        if current_paragraph:
            paragraphs.append('. '.join(current_paragraph) + ('.' if not current_paragraph[-1].endswith('.') else ''))
        
        return paragraphs
    
    def _format_timestamped(self, result: Dict) -> List[str]:
        """Format with timestamps for reference."""
        segments = result.get('segments', [])
        if not segments:
            return self._format_clean(result)
        
        lines = []
        for segment in segments:
            start = self._format_timestamp(segment.get('start', 0))
            end = self._format_timestamp(segment.get('end', 0))
            text = segment.get('text', '').strip()
            
            if text:
                lines.append(f"## [{start}] - [{end}]")
                lines.append(f"{text}")
                lines.append("")
        
        return lines
    
    def _format_chunked(self, result: Dict) -> List[str]:
        """Format in chunks for optimal RAG performance."""
        segments = result.get('segments', [])
        if not segments:
            return self._format_clean(result)
        
        lines = []
        current_chunk = []
        current_chunk_chars = 0
        chunk_number = 1
        
        for segment in segments:
            text = segment.get('text', '').strip()
            if not text:
                continue
            
            # Add to current chunk if within size limit
            if current_chunk_chars + len(text) <= self.chunk_size:
                current_chunk.append(text)
                current_chunk_chars += len(text)
            else:
                # Finalize current chunk
                if current_chunk:
                    start_time = self._format_timestamp(segments[0].get('start', 0))
                    end_time = self._format_timestamp(segment.get('start', 0))
                    
                    lines.append(f"## Segment {chunk_number} ({start_time}-{end_time})")
                    lines.append(' '.join(current_chunk))
                    lines.append("")
                    
                    chunk_number += 1
                
                # Start new chunk
                current_chunk = [text]
                current_chunk_chars = len(text)
        
        # Add final chunk
        if current_chunk:
            start_time = self._format_timestamp(segments[0].get('start', 0))
            end_time = self._format_timestamp(segments[-1].get('end', 0))
            
            lines.append(f"## Segment {chunk_number} ({start_time}-{end_time})")
            lines.append(' '.join(current_chunk))
        
        return lines
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp as MM:SS."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def save_json(self, result: Dict, output_path: Path):
        """Save raw transcription result as JSON."""
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')