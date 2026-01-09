"""
P5.js WEBGL sketch to ASCII converter for dome projection.
Runs a p5.js WEBGL sketch in a headless browser, captures frames as PNG,
then converts them to ASCII output optimized for 2048x2048 dome projection.

This module provides a complete pipeline for converting p5.js WEBGL sketches
to ASCII art: it launches a headless browser, loads the HTML sketch, captures
frames at specified FPS, and converts them to ASCII art frames.

Author: ASCII Dome Project
Version: 1.0.0
Date: 2026-01-09
License: MIT

Usage:
    python p5_webgl_to_ascii.py /path/to/sketch/directory --chars chars_sorted/invisible_cities_expanded_sorted.json
    python p5_webgl_to_ascii.py /path/to/sketch.html --chars chars.json --frames 300 --fps 30
    python p5_webgl_to_ascii.py /path/to/sketch --chars chars.json --skip-png  # Only convert existing PNGs
    python p5_webgl_to_ascii.py /path/to/sketch --chars chars.json --skip-ascii  # Only capture PNGs

Dependencies:
    - playwright (required)
    - Pillow (PIL)
    - json, http.server (standard library)
    
Installation:
    pip install playwright pillow
    playwright install chromium
"""

import json
import argparse
import os
import time
import subprocess
import http.server
import socketserver
import threading
import tarfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Import playwright (required)
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

OUTPUT_SIZE = 2048

FONT_DIR = "/Users/adelinesetiawan/ASCII-dome/fonts"
FONTS = {
    "menlo": f"{FONT_DIR}/Menlo.ttc",
    "monaco": f"{FONT_DIR}/Monaco.ttf",
    "courier": f"{FONT_DIR}/Courier.ttc",
}


def load_characters(json_path):
    """Load character set from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get('characters', data.get('chars', ''))
    return ''.join(data) if isinstance(data, list) else data


def load_font(font_path, size):
    """Load font from path."""
    if font_path.endswith('.ttc'):
        return ImageFont.truetype(font_path, size, index=0)
    return ImageFont.truetype(font_path, size)


def get_font_metrics(font):
    """Get character width and height for font."""
    bbox = font.getbbox("W")
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def find_html_file(sketch_path):
    """
    Find the HTML file in a p5.js sketch directory or return the path if it's already an HTML file.
    
    Args:
        sketch_path (str): Path to sketch directory or HTML file
        
    Returns:
        str: Path to HTML file, or None if not found
    """
    path = Path(sketch_path)
    
    # If it's already an HTML file, return it
    if path.is_file() and path.suffix in ['.html', '.htm']:
        return str(path.absolute())
    
    # If it's a directory, look for index.html or sketch.html
    if path.is_dir():
        for name in ['index.html', 'sketch.html']:
            html_path = path / name
            if html_path.exists():
                return str(html_path.absolute())
    
    return None


def start_local_server(sketch_dir, port=8000):
    """
    Start a local HTTP server to serve the sketch files.
    
    Args:
        sketch_dir (str): Directory containing the sketch files
        port (int): Starting port number (will try next available if in use)
        
    Returns:
        tuple: (httpd, server_url)
    """
    sketch_dir = Path(sketch_dir).absolute()
    
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(sketch_dir), **kwargs)
    
    # Try to find an available port
    for attempt in range(10):
        try:
            httpd = socketserver.TCPServer(("", port), CustomHandler)
            break
        except OSError:
            port += 1
            if attempt == 9:
                raise Exception(f"Could not find available port after 10 attempts")
    
    def run_server():
        httpd.serve_forever()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(0.5)
    
    server_url = f"http://localhost:{port}"
    return httpd, server_url


def frame_to_ascii(pil_image, chars, cols, rows):
    """Convert PIL image to ASCII lines. Optimized for 30fps processing."""
    # Convert to grayscale and resize in one step for efficiency
    gray = pil_image.convert("L")
    resized = gray.resize((cols, rows), Image.Resampling.LANCZOS)
    
    # Get pixels as array for faster access
    pixels = list(resized.getdata())
    num_chars = len(chars)
    
    # Pre-calculate character mapping for performance
    char_map = [chars[min(int(p / 256 * num_chars), num_chars - 1)] for p in pixels]
    
    # Build ASCII lines efficiently
    ascii_lines = []
    for row in range(rows):
        start_idx = row * cols
        line = ''.join(char_map[start_idx:start_idx + cols])
        ascii_lines.append(line)

    return ascii_lines


def render_ascii_frame(ascii_lines, font, char_w, char_h):
    """Render ASCII lines to 2048x2048 PNG image. Optimized for 30fps processing."""
    # Create image with black background
    img = Image.new('RGB', (OUTPUT_SIZE, OUTPUT_SIZE), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Calculate text dimensions and centering offsets
    text_width = len(ascii_lines[0]) * char_w
    text_height = len(ascii_lines) * char_h
    x_offset = (OUTPUT_SIZE - text_width) // 2
    y_offset = (OUTPUT_SIZE - text_height) // 2

    # Render all lines efficiently (optimized for 30fps throughput)
    for i, line in enumerate(ascii_lines):
        draw.text((x_offset, y_offset + i * char_h), line, font=font, fill=(255, 255, 255))

    return img


def capture_frames_playwright(html_path, sketch_dir, output_dir, num_frames, fps, wait_time=2):
    """
    Capture frames from p5.js WEBGL sketch using the sketch's built-in recording (R/S keys).
    Waits for user to manually press R to start and S to stop recording.
    Uses a local HTTP server to serve the files.
    
    Args:
        html_path (str): Path to HTML file containing p5.js sketch
        sketch_dir (str): Directory containing the sketch files
        output_dir (str): Directory to save captured PNG frames
        num_frames (int): Number of frames to capture (informational only)
        fps (float): Frame rate for capture (informational only)
        wait_time (float): Seconds to wait for p5.js initialization (default: 2)
        
    Returns:
        str: Path to output directory containing captured frames
    """
    print(f"Waiting for manual recording (press R to start, S to stop)...")
    
    html_path = Path(html_path)
    sketch_dir = Path(sketch_dir)
    html_filename = html_path.name
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Start local HTTP server
    print("Starting local HTTP server...")
    httpd, server_url = start_local_server(str(sketch_dir))
    
    # Setup download path for tar file
    downloads_dir = Path.home() / "Downloads"
    tar_file = downloads_dir / "p5_frames.tar"
    
    # Remove existing tar file if it exists
    if tar_file.exists():
        tar_file.unlink()
    
    try:
        with sync_playwright() as p:
            # Launch browser (headless=False so user can interact)
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={'width': 2048, 'height': 2048},
                device_scale_factor=1,
                accept_downloads=True
            )
            page = context.new_page()
            
            # Load the HTML file via HTTP server
            html_url = f"{server_url}/{html_filename}"
            print(f"Loading: {html_url}")
            page.goto(html_url, wait_until='networkidle', timeout=30000)
            
            # Wait for p5.js to initialize
            print("Waiting for p5.js to initialize...")
            time.sleep(wait_time)
            
            # Wait for canvas to be ready
            try:
                page.wait_for_selector('canvas', timeout=10000)
                print("Canvas found!")
            except Exception as e:
                print(f"Warning: Canvas not found immediately: {e}")
                print("Continuing anyway...")
            
            print("\n" + "="*60)
            print("READY FOR RECORDING")
            print("="*60)
            print("Please interact with the browser window:")
            print("  1. Press 'R' in the browser to START recording")
            print("  2. Press 'S' in the browser to STOP recording")
            print("  3. The script will automatically detect when you stop")
            print("="*60 + "\n")
            
            # Wait for user to press S (which triggers download)
            print("Waiting for you to press 'S' to stop recording...")
            try:
                with page.expect_download(timeout=600000) as download_info:  # 10 minute timeout
                    # User will press S manually in browser
                    pass
                
                # Download detected (user pressed S)
                download = download_info.value
                download.save_as(str(tar_file))
                print(f"\nDownload detected! Downloaded: {tar_file}")
                
            except Exception as e:
                print(f"\nTimeout or error waiting for download: {e}")
                print("Make sure you pressed 'S' to stop recording in the browser.")
            
            # Give a moment for user to see the result, then close browser
            print("\nClosing browser in 2 seconds...")
            time.sleep(2)
            
            browser.close()
            
            # Extract tar file if it exists
            if tar_file.exists():
                print(f"\nExtracting tar file: {tar_file}")
                with tarfile.open(tar_file, 'r') as tar:
                    tar.extractall(output_dir)
                print(f"Extracted frames to '{output_dir}/'")
                
                # Clean up tar file
                tar_file.unlink()
                print("Cleaned up tar file")
            else:
                print(f"\nWarning: Tar file not found")
                print("Frames may not have been captured. Check browser console.")
    finally:
        # Shutdown server
        httpd.shutdown()
        httpd.server_close()
    
    # Count extracted frames
    png_files = list(Path(output_dir).glob('*.png'))
    print(f"\nExtracted {len(png_files)} frames to '{output_dir}/'")
    return output_dir


def convert_png_to_ascii(png_dir, chars, font, font_size, output_dir, target_fps=30.0):
    """
    Convert PNG frames to ASCII art frames. Optimized for 30fps processing.
    
    Processes all PNG files in the input directory, converts each to ASCII art
    using the provided character set and font, and renders to 2048x2048 PNG images.
    Includes performance tracking to monitor processing speed against target FPS.
    
    Args:
        png_dir (str): Directory containing input PNG frames
        chars (str): Sorted character string (dark to light)
        font (ImageFont): PIL ImageFont object for rendering
        font_size (int): Font size in points (for metrics calculation)
        output_dir (str): Directory to save ASCII frames
        target_fps (float): Target processing speed in fps (default: 30.0)
        
    Returns:
        str: Path to output directory containing ASCII frames
        
    Note:
        Prints performance metrics every 10 frames showing current and average FPS.
    """
    print(f"\nConverting PNG frames to ASCII (target: {target_fps} fps)...")
    
    # Get font metrics
    char_w, char_h = get_font_metrics(font)
    cols = OUTPUT_SIZE // char_w
    rows = OUTPUT_SIZE // char_h
    print(f"Grid: {cols}x{rows} characters")
    
    # Find all PNG files
    png_files = sorted(Path(png_dir).glob('*.png'))
    if not png_files:
        print(f"Error: No PNG files found in {png_dir}")
        return
    
    print(f"Found {len(png_files)} PNG files")
    os.makedirs(output_dir, exist_ok=True)
    
    # Performance tracking for 30fps
    start_time = time.time()
    frame_time_target = 1.0 / target_fps  # Target time per frame (33.33ms for 30fps)
    
    for i, png_path in enumerate(png_files):
        frame_start = time.time()
        
        # Load image
        pil_image = Image.open(png_path)
        
        # Convert to ASCII (optimized for 30fps)
        ascii_lines = frame_to_ascii(pil_image, chars, cols, rows)
        img = render_ascii_frame(ascii_lines, font, char_w, char_h)
        
        # Save ASCII frame
        output_path = os.path.join(output_dir, f'frame_{i:06d}.png')
        img.save(output_path, 'PNG')
        
        # Performance reporting
        frame_time = time.time() - frame_start
        current_fps = 1.0 / frame_time if frame_time > 0 else 0
        
        if (i + 1) % 10 == 0:
            elapsed = time.time() - start_time
            avg_fps = (i + 1) / elapsed if elapsed > 0 else 0
            status = "✓" if current_fps >= target_fps * 0.9 else "⚠"
            print(f"  {status} {i + 1}/{len(png_files)} frames | "
                  f"Current: {current_fps:.1f} fps | Avg: {avg_fps:.1f} fps")
    
    total_time = time.time() - start_time
    final_fps = len(png_files) / total_time if total_time > 0 else 0
    print(f"\nDone. {len(png_files)} ASCII frames saved to '{output_dir}/'")
    print(f"Processing speed: {final_fps:.1f} fps (target: {target_fps} fps)")
    return output_dir


def main():
    """
    Main entry point for p5.js WEBGL to ASCII conversion pipeline.
    
    Orchestrates the complete workflow:
    1. Captures PNG frames from p5.js WEBGL sketch using headless browser
    2. Converts PNG frames to ASCII art using sorted character set
    3. Renders ASCII frames as 2048x2048 PNG images for dome projection
    
    Command-line arguments:
        input: Path to HTML file containing p5.js WEBGL sketch (required)
        --chars: Path to JSON file with sorted characters (required)
        --font: Font name (menlo, monaco, courier) or path (default: menlo)
        --font-size: Font size in points (default: 10)
        --frames: Number of frames to capture (default: 300)
        --fps: Frame rate for capture and processing (default: 30.0)
        --wait: Seconds to wait for p5.js initialization (default: 2.0)
        --png-output: Directory for temporary PNG frames (default: p5_frames)
        --output: Directory for final ASCII frames (default: ascii_frames/p5_webgl)
        --video-output: Output video file path (default: auto-generated from input name)
        --skip-png: Skip PNG capture, only convert existing PNGs (flag)
        --skip-ascii: Skip ASCII conversion, only capture PNGs (flag)
        --skip-video: Skip video creation, only create PNG frames (flag)
        
    Output:
        Creates directories with frame_000000.png, frame_000001.png, etc.
        Automatically creates MP4 video with naming: input_ascii.mp4
        Video is saved in the output directory (or specified --video-output path)
        
    Note:
        Requires either 'playwright' or 'selenium' to be installed.
        Playwright is recommended for better performance and reliability.
    """
    parser = argparse.ArgumentParser(
        description='P5.js WEBGL sketch to ASCII converter for dome projection'
    )
    parser.add_argument('input', help='Input p5.js sketch directory or HTML file')
    parser.add_argument('--chars', required=True, help='Sorted characters JSON file')
    parser.add_argument('--font', default='menlo', help='Font name (menlo, monaco, courier) or path')
    parser.add_argument('--font-size', type=int, default=10, help='Font size (default: 10)')
    parser.add_argument('--frames', type=int, default=300, help='Number of frames to capture (default: 300)')
    parser.add_argument('--fps', type=float, default=30.0, help='FPS for capture (default: 30)')
    parser.add_argument('--wait', type=float, default=2.0, help='Wait time for p5.js to initialize (default: 2 seconds)')
    parser.add_argument('--png-output', default='p5_frames', help='Temporary PNG output directory')
    parser.add_argument('--output', default='ascii_frames/p5_webgl', help='Final ASCII output directory')
    parser.add_argument('--video-output', help='Output video file path (default: auto-generated from input name)')
    parser.add_argument('--skip-png', action='store_true', help='Skip PNG capture, only convert existing PNGs')
    parser.add_argument('--skip-ascii', action='store_true', help='Skip ASCII conversion, only capture PNGs')
    parser.add_argument('--skip-video', action='store_true', help='Skip video creation, only create PNG frames')
    args = parser.parse_args()
    
    # Find HTML file
    html_path = find_html_file(args.input)
    if not html_path:
        print(f"Error: Could not find HTML file in {args.input}")
        print("  Looking for: index.html, sketch.html, or any .html file")
        return
    
    print(f"Found HTML file: {html_path}")
    
    # Check for required libraries
    if not args.skip_png:
        if not HAS_PLAYWRIGHT:
            print("Error: 'playwright' is required")
            print("Install with: pip install playwright")
            print("Then run: playwright install chromium")
            return
    
    # Load characters
    if not args.skip_ascii:
        chars = load_characters(args.chars)
        if not chars:
            print("Error: No characters loaded")
            return
        print(f"Loaded {len(chars)} characters: {chars[:20]}...")
        
        # Load font
        font_path = FONTS.get(args.font.lower(), args.font)
        font = load_font(font_path, args.font_size)
        print(f"Font: {font_path}")
    
    # Step 1: Capture PNG frames from p5.js sketch
    if not args.skip_png:
        if not os.path.exists(html_path):
            print(f"Error: HTML file not found: {html_path}")
            return
        
        print(f"\n{'='*60}")
        print("STEP 1: Capturing PNG frames from p5.js WEBGL sketch")
        print(f"{'='*60}")
        
        # Get sketch directory (parent of HTML file)
        sketch_dir = str(Path(html_path).parent)
        
        capture_frames_playwright(
            html_path,
            sketch_dir,
            args.png_output,
            args.frames,
            args.fps,
            args.wait
        )
    
    # Step 2: Convert PNG frames to ASCII
    if not args.skip_ascii:
        print(f"\n{'='*60}")
        print("STEP 2: Converting PNG frames to ASCII")
        print(f"{'='*60}")
        
        convert_png_to_ascii(
            args.png_output,
            chars,
            font,
            args.font_size,
            args.output,
            args.fps
        )
        
        print(f"\n{'='*60}")
        print("COMPLETE!")
        print(f"{'='*60}")
        print(f"ASCII frames saved to: {args.output}/")
        
        # Automatically create video from ASCII frames
        if not args.skip_video:
            # Generate output video filename
            if args.video_output:
                video_output = args.video_output
            else:
                # Create filename based on HTML file: sketch.html -> sketch_ascii.mov
                html_path_obj = Path(html_path)
                video_output = html_path_obj.stem + '_ascii.mov'
                # Save in same directory as output frames
                video_output = os.path.join(args.output, video_output)
            
            print(f"\nCreating video: {video_output}")
            
            # Check if ffmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], 
                             capture_output=True, 
                             check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Error: ffmpeg not found. Please install ffmpeg to create video.")
                print(f"  Install: brew install ffmpeg  (macOS)")
                print(f"  Or run manually:")
                print(f"  cd {args.output} && ffmpeg -framerate {args.fps:.0f} -pattern_type glob -i '*.png' -c:v prores_ks -profile:v 2 -pix_fmt yuv422p10le {video_output}")
            else:
                # Run ffmpeg to create video (ProRes high quality)
                # Change to frames directory for glob pattern
                original_dir = os.getcwd()
                os.chdir(args.output)
                
                # Get just the filename for output (since we're in the frames directory)
                video_filename = os.path.basename(video_output)
                
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-y',  # Overwrite output file if it exists
                    '-framerate', str(int(args.fps)),
                    '-pattern_type', 'glob',
                    '-i', '*.png',
                    '-c:v', 'prores_ks',
                    '-profile:v', '2',
                    '-pix_fmt', 'yuv422p10le',
                    video_filename
                ]
                
                try:
                    result = subprocess.run(ffmpeg_cmd, 
                                          capture_output=True, 
                                          text=True,
                                          check=True)
                    # Change back to original directory
                    os.chdir(original_dir)
                    print(f"✓ Video created successfully: {video_output}")
                    file_size = os.path.getsize(video_output) / (1024 * 1024)  # MB
                    print(f"  File size: {file_size:.1f} MB")
                except subprocess.CalledProcessError as e:
                    # Change back to original directory even on error
                    os.chdir(original_dir)
                    print(f"Error creating video: {e}")
                    print(f"  stderr: {e.stderr}")
                    print(f"\n  You can create it manually with:")
                    print(f"  cd {args.output} && ffmpeg -framerate {args.fps:.0f} -pattern_type glob -i '*.png' -c:v prores_ks -profile:v 2 -pix_fmt yuv422p10le {video_filename}")
        else:
            print(f"\nSkipping video creation (--skip-video flag set)")
            print(f"  To create video manually:")
            print(f"  cd {args.output} && ffmpeg -framerate {args.fps:.0f} -pattern_type glob -i '*.png' -c:v prores_ks -profile:v 2 -pix_fmt yuv422p10le output.mov")
    else:
        print(f"\nPNG frames saved to: {args.png_output}/")
        print("Use --skip-png to convert these to ASCII later")


if __name__ == "__main__":
    main()

