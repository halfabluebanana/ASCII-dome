"""
Video to ASCII converter for dome projection.
Converts video files to ASCII art frames optimized for 2048x2048 dome projection.

This module processes video files frame-by-frame, converts each frame to ASCII art
using a sorted character set, and renders the ASCII text to 2048x2048 PNG images
suitable for dome projection systems.

Author: ASCII Dome Project
Version: 1.0.0
Date: 2026-01-09
License: MIT

Usage:
    python video_to_ascii.py input.mp4 --chars chars_sorted.json --font menlo
    python video_to_ascii.py input.mp4 --chars chars.json --font menlo --font-size 12 --preview

Dependencies:
    - opencv-python (cv2)
    - Pillow (PIL)
    - json (standard library)
"""

import cv2
import json
import argparse
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_SIZE = 2048

FONT_DIR = "/Users/adelinesetiawan/ASCII-dome/fonts"
FONTS = {
    "menlo": f"{FONT_DIR}/Menlo.ttc",
}


def load_characters(json_path):
    """
    Load character set from JSON file.
    
    Supports multiple JSON formats:
    - {"characters": "ABC123"} or {"chars": "ABC123"}
    - ["A", "B", "C", "1", "2", "3"]
    - "ABC123" (string)
    
    Args:
        json_path (str): Path to JSON file containing character set
        
    Returns:
        str: String of characters sorted by brightness (dark to light)
        
    Raises:
        FileNotFoundError: If JSON file doesn't exist
        json.JSONDecodeError: If JSON file is invalid
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get('characters', data.get('chars', ''))
    return ''.join(data) if isinstance(data, list) else data


def get_font_metrics(font):
    """
    Get character width and height metrics for a font.
    
    Uses the character 'W' as a reference for maximum width.
    
    Args:
        font (ImageFont): PIL ImageFont object
        
    Returns:
        tuple: (char_width, char_height) in pixels
    """
    bbox = font.getbbox("W")
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def load_font(font_path, size):
    """
    Load a font from file path.
    
    Handles both TrueType (.ttf) and TrueType Collection (.ttc) fonts.
    For .ttc files, uses the first font in the collection (index=0).
    
    Args:
        font_path (str): Path to font file
        size (int): Font size in points
        
    Returns:
        ImageFont: PIL ImageFont object
        
    Raises:
        IOError: If font file cannot be opened
        OSError: If font file is invalid
    """
    if font_path.endswith('.ttc'):
        return ImageFont.truetype(font_path, size, index=0)
    return ImageFont.truetype(font_path, size)


def frame_to_ascii(pil_image, chars, cols, rows):
    """
    Convert a PIL image to ASCII art lines.
    
    Converts image to grayscale, resizes to specified dimensions,
    and maps each pixel's brightness to a character from the sorted
    character set (darkest pixel = first char, brightest = last char).
    
    Args:
        pil_image (PIL.Image): Input image (any color mode)
        chars (str): Sorted character string (dark to light)
        cols (int): Number of character columns (width)
        rows (int): Number of character rows (height)
        
    Returns:
        list: List of strings, each string is one row of ASCII characters
    """
    gray = pil_image.convert("L")
    resized = gray.resize((cols, rows), Image.Resampling.LANCZOS)
    pixels = list(resized.getdata())

    num_chars = len(chars)
    ascii_lines = []

    for row in range(rows):
        line = ""
        for col in range(cols):
            pixel = pixels[row * cols + col]
            idx = int(pixel / 256 * num_chars)
            idx = min(idx, num_chars - 1)
            line += chars[idx]
        ascii_lines.append(line)

    return ascii_lines


def render_ascii_frame(ascii_lines, font, char_w, char_h):
    """
    Render ASCII text lines to a 2048x2048 PNG image.
    
    Creates a black background image and renders white ASCII text
    centered on the canvas. Used for dome projection output.
    
    Args:
        ascii_lines (list): List of ASCII strings (one per row)
        font (ImageFont): PIL ImageFont object for rendering
        char_w (int): Character width in pixels
        char_h (int): Character height in pixels
        
    Returns:
        PIL.Image: 2048x2048 RGB image with ASCII text rendered in white
    """
    img = Image.new('RGB', (OUTPUT_SIZE, OUTPUT_SIZE), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    text_width = len(ascii_lines[0]) * char_w
    text_height = len(ascii_lines) * char_h
    x_offset = (OUTPUT_SIZE - text_width) // 2
    y_offset = (OUTPUT_SIZE - text_height) // 2

    for i, line in enumerate(ascii_lines):
        draw.text((x_offset, y_offset + i * char_h), line, font=font, fill=(255, 255, 255))

    return img


def main():
    """
    Main entry point for video to ASCII conversion.
    
    Processes command-line arguments, loads character set and font,
    opens video file, converts each frame to ASCII, and saves output
    as 2048x2048 PNG images.
    
    Command-line arguments:
        input: Input video file path
        --chars: Path to JSON file with sorted characters (required)
        --font: Font name (menlo) or path (default: menlo)
        --font-size: Font size in points (default: 10)
        --output: Output directory for ASCII frames (default: ascii_frames/video)
        --video-output: Output video file path (default: auto-generated from input name)
        --skip-video: Skip video creation, only create PNG frames (flag)
        --preview: Process only first 30 frames (flag)
        
    Output:
        Creates directory with frame_000000.png, frame_000001.png, etc.
        Automatically creates MP4 video with naming: input_ascii.mp4
        Video is saved in the output directory (or specified --video-output path)
    """
    parser = argparse.ArgumentParser(description='Video to ASCII for dome')
    parser.add_argument('input', help='Input video file')
    parser.add_argument('--chars', required=True, help='Sorted characters JSON')
    parser.add_argument('--font', default='menlo', help='Font name (menlo) or path')
    parser.add_argument('--font-size', type=int, default=10, help='Font size (default: 10)')
    parser.add_argument('--output', default='ascii_frames/video', help='Output directory for ASCII frames')
    parser.add_argument('--video-output', help='Output video file path (default: auto-generated from input name)')
    parser.add_argument('--skip-video', action='store_true', help='Skip video creation, only create PNG frames')
    parser.add_argument('--preview', action='store_true', help='Process only first 30 frames')
    args = parser.parse_args()

    chars = load_characters(args.chars)
    if not chars:
        print("Error: No characters loaded")
        return

    print(f"Loaded {len(chars)} characters: {chars[:20]}...")

    font_path = FONTS.get(args.font.lower(), args.font)
    font = load_font(font_path, args.font_size)
    print(f"Font: {font_path}")

    char_w, char_h = get_font_metrics(font)
    cols = OUTPUT_SIZE // char_w
    rows = OUTPUT_SIZE // char_h
    print(f"Grid: {cols}x{rows} characters")
    print(f"Char size: {char_w}x{char_h} pixels")

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print(f"Error: Cannot open {args.input}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video: {total_frames} frames @ {fps:.2f} FPS")

    os.makedirs(args.output, exist_ok=True)

    frame_num = 0
    max_frames = 30 if args.preview else float('inf')

    print("Processing frames...")
    while frame_num < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)

        ascii_lines = frame_to_ascii(pil_image, chars, cols, rows)
        img = render_ascii_frame(ascii_lines, font, char_w, char_h)

        output_path = os.path.join(args.output, f'frame_{frame_num:06d}.png')
        img.save(output_path, 'PNG')

        frame_num += 1
        if frame_num % 10 == 0:
            print(f"  {frame_num}/{total_frames} frames")

    cap.release()
    print(f"\nDone. {frame_num} frames saved to '{args.output}/'")
    
    # Automatically create video from frames
    if not args.skip_video:
        # Generate output video filename
        if args.video_output:
            video_output = args.video_output
        else:
            # Create filename based on input: input.mp4 -> input_ascii.mp4
            input_path = Path(args.input)
            video_output = input_path.stem + '_ascii' + input_path.suffix
            # Save in same directory as output frames, or current directory
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
            print(f"  ffmpeg -framerate {fps:.0f} -i {args.output}/frame_%06d.png -c:v libx264 -pix_fmt yuv420p {video_output}")
            return
        
        # Run ffmpeg to create video
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-framerate', str(int(fps)),
            '-i', os.path.join(args.output, 'frame_%06d.png'),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            video_output
        ]
        
        try:
            result = subprocess.run(ffmpeg_cmd, 
                                  capture_output=True, 
                                  text=True,
                                  check=True)
            print(f"✓ Video created successfully: {video_output}")
            file_size = os.path.getsize(video_output) / (1024 * 1024)  # MB
            print(f"  File size: {file_size:.1f} MB")
        except subprocess.CalledProcessError as e:
            print(f"Error creating video: {e}")
            print(f"  stderr: {e.stderr}")
            print(f"\n  You can create it manually with:")
            print(f"  ffmpeg -framerate {fps:.0f} -i {args.output}/frame_%06d.png -c:v libx264 -pix_fmt yuv420p {video_output}")
    else:
        print(f"\nSkipping video creation (--skip-video flag set)")
        print(f"  To create video manually:")
        print(f"  ffmpeg -framerate {fps:.0f} -i {args.output}/frame_%06d.png -c:v libx264 -pix_fmt yuv420p output.mp4")


if __name__ == "__main__":
    main()
