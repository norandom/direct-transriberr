"""Command-line interface for direct transcriber."""

import sys
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table
from rich.prompt import Confirm

from .memory import get_system_memory, select_best_model, get_model_info, setup_cpu_optimization
from .transcriber import LocalTranscriber, get_media_files
from .formatter import MarkdownFormatter

console = Console()


@click.group()
@click.version_option()
def cli():
    """Direct Transcriber - Local CPU-only batch audio transcription tool."""
    pass


@cli.command()
@click.argument('input_path', type=click.Path(exists=True, path_type=Path))
@click.option('--output-dir', '-o', type=click.Path(path_type=Path), 
              help='Output directory for transcriptions')
@click.option('--model', '-m', type=click.Choice(['tiny', 'base', 'small', 'medium', 'large-v3']),
              help='Whisper model to use (auto-detected if not specified)')
@click.option('--format', '-f', type=click.Choice(['md', 'json', 'both']), default='md',
              help='Output format')
@click.option('--timestamps', is_flag=True, help='Include timestamps in markdown')
@click.option('--chunk-size', type=int, help='Chunk size for RAG optimization (characters)')
@click.option('--workers', '-w', type=int, help='Number of parallel workers (auto-detected if not specified)')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation prompts')
def batch(input_path: Path, output_dir: Optional[Path], model: Optional[str], 
          format: str, timestamps: bool, chunk_size: Optional[int], 
          workers: Optional[int], yes: bool):
    """Batch transcribe audio files from INPUT_PATH directory."""
    
    # System resource detection
    console.print("🔍 Detecting system resources...")
    available_ram = get_system_memory()
    worker_count = setup_cpu_optimization()
    
    # Auto-select model if not specified
    if not model:
        model = select_best_model(available_ram)
    
    # Display system info
    model_desc, model_ram = get_model_info(model)
    
    table = Table(title="System Information")
    table.add_column("Resource", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Available RAM", f"{available_ram:.1f} GB")
    table.add_row("CPU Cores (usable)", f"{worker_count}")
    table.add_row("Selected Model", f"{model} ({model_desc})")
    table.add_row("Estimated RAM Usage", f"{model_ram:.1f} GB")
    table.add_row("GPU Mode", "❌ Disabled (CPU-only)")
    
    console.print(table)
    
    # Check if we have enough RAM
    if model_ram > available_ram * 0.8:
        console.print("⚠️  [yellow]Warning: Model may use more RAM than available[/yellow]")
        suggested_model = select_best_model(available_ram)
        if suggested_model != model:
            console.print(f"💡 Suggested model: {suggested_model}")
    
    # Get input files (don't create transcriber yet to avoid double model loading)
    if input_path.is_file():
        audio_files = [input_path]
        if not output_dir:
            output_dir = input_path.parent / "transcriptions"
    else:
        # Use standalone function to avoid loading model twice
        audio_files = get_media_files(input_path)
        if not output_dir:
            output_dir = input_path / "transcriptions"
    
    if not audio_files:
        console.print("❌ No audio or video files found")
        return
    
    # Count file types
    video_count = sum(1 for f in audio_files if f.suffix.lower() in {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'})
    audio_count = len(audio_files) - video_count
    
    file_summary = []
    if audio_count > 0:
        file_summary.append(f"{audio_count} audio files")
    if video_count > 0:
        file_summary.append(f"{video_count} video files")
    
    console.print(f"📁 Found {' and '.join(file_summary)} ({len(audio_files)} total)")
    
    # Confirm before processing
    if not yes:
        if not Confirm.ask(f"Continue with {model} model?"):
            console.print("Cancelled")
            return
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize transcriber and formatter
    transcriber = LocalTranscriber(model)
    formatter = MarkdownFormatter(include_timestamps=timestamps, chunk_size=chunk_size)
    
    # Process files with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
        disable=False,  # Force enable progress bar
    ) as progress:
        
        overall_task = progress.add_task("Overall Progress", total=len(audio_files))
        
        success_count = 0
        for i, file_path in enumerate(audio_files):
            console.print(f"🎬 Processing file {i+1}/{len(audio_files)}: {file_path.name}")
            file_task = progress.add_task(f"Processing {file_path.name}", total=100)
            
            try:
                # Transcribe file
                result = transcriber.transcribe_file(file_path, progress, file_task)
                
                if result:
                    # Generate output filename
                    base_name = file_path.stem
                    
                    # Save markdown
                    if format in ['md', 'both']:
                        md_path = output_dir / f"{base_name}.md"
                        formatter.format_transcription(result, md_path)
                        console.print(f"✅ Saved: {md_path}")
                    
                    # Save JSON
                    if format in ['json', 'both']:
                        json_path = output_dir / f"{base_name}.json"
                        formatter.save_json(result, json_path)
                        console.print(f"✅ Saved: {json_path}")
                    
                    success_count += 1
                else:
                    console.print(f"❌ Failed: {file_path}")
                
            except Exception as e:
                console.print(f"❌ Error processing {file_path}: {e}")
            
            progress.update(overall_task, advance=1)
            progress.remove_task(file_task)
    
    # Summary
    console.print(f"\n🎉 Completed: {success_count}/{len(audio_files)} files")
    console.print(f"📁 Output directory: {output_dir}")


@cli.command()
@click.argument('file_path', type=click.Path(exists=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), help='Output file path')
@click.option('--model', '-m', type=click.Choice(['tiny', 'base', 'small', 'medium', 'large-v3']),
              help='Whisper model to use (auto-detected if not specified)')
@click.option('--format', '-f', type=click.Choice(['md', 'json']), default='md',
              help='Output format')
@click.option('--timestamps', is_flag=True, help='Include timestamps in markdown')
def single(file_path: Path, output: Optional[Path], model: Optional[str], 
           format: str, timestamps: bool):
    """Transcribe a single audio file."""
    
    # Auto-select model if not specified
    if not model:
        available_ram = get_system_memory()
        model = select_best_model(available_ram)
        console.print(f"🎯 Auto-selected model: {model}")
    
    # Setup CPU optimization
    setup_cpu_optimization()
    
    # Initialize transcriber
    transcriber = LocalTranscriber(model)
    
    # Process file
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        
        task = progress.add_task(f"Processing {file_path.name}", total=100)
        result = transcriber.transcribe_file(file_path, progress, task)
    
    if not result:
        console.print("❌ Transcription failed")
        return
    
    # Generate output path if not specified
    if not output:
        output = file_path.parent / f"{file_path.stem}.{format}"
    
    # Save result
    if format == 'md':
        formatter = MarkdownFormatter(include_timestamps=timestamps)
        formatter.format_transcription(result, output)
    else:
        formatter = MarkdownFormatter()
        formatter.save_json(result, output)
    
    console.print(f"✅ Saved: {output}")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()