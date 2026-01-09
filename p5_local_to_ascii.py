"""
Local p5.js sketch to ASCII converter for dome projection.
Converts downloaded/local p5.js sketches to ASCII art frames and video.

This script is designed for local p5.js sketches (like those downloaded from p5.js editor):
1. Finds HTML file in the sketch directory
2. Captures frames from p5.js sketch in headless browser
3. Converts PNG frames to ASCII art using sorted character set
4. Renders ASCII frames as 2048x2048 PNG images
5. Creates MP4 video from ASCII frames

Author: ASCII Dome Project
Version: 1.0.0
Date: 2026-01-09
License: MIT

Usage:
    python p5_local_to_ascii.py /path/to/sketch/directory --chars chars_sorted/chars_standard.json
    python p5_local_to_ascii.py /path/to/sketch/directory --chars chars.json --frames 300 --fps 30

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


def load_characters(json_path):
    """
    Load character set from JSON file.
    
    Args:
        json_path (str): Path to JSON file containing character set
        
    Returns:
        str: String of characters sorted by brightness (dark to light)
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get('characters', data.get('chars', ''))
    return ''.join(data) if isinstance(data, list) else data


def load_font(font_path, size):
    """
    Load a font from file path.
    
    Args:
        font_path (str): Path to font file
        size (int): Font size in points
        
    Returns:
        ImageFont: PIL ImageFont object
    """
    if font_path.endswith('.ttc'):
        return ImageFont.truetype(font_path, size, index=0)
    return ImageFont.truetype(font_path, size)


def get_font_metrics(font):
    """
    Get character width and height metrics for a font.
    
    Args:
        font (ImageFont): PIL ImageFont object
        
    Returns:
        tuple: (char_width, char_height) in pixels
    """
    bbox = font.getbbox("W")
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def frame_to_ascii(pil_image, chars, cols, rows):
    """
    Convert a PIL image to ASCII art lines. Optimized for 30fps processing.
    
    Args:
        pil_image (PIL.Image): Input image (any color mode)
        chars (str): Sorted character string (dark to light)
        cols (int): Number of character columns (width)
        rows (int): Number of character rows (height)
        
    Returns:
        list: List of strings, each string is one row of ASCII characters
    """
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
    """
    Render ASCII text lines to a 2048x2048 PNG image. Optimized for 30fps processing.
    
    Args:
        ascii_lines (list): List of ASCII strings (one per row)
        font (ImageFont): PIL ImageFont object for rendering
        char_w (int): Character width in pixels
        char_h (int): Character height in pixels
        
    Returns:
        PIL.Image: 2048x2048 RGB image with ASCII text rendered in white
    """
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


def capture_frames_playwright(html_path, sketch_dir, output_dir, num_frames, fps, wait_time=3):
    """
    Capture frames from p5.js sketch using the sketch's built-in recording (R/S keys).
    Uses a local HTTP server to serve the files.
    
    Args:
        html_path (str): Path to HTML file containing p5.js sketch
        sketch_dir (str): Directory containing the sketch files
        output_dir (str): Directory to save captured PNG frames
        num_frames (int): Number of frames to capture
        fps (float): Frame rate for capture (frames per second)
        wait_time (float): Seconds to wait for p5.js initialization (default: 3)
        
    Returns:
        str: Path to output directory containing captured frames
    """
    print(f"Capturing {num_frames} frames using sketch recording (R/S keys)...")
    
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
            # Launch browser (headless=False to see recording indicator)
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
                print("Canvas found, starting recording...")
            except Exception as e:
                print(f"Warning: Canvas not found immediately: {e}")
                print("Continuing anyway...")
            
            # Press 'R' to start recording
            print("Pressing 'R' to start recording...")
            page.keyboard.press('r')
            time.sleep(0.5)  # Brief pause for recording to start
            
            # Calculate recording duration
            recording_duration = num_frames / fps
            print(f"Recording for {recording_duration:.1f} seconds ({num_frames} frames @ {fps} fps)...")
            
            # Wait for frames to be captured
            time.sleep(recording_duration + 1)  # Add 1 second buffer
            
            # Press 'S' to stop recording and wait for download
            print("Pressing 'S' to stop recording...")
            with page.expect_download(timeout=30000) as download_info:
                page.keyboard.press('s')
            
            # Save the downloaded file
            download = download_info.value
            download.save_as(str(tar_file))
            print(f"Downloaded: {tar_file}")
            
            browser.close()
            
            # Extract tar file if it exists
            if tar_file.exists():
                print(f"Extracting tar file: {tar_file}")
                with tarfile.open(tar_file, 'r') as tar:
                    tar.extractall(output_dir)
                print(f"Extracted frames to '{output_dir}/'")
                
                # Clean up tar file
                tar_file.unlink()
                print("Cleaned up tar file")
            else:
                print(f"Warning: Tar file not found")
                print("Frames may not have been captured. Check browser console.")
    finally:
        # Shutdown server
        httpd.shutdown()
        httpd.server_close()
    
    # Count extracted frames
    png_files = list(Path(output_dir).glob('*.png'))
    print(f"Extracted {len(png_files)} frames to '{output_dir}/'")
    return output_dir


def convert_png_to_ascii(png_dir, chars, font, font_size, output_dir, target_fps=30.0):
    """
    Convert PNG frames to ASCII art frames. Optimized for 30fps processing.
    
    Args:
        png_dir (str): Directory containing input PNG frames
        chars (str): Sorted character string (dark to light)
        font (ImageFont): PIL ImageFont object for rendering
        font_size (int): Font size in points (for metrics calculation)
        output_dir (str): Directory to save ASCII frames
        target_fps (float): Target processing speed in fps (default: 30.0)
        
    Returns:
        str: Path to output directory containing ASCII frames
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


def create_video_from_frames(frames_dir, output_video, fps):
    """
    Create MP4 video from PNG frames using ffmpeg.
    
    Args:
        frames_dir (str): Directory containing PNG frames
        output_video (str): Output video file path
        fps (float): Frame rate for video
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nCreating video: {output_video}")
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], 
                     capture_output=True, 
                     check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg not found. Please install ffmpeg to create video.")
        print(f"  Install: brew install ffmpeg  (macOS)")
        print(f"  Or run manually:")
        print(f"  ffmpeg -framerate {fps:.0f} -i {frames_dir}/frame_%06d.png -c:v libx264 -pix_fmt yuv420p {output_video}")
        return False
    
    # Run ffmpeg to create video
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file if it exists
        '-framerate', str(int(fps)),
        '-i', os.path.join(frames_dir, 'frame_%06d.png'),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        output_video
    ]
    
    try:
        result = subprocess.run(ffmpeg_cmd, 
                              capture_output=True, 
                              text=True,
                              check=True)
        print(f"✓ Video created successfully: {output_video}")
        file_size = os.path.getsize(output_video) / (1024 * 1024)  # MB
        print(f"  File size: {file_size:.1f} MB")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating video: {e}")
        print(f"  stderr: {e.stderr}")
        print(f"\n  You can create it manually with:")
        print(f"  ffmpeg -framerate {fps:.0f} -i {frames_dir}/frame_%06d.png -c:v libx264 -pix_fmt yuv420p {output_video}")
        return False


def main():
    """
    Main entry point for local p5.js sketch to ASCII conversion pipeline.
    
    Orchestrates the complete workflow:
    1. Finds HTML file in sketch directory
    2. Captures PNG frames from p5.js sketch using headless browser
    3. Converts PNG frames to ASCII art using sorted character set
    4. Renders ASCII frames as 2048x2048 PNG images for dome projection
    5. Creates MP4 video from ASCII frames
    
    Command-line arguments:
        sketch_path: Path to p5.js sketch directory or HTML file (required)
        --chars: Path to JSON file with sorted characters (required)
        --font: Font name (menlo, monaco, courier) or path (default: menlo)
        --font-size: Font size in points (default: 10)
        --frames: Number of frames to capture (default: 300)
        --fps: Frame rate for capture and processing (default: 30.0)
        --wait: Seconds to wait for p5.js to initialize (default: 3.0)
        --png-output: Directory for temporary PNG frames (default: p5_frames)
        --output: Directory for final ASCII frames (default: ascii_frames/p5_local)
        --video-output: Output video file path (default: auto-generated from sketch name)
        --skip-png: Skip PNG capture, only convert existing PNGs (flag)
        --skip-ascii: Skip ASCII conversion, only capture PNGs (flag)
        --skip-video: Skip video creation, only create PNG frames (flag)
    """
    parser = argparse.ArgumentParser(
        description='Local p5.js sketch to ASCII converter for dome projection'
    )
    parser.add_argument('sketch_path', help='Path to p5.js sketch directory or HTML file')
    parser.add_argument('--chars', required=True, help='Sorted characters JSON file')
    parser.add_argument('--font', default='menlo', help='Font name (menlo, monaco, courier) or path')
    parser.add_argument('--font-size', type=int, default=10, help='Font size (default: 10)')
    parser.add_argument('--frames', type=int, default=300, help='Number of frames to capture (default: 300)')
    parser.add_argument('--fps', type=float, default=30.0, help='FPS for capture (default: 30)')
    parser.add_argument('--wait', type=float, default=3.0, help='Wait time for p5.js to initialize (default: 3 seconds)')
    parser.add_argument('--png-output', default='p5_frames', help='Temporary PNG output directory')
    parser.add_argument('--output', default='ascii_frames/p5_local', help='Final ASCII output directory')
    parser.add_argument('--video-output', help='Output video file path (default: auto-generated from sketch name)')
    parser.add_argument('--skip-png', action='store_true', help='Skip PNG capture, only convert existing PNGs')
    parser.add_argument('--skip-ascii', action='store_true', help='Skip ASCII conversion, only capture PNGs')
    parser.add_argument('--skip-video', action='store_true', help='Skip video creation, only create PNG frames')
    args = parser.parse_args()
    
    # Find HTML file
    html_path = find_html_file(args.sketch_path)
    if not html_path:
        print(f"Error: Could not find HTML file in {args.sketch_path}")
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
        print("STEP 1: Capturing PNG frames from p5.js sketch")
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
        
        # Step 3: Create video from ASCII frames
        if not args.skip_video:
            print(f"\n{'='*60}")
            print("STEP 3: Creating video from ASCII frames")
            print(f"{'='*60}")
            
            # Generate output video filename
            if args.video_output:
                video_output = args.video_output
            else:
                # Create filename based on sketch directory name
                sketch_name = Path(args.sketch_path).stem
                video_output = sketch_name + '_ascii.mp4'
                # Save in same directory as output frames
                video_output = os.path.join(args.output, video_output)
            
            create_video_from_frames(args.output, video_output, args.fps)
        
        print(f"\n{'='*60}")
        print("COMPLETE!")
        print(f"{'='*60}")
        print(f"ASCII frames saved to: {args.output}/")
        if not args.skip_video:
            print(f"Video saved to: {video_output}")
    else:
        print(f"\nPNG frames saved to: {args.png_output}/")
        print("Use --skip-png to convert these to ASCII later")


if __name__ == "__main__":
    main()