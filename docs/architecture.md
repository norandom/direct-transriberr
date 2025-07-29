# Direct Transcriber - Architecture & Code Structure

## Overview

The Direct Transcriber follows a modular architecture designed for extensibility, testability, and maintainability. The system is organized into distinct layers with clear responsibilities.

## Directory Structure

```
direct-transcriber/
├── src/
│   └── direct_transcriber/
│       ├── __init__.py
│       ├── cli.py                 # CLI entry point and command definitions
│       ├── config/                # Configuration management
│       │   ├── __init__.py
│       │   ├── settings.py        # Settings model and validation
│       │   ├── loader.py          # Config file loading
│       │   └── defaults.py        # Default configuration values
│       ├── core/                  # Core business logic
│       │   ├── __init__.py
│       │   ├── transcriber.py     # Abstract transcriber interface
│       │   ├── whisper_transcriber.py  # Whisper implementation
│       │   ├── batch_processor.py # Batch processing orchestration
│       │   └── models.py          # Domain models (TranscriptionResult, etc.)
│       ├── media/                 # Media handling
│       │   ├── __init__.py
│       │   ├── extractor.py       # Audio extraction from video
│       │   ├── validator.py       # File validation
│       │   ├── analyzer.py        # Duration estimation, format detection
│       │   └── cache.py           # Extracted audio caching
│       ├── output/                # Output formatting
│       │   ├── __init__.py
│       │   ├── base.py            # Abstract formatter interface
│       │   ├── markdown.py        # Markdown formatter
│       │   ├── json_formatter.py  # JSON formatter
│       │   ├── rag_optimizer.py   # RAG-specific optimizations
│       │   └── chunking.py        # Intelligent chunking strategies
│       ├── analysis/              # Content analysis
│       │   ├── __init__.py
│       │   ├── metadata.py        # Metadata extraction
│       │   ├── quality.py         # Quality scoring
│       │   ├── entities.py        # Entity extraction
│       │   └── keywords.py        # Keyword extraction
│       ├── utils/                 # Utilities
│       │   ├── __init__.py
│       │   ├── memory.py          # Memory management
│       │   ├── progress.py        # Progress tracking
│       │   ├── logging.py         # Structured logging
│       │   └── errors.py          # Custom exceptions
│       └── plugins/               # Plugin system
│           ├── __init__.py
│           ├── base.py            # Plugin interface
│           └── registry.py        # Plugin registration
├── tests/                         # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/                          # Documentation
│   ├── architecture.md
│   ├── api/
│   └── guides/
├── scripts/                       # Utility scripts
├── docker/                        # Docker configurations
│   ├── Dockerfile
│   ├── Dockerfile.light
│   └── entrypoint.sh
└── config/                        # Configuration files
    ├── default.yaml
    └── example.yaml
```

## Core Components

### 1. Configuration Layer (`config/`)

**Responsibilities:**
- Load and validate configuration from multiple sources (files, env vars, CLI args)
- Provide typed configuration objects
- Support configuration inheritance and overrides

**Key Classes:**
```python
# settings.py
class TranscriberSettings:
    model: str
    device: str
    language: Optional[str]
    
class OutputSettings:
    format: str
    chunk_size: Optional[int]
    include_timestamps: bool
    
class Settings:
    transcriber: TranscriberSettings
    output: OutputSettings
    processing: ProcessingSettings
```

### 2. Core Business Logic (`core/`)

**Responsibilities:**
- Define abstract interfaces for transcription
- Implement transcription strategies
- Orchestrate batch processing

**Key Interfaces:**
```python
# transcriber.py
class TranscriberInterface(ABC):
    @abstractmethod
    async def transcribe(self, audio_path: Path) -> TranscriptionResult:
        pass
    
    @abstractmethod
    def estimate_memory_usage(self) -> int:
        pass

# models.py
@dataclass
class TranscriptionResult:
    text: str
    segments: List[Segment]
    metadata: TranscriptionMetadata
    confidence: float
    language: str
```

### 3. Media Handling (`media/`)

**Responsibilities:**
- Extract audio from various formats
- Validate media files
- Cache extracted audio
- Analyze media properties

**Key Classes:**
```python
# extractor.py
class MediaExtractor:
    def extract_audio(self, input_path: Path) -> Path:
        """Extract audio, return path to WAV file"""
        
# validator.py
class MediaValidator:
    def validate(self, file_path: Path) -> ValidationResult:
        """Check if file is valid and processable"""
```

### 4. Output Formatting (`output/`)

**Responsibilities:**
- Format transcription results for different use cases
- Implement RAG-optimized output strategies
- Handle intelligent chunking

**Key Classes:**
```python
# base.py
class FormatterInterface(ABC):
    @abstractmethod
    def format(self, result: TranscriptionResult, options: Dict) -> str:
        pass

# rag_optimizer.py
class RAGOptimizer:
    def optimize_for_retrieval(self, result: TranscriptionResult) -> RAGOptimizedResult:
        """Apply RAG-specific optimizations"""
```

### 5. Content Analysis (`analysis/`)

**Responsibilities:**
- Extract metadata and entities
- Score transcription quality
- Generate keywords and summaries

**Key Classes:**
```python
# metadata.py
class MetadataExtractor:
    def extract(self, result: TranscriptionResult) -> DocumentMetadata:
        """Extract comprehensive metadata"""

# quality.py
class QualityAnalyzer:
    def analyze(self, result: TranscriptionResult) -> QualityScore:
        """Assess transcription quality"""
```

## Design Patterns

### 1. Strategy Pattern
Used for transcription engines and output formatters to allow easy swapping of implementations.

### 2. Factory Pattern
For creating appropriate transcriber instances based on configuration.

### 3. Chain of Responsibility
For processing pipeline (validation → extraction → transcription → analysis → formatting).

### 4. Observer Pattern
For progress tracking and event handling during batch processing.

### 5. Plugin Architecture
Allows extending functionality without modifying core code.

## Data Flow

```
Input File → Validation → Media Extraction → Transcription → Analysis → Formatting → Output
                ↓                ↓                 ↓            ↓           ↓
             [Cache]         [Progress]       [Metadata]   [Quality]   [Chunking]
```

## Error Handling Strategy

1. **Validation Errors**: Caught early, logged, allow batch to continue
2. **Transcription Errors**: Retry with backoff, fallback to simpler model
3. **System Errors**: Graceful degradation, state preservation for resume
4. **Resource Errors**: Memory monitoring, automatic model downgrade

## Extension Points

1. **Custom Transcribers**: Implement `TranscriberInterface`
2. **Output Formats**: Implement `FormatterInterface`
3. **Analysis Modules**: Add to `analysis/` package
4. **Media Handlers**: Extend `MediaExtractor` for new formats
5. **Chunking Strategies**: Implement `ChunkingStrategy` interface

## Configuration Hierarchy

```
1. Default configuration (built-in)
2. System configuration (/etc/direct-transcriber/config.yaml)
3. User configuration (~/.direct-transcriber/config.yaml)
4. Project configuration (./transcriber.yaml)
5. Environment variables (DT_*)
6. Command-line arguments
```

## Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete transcription workflows
- **Performance Tests**: Benchmark memory usage and speed
- **Property Tests**: Test chunking and formatting algorithms