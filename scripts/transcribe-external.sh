#!/bin/bash

# Script to transcribe external files using Docker Compose

set -e

# Default values
MEDIA_DIR=""
OUTPUT_DIR=""
MODEL=""
SINGLE_FILE=""
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Help function
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Transcribe audio/video files using Docker Compose

OPTIONS:
    -m, --media-dir DIR      Directory containing media files (required)
    -o, --output-dir DIR     Output directory for transcriptions (required)
    -f, --file FILE          Single file to transcribe (optional)
    --model MODEL           Whisper model to use (tiny, base, small, medium, large-v3)
    -h, --help              Show this help message

EXAMPLES:
    # Batch process directory
    $0 -m /path/to/media -o /path/to/output

    # Single file
    $0 -f /path/to/video.mp4 -o /path/to/output

    # With specific model
    $0 -m /path/to/media -o /path/to/output --model large-v3

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--media-dir)
            MEDIA_DIR="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -f|--file)
            SINGLE_FILE="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$OUTPUT_DIR" ]]; then
    echo "Error: Output directory is required"
    show_help
    exit 1
fi

if [[ -z "$MEDIA_DIR" && -z "$SINGLE_FILE" ]]; then
    echo "Error: Either media directory or single file is required"
    show_help
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Handle single file processing
if [[ -n "$SINGLE_FILE" ]]; then
    if [[ ! -f "$SINGLE_FILE" ]]; then
        echo "Error: File '$SINGLE_FILE' not found"
        exit 1
    fi
    
    # Get directory and filename
    FILE_DIR=$(dirname "$SINGLE_FILE")
    FILE_NAME=$(basename "$SINGLE_FILE")
    FILE_BASE=$(basename "$SINGLE_FILE" | sed 's/\.[^.]*$//')
    
    echo "🎬 Transcribing single file: $SINGLE_FILE"
    echo "📁 Output directory: $OUTPUT_DIR"
    
    # Build docker run command
    DOCKER_CMD="docker run --rm -v \"$FILE_DIR\":/input:ro -v \"$OUTPUT_DIR\":/output -v \"$(pwd)/models\":/models -e WHISPER_MODEL_DIR=/models"
    
    # Add model if specified
    if [[ -n "$MODEL" ]]; then
        DOCKER_CMD="$DOCKER_CMD direct-transcriber single /input/$FILE_NAME --output /output/$FILE_BASE.md --model $MODEL"
    else
        DOCKER_CMD="$DOCKER_CMD direct-transcriber single /input/$FILE_NAME --output /output/$FILE_BASE.md"
    fi
    
    # Build and run
    docker build -t direct-transcriber .
    eval $DOCKER_CMD
else
    # Batch processing
    if [[ ! -d "$MEDIA_DIR" ]]; then
        echo "Error: Media directory '$MEDIA_DIR' not found"
        exit 1
    fi
    
    echo "🎬 Transcribing directory: $MEDIA_DIR"
    echo "📁 Output directory: $OUTPUT_DIR"
    
    # Export environment variables
    export MEDIA_DIR
    export OUTPUT_DIR
    export WHISPER_MODEL="$MODEL"
    
    # Run with external profile
    docker-compose --profile external up --build transcriber-external
fi

echo "✅ Transcription completed!"
echo "📁 Check output directory: $OUTPUT_DIR"