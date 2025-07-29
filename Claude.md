# Direct Transcriber - Improvement TODO List

## Project Context
This tool transcribes videos/audio to text for RAG tools like RAGflow. The output should be optimized for semantic search and retrieval.

## TODO: Core Improvements

### 1. Error Handling & Resilience
- [ ] Add retry logic for failed transcriptions (temporary file errors, memory issues)
- [ ] Implement better error recovery for batch processing (continue with remaining files)
- [ ] Add validation for input files before processing (format, size, corruption check)
- [ ] Handle edge cases like corrupted audio/video files gracefully
- [ ] Add option to skip problematic files and log errors

### 2. Performance Optimizations
- [ ] Add file size/duration estimation before processing for better progress tracking
- [ ] Cache extracted audio for video files to avoid re-extraction on retry
- [ ] Implement streaming transcription for very large files
- [ ] Add memory usage monitoring during transcription
- [ ] Optimize batch size based on available memory

### 3. Code Organization & Architecture
- [x] Extract FFmpeg operations to a dedicated module (`src/direct_transcriber/media.py`)
- [ ] Create a proper configuration management system
- [ ] Add dependency injection for better testability
- [x] Implement a plugin system for different output formats
- [x] Create abstract base classes for transcribers and formatters

### 4. Feature Enhancements
- [ ] Implement speaker diarization when available
- [ ] Add language detection and multi-language support
- [ ] Support for custom vocabulary and domain-specific terms
- [ ] Add webhook/callback support for integration with other systems
- [ ] Implement pause/resume capability for long batch jobs

### 5. Testing & Quality
- [ ] Add comprehensive unit tests for all modules
- [ ] Implement integration tests for the CLI
- [ ] Add performance benchmarks
- [ ] Set up continuous integration
- [ ] Add type hints throughout the codebase

### 6. User Experience
- [ ] Add a configuration file system (~/.direct-transcriber/config.yml)
- [ ] Implement resume capability for interrupted batch jobs
- [ ] Add dry-run mode to preview what will be processed
- [ ] Better progress indication with ETA and throughput metrics
- [ ] Add interactive mode for model selection
- [ ] Support for glob patterns in file selection

### 7. Security & Privacy
- [ ] Add option to sanitize/redact sensitive information from transcripts
- [ ] Implement secure file handling for temporary files
- [ ] Add audit logging for compliance requirements
- [ ] Support for encrypted input/output directories

### 8. Docker & Deployment
- [ ] Multi-stage Docker build to reduce image size
- [ ] Add health checks to containers
- [ ] Implement proper signal handling for graceful shutdown
- [ ] Add Kubernetes deployment manifests
- [ ] Create docker-compose profiles for different use cases

## TODO: RAG-Optimized Output Improvements

### 1. Semantic Chunking
- [x] Implement intelligent chunking based on sentence boundaries and topic shifts
- [x] Add overlap between chunks to maintain context (sliding window)
- [x] Dynamic chunk sizing based on content density
- [x] Add chunk metadata (position, context, neighboring chunks)

### 2. Metadata Enhancement
- [x] Add semantic tags/keywords extraction for each chunk
- [x] Include confidence scores for transcription segments
- [x] Add topic detection and classification
- [x] Generate document summary in metadata header
- [x] Extract and highlight key entities (names, places, dates, technical terms)

### 3. Structured Output Formats
- [ ] Add JSON-LD output with semantic markup
- [x] Implement hierarchical document structure (sections, subsections)
- [ ] Create standalone chunk files for large documents
- [x] Add cross-reference links between related chunks

### 4. Search Optimization
- [ ] Pre-compute embeddings for chunks (optional)
- [ ] Add phonetic representations for better search matching
- [ ] Generate alternative phrasings for technical terms
- [ ] Create inverted index metadata file

### 5. Context Preservation
- [x] Add document-level context to each chunk
- [x] Include temporal context (before/after summaries)
- [ ] Preserve speaker information in chunks
- [x] Add discourse markers and transition indicators

### 6. Quality Indicators
- [x] Add audio quality score to output
- [x] Flag low-confidence transcription segments
- [ ] Include silence/noise ratio metrics
- [x] Mark potential transcription errors for review

### 7. RAGflow-Specific Features
- [x] Add RAGflow-compatible frontmatter
- [x] Generate chunk IDs compatible with RAGflow indexing
- [ ] Create manifest file for batch imports
- [ ] Support RAGflow's document versioning scheme

## Implementation Notes

- Always test with actual RAG tools to ensure compatibility
- Consider the trade-off between chunk size and context preservation
- Optimize for both semantic search and keyword search
- Maintain backward compatibility with existing output formats