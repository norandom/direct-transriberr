# Direct Transcriber

A local CPU-only batch audio transcription tool optimized for RAGflow integration. Uses OpenAI Whisper models running entirely on your machine - no data leaves your system.

## Features

- **100% Local Processing** - No external API calls, all processing on CPU
- **Automatic Model Selection** - Detects available RAM and suggests optimal Whisper model
- **Batch Processing** - Process entire directories of audio files
- **RAGflow Optimized** - Markdown output with metadata and chunking options
- **Progress Tracking** - Rich progress bars for individual files and batches
- **Multi-format Support** - Handles audio (MP3, WAV, M4A, FLAC, OGG, WMA, AAC) and video (MP4, AVI, MOV, MKV, WMV, FLV, WebM, M4V)
- **Memory Safe** - Monitors system resources and prevents OOM errors

## Installation

### Option 1: Pre-built Docker Images (Recommended)

**Using GitHub Container Registry (fastest):**
```bash
# Use pre-built images - no build required!
docker run --rm -v ./input:/input -v ./output:/output -v ./models:/models \
  ghcr.io/user/direct-transcriber:latest \
  direct-transcriber batch /input --output-dir /output --yes

# Or with docker-compose
curl -O https://raw.githubusercontent.com/user/direct-transcriber/main/docker-compose.ghcr.yml
docker-compose -f docker-compose.ghcr.yml up
```

### Option 2: Local Docker Build

```bash
# Clone repository
git clone https://github.com/norandom/direct-transriberr
cd direct-transcriber

# Build and run with Docker Compose
docker-compose up --build
```

### Option 3: Python Installation

**Requirements:**
- Python 3.9+
- FFmpeg (for audio processing)
- uv (for dependency management)

**Install with uv:**
```bash
# Clone repository
git clone https://github.com/norandom/direct-transriberr
cd direct-transcriber

# Install with uv
uv pip install -e .
```

**System Dependencies:**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**CentOS/RHEL:**
```bash
sudo yum install ffmpeg
```

## Usage

### Docker Usage (Recommended)

**Using the helper script for external files:**

```bash
# Batch process external directory
./scripts/transcribe-external.sh -m /path/to/your/media -o /path/to/output

# Single external file
./scripts/transcribe-external.sh -f /path/to/video.mp4 -o /path/to/output

# With specific model
./scripts/transcribe-external.sh -m /path/to/media -o /path/to/output --model large-v3
```

**Direct Docker Compose usage:**

```bash
# Copy files to input directory
cp /path/to/your/media/* ./input/

# Run transcription (models will be downloaded to ./models on first run)
docker-compose up --build

# For external directories, set environment variables
MEDIA_DIR=/path/to/your/media OUTPUT_DIR=/path/to/output docker-compose --profile external up --build transcriber-external
```

### Python/uv Usage

**Prerequisites:**
```bash
# Activate the virtual environment
source .venv/bin/activate
```

**Batch Processing:**

```bash
# Process all audio and video files in a directory
direct-transcriber batch /path/to/media/files/

# With custom output directory
direct-transcriber batch /audio/ --output-dir /transcriptions/

# Force specific model
direct-transcriber batch /audio/ --model large-v3

# Include timestamps for reference
direct-transcriber batch /audio/ --timestamps

# Chunk output for better RAG performance
direct-transcriber batch /audio/ --chunk-size 500

# Save both markdown and JSON
direct-transcriber batch /audio/ --format both
```

**Single File:**

```bash
# Transcribe single audio file
direct-transcriber single audio.mp3

# Transcribe single video file (extracts audio automatically)
direct-transcriber single video.mp4

# With custom output  
direct-transcriber single media.mp4 --output transcript.md

# JSON output
direct-transcriber single media.mp4 --format json

# RAG-optimized output with intelligent chunking
direct-transcriber single media.mp4 --rag-optimized --chunking-strategy semantic

# Fixed-size chunking for consistent chunk sizes
direct-transcriber single media.mp4 --rag-optimized --chunking-strategy fixed --chunk-size 1000

# Example: Process a video segment with medium model and RAG optimization
direct-transcriber single test_5min.mp4 --model medium --rag-optimized --chunking-strategy semantic --output test_5min_medium.md
```

### Command Options

- `--model, -m`: Whisper model (tiny, base, small, medium, large-v3)
- `--output-dir, -o`: Output directory for batch processing
- `--format, -f`: Output format (md, json, both)
- `--timestamps`: Include timestamps in markdown
- `--chunk-size`: Chunk size for RAG optimization (characters)
- `--rag-optimized`: Enable RAG-optimized output with intelligent chunking
- `--chunking-strategy`: Chunking strategy (semantic, sentence, fixed)
- `--workers, -w`: Number of parallel workers (auto-detected)
- `--yes, -y`: Skip confirmation prompts

## Model Selection

The tool automatically selects the best Whisper model based on available RAM:

| Model | RAM Required | Quality | Speed |
|-------|-------------|---------|--------|
| tiny | 1 GB | Lowest | Fastest |
| base | 1.5 GB | Good | Fast |
| small | 2 GB | Better | Moderate |
| medium | 4 GB | High | Slower |
| large-v3 | 6 GB | Best | Slowest |

## Output Formats

### Clean Markdown (Default)
```markdown
# Video Transcription
**File:** `/full/path/to/video/meeting.mp4`
**Duration:** 15:32 | **Model:** large-v3 | **Language:** en
**Source:** video | **Transcribed:** 2024-01-15 14:30:22

---

The speaker discusses the importance of machine learning in modern applications. They explain how neural networks can be trained to recognize patterns in data.

Another topic covered is the implementation of transformer models for natural language processing tasks.
```

### With Timestamps
```markdown
# Audio Transcription
**File:** `/full/path/to/audio/meeting.mp3`

## [00:00] - [02:15]
The speaker discusses the importance of machine learning in modern applications.

## [02:15] - [04:30]
They explain how neural networks can be trained to recognize patterns in data.
```

### Chunked for RAG
```markdown
# Audio Transcription
**File:** `/full/path/to/audio/meeting.mp3`

## Segment 1 (00:00-05:00)
[Content chunk optimized for semantic search]

## Segment 2 (05:00-10:00)
[Next semantic chunk]
```

## Docker Image

### Optimized Container

The Docker image uses a multi-stage build process to minimize size while maintaining full functionality:

- **Base**: Python 3.11-slim for minimal footprint
- **Size**: ~800MB (compared to 2GB+ for standard PyTorch images)
- **Security**: Runs as non-root user
- **Optimization**: Removes test files, caches, and unnecessary components

### Available Tags

- `ghcr.io/norandom/direct-transriberr:latest` - Latest stable release
- `ghcr.io/norandom/direct-transriberr:main` - Latest development build
- `ghcr.io/norandom/direct-transriberr:v1.0.0` - Specific version tags

## Docker Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# External media directory (absolute path)
MEDIA_DIR=/path/to/your/media/files

# Output directory for transcriptions (absolute path)
OUTPUT_DIR=/path/to/your/transcriptions

# Model to use (optional, auto-detected if not specified)
WHISPER_MODEL=large-v3

# Memory limit for container (optional)
MEMORY_LIMIT=8G
```

### Volume Mounting

The Docker setup supports several volume mounting options:

1. **Default directories**: `./input`, `./output`, and `./models`
2. **Environment variables**: Use `MEDIA_DIR` and `OUTPUT_DIR`
3. **Single file mounting**: Mount specific files for transcription
4. **External script**: Use `scripts/transcribe-external.sh` for easy external file processing
5. **Persistent model storage**: Models are downloaded once to `./models` and reused

## Performance

- **CPU Optimization**: Uses available CPU cores minus 1 for system
- **Memory Management**: Monitors RAM usage and prevents OOM
- **Batch Processing**: Processes multiple files with progress tracking
- **Format Support**: Automatic audio format conversion via FFmpeg
- **Docker Isolation**: Containerized processing with resource limits
- **Model Persistence**: Whisper models downloaded once and cached in `./models`
- **Enhanced Progress**: Detailed progress tracking with processing times
- **CPU Optimized**: FP16 warnings suppressed, CPU-specific optimizations

## RAG Optimization Features

Direct Transcriber now includes advanced RAG (Retrieval-Augmented Generation) optimizations:

### Intelligent Chunking Strategies

**Semantic Chunking (Recommended):**
- Breaks content at natural topic boundaries
- Detects discourse markers and transitions
- Preserves context and meaning
- Ideal for complex discussions and lectures

**Sentence Chunking:**
- Groups sentences into coherent chunks
- Respects sentence boundaries
- Good for clear, structured speech
- Maintains readability

**Fixed-Size Chunking:**
- Consistent chunk sizes with smart overlap
- Predictable for downstream processing
- Good for batch processing workflows

### Enhanced Metadata Extraction

- **Keyword Extraction**: Automatic identification of key terms
- **Entity Recognition**: Names, numbers, times, and proper nouns
- **Topic Classification**: Domain-specific topic identification
- **Quality Scoring**: Confidence-based chunk quality assessment
- **Context Linking**: Inter-chunk relationships and context

### RAG-Optimized Output

```bash
# Enable RAG optimization
direct-transcriber batch /audio --rag-optimized

# Choose chunking strategy
direct-transcriber batch /audio --rag-optimized --chunking-strategy semantic

# Custom chunk size
direct-transcriber batch /audio --rag-optimized --chunk-size 1500
```

**Output Features:**
- Structured markdown with semantic sections
- JSON sidecar files for programmatic access
- Cross-chunk context preservation
- Quality metrics and confidence scores
- Entity and keyword extraction
- Topic classification

**Example RAG Output:**
```markdown
# Audio Transcription (RAG Optimized)
**Chunks:** 15 | **Strategy:** SemanticChunking

## Segment 1 (00:00 - 02:30)
**ID:** `lecture_001` | **Quality:** 0.92 | **Topics:** technology, AI

The speaker discusses machine learning fundamentals...

🏷️ **Entities:** Neural Networks, Deep Learning, PyTorch
```

### Integration Benefits

- **Better Retrieval**: Semantic chunks improve search relevance
- **Context Preservation**: Overlapping chunks maintain continuity
- **Quality Filtering**: Low-confidence segments are flagged
- **Structured Data**: JSON output enables programmatic processing
- **Metadata Rich**: Enhanced information for better indexing

## License

MIT License - see LICENSE file for details.
