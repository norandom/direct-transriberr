# Migration Plan: Current → Target Architecture

## Overview

This document outlines the step-by-step migration from the current simple structure to the proposed modular architecture while maintaining backward compatibility.

## Current Structure

```
src/direct_transcriber/
├── __init__.py
├── cli.py         # 228 lines - CLI, main logic, orchestration
├── transcriber.py # 153 lines - Transcription, media handling
├── formatter.py   # 162 lines - Output formatting
└── memory.py      # 59 lines - System resource management
```

## Migration Phases

### Phase 1: Core Refactoring (Priority: High)

**Goal**: Extract core abstractions without breaking existing functionality

1. **Create Core Module**
   ```python
   # core/models.py - Extract data models
   @dataclass
   class Segment:
       start: float
       end: float
       text: str
       confidence: float = 1.0
   
   @dataclass
   class TranscriptionMetadata:
       file_path: str
       duration: float
       model: str
       language: str
       source_type: str
       transcribed_at: datetime
   
   @dataclass
   class TranscriptionResult:
       text: str
       segments: List[Segment]
       metadata: TranscriptionMetadata
   ```

2. **Extract Media Handling**
   ```python
   # media/extractor.py - Move from transcriber.py
   class MediaExtractor:
       def extract_audio(self, input_path: Path, output_path: Path) -> bool
       def get_duration(self, file_path: Path) -> float
   
   # media/validator.py - New functionality
   class MediaValidator:
       def is_supported_format(self, file_path: Path) -> bool
       def validate_file(self, file_path: Path) -> ValidationResult
   ```

3. **Create Abstract Interfaces**
   ```python
   # core/transcriber.py
   class TranscriberInterface(ABC):
       @abstractmethod
       def transcribe(self, audio_path: Path) -> TranscriptionResult
   
   # output/base.py
   class FormatterInterface(ABC):
       @abstractmethod
       def format(self, result: TranscriptionResult) -> str
   ```

### Phase 2: Configuration System (Priority: High)

**Goal**: Centralize configuration management

1. **Create Configuration Module**
   ```python
   # config/settings.py
   class Settings:
       @classmethod
       def load(cls) -> 'Settings':
           # Load from files, env vars, etc.
   ```

2. **Migrate Hard-coded Values**
   - Move model configurations to settings
   - Extract file format lists to config
   - Centralize resource limits

### Phase 3: Enhanced Output System (Priority: Medium)

**Goal**: Implement RAG-optimized output

1. **Chunking System**
   ```python
   # output/chunking.py
   class ChunkingStrategy(ABC):
       @abstractmethod
       def chunk(self, result: TranscriptionResult) -> List[Chunk]
   
   class SemanticChunking(ChunkingStrategy):
       # Implement intelligent chunking
   ```

2. **RAG Optimizer**
   ```python
   # output/rag_optimizer.py
   class RAGOptimizer:
       def add_metadata(self, chunk: Chunk) -> EnhancedChunk
       def generate_embeddings(self, chunk: Chunk) -> Embeddings
   ```

### Phase 4: Analysis Pipeline (Priority: Medium)

**Goal**: Add content analysis capabilities

1. **Quality Analysis**
   ```python
   # analysis/quality.py
   class QualityAnalyzer:
       def score_confidence(self, result: TranscriptionResult) -> float
       def identify_issues(self, result: TranscriptionResult) -> List[Issue]
   ```

2. **Metadata Extraction**
   ```python
   # analysis/metadata.py
   class MetadataExtractor:
       def extract_entities(self, text: str) -> List[Entity]
       def generate_keywords(self, text: str) -> List[str]
   ```

### Phase 5: Error Handling & Resilience (Priority: High)

**Goal**: Implement robust error handling

1. **Custom Exceptions**
   ```python
   # utils/errors.py
   class TranscriptionError(Exception): pass
   class MediaError(TranscriptionError): pass
   class ModelLoadError(TranscriptionError): pass
   ```

2. **Retry Logic**
   ```python
   # utils/retry.py
   class RetryHandler:
       def with_retry(self, func, max_attempts=3)
   ```

### Phase 6: Testing Infrastructure (Priority: High)

**Goal**: Comprehensive test coverage

1. **Unit Tests**
   - Test each module in isolation
   - Mock external dependencies

2. **Integration Tests**
   - Test complete workflows
   - Use sample media files

## Implementation Order

1. **Week 1-2**: Core refactoring (Phase 1)
   - Extract models and interfaces
   - Refactor without changing behavior
   - Maintain CLI compatibility

2. **Week 3**: Configuration system (Phase 2)
   - Implement settings management
   - Add configuration file support
   - Keep command-line arguments working

3. **Week 4**: Error handling (Phase 5)
   - Add retry logic
   - Improve error messages
   - Add logging

4. **Week 5-6**: RAG optimizations (Phase 3)
   - Implement chunking strategies
   - Add metadata enhancement
   - Create specialized formatters

5. **Week 7**: Analysis pipeline (Phase 4)
   - Add quality scoring
   - Implement entity extraction
   - Generate keywords

6. **Week 8**: Testing and documentation (Phase 6)
   - Write comprehensive tests
   - Update documentation
   - Create migration guide

## Backward Compatibility

### CLI Compatibility
```bash
# Old command (still works)
direct-transcriber batch /input --model large-v3

# New command (additional features)
direct-transcriber batch /input --config config.yaml --profile rag-optimized
```

### Output Compatibility
- Default output format remains unchanged
- New formats available via configuration
- Existing integrations continue to work

## File Migration Map

| Current File | New Location(s) |
|-------------|----------------|
| `cli.py` | `cli.py` (simplified) + `core/batch_processor.py` |
| `transcriber.py` | `core/whisper_transcriber.py` + `media/extractor.py` |
| `formatter.py` | `output/markdown.py` + `output/json_formatter.py` |
| `memory.py` | `utils/memory.py` |

## Risk Mitigation

1. **Feature Flags**: Use flags to enable new features gradually
2. **Parallel Implementation**: Keep old code working while building new
3. **Incremental Migration**: Move one component at a time
4. **Comprehensive Testing**: Test each phase thoroughly
5. **Rollback Plan**: Tag releases for easy rollback

## Success Metrics

- All existing commands work without changes
- Test coverage > 80%
- No performance regression
- New features accessible via configuration
- Clear documentation for new capabilities