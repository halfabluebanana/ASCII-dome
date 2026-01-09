"""
Batch extract and sort characters from text/json files.
Extracts unique characters from multiple files, sorts them by visual brightness,
and saves sorted character sets with _sorted suffix.

This module processes all .txt and .json files in a source directory,
extracts unique printable characters, measures their visual brightness when
rendered with a specified font, sorts them from darkest to lightest, and
saves the results as JSON files.

Author: ASCII Dome Project
Version: 1.0.0
Date: 2026-01-09
License: MIT

Dependencies:
    - Pillow (PIL)
    - json (standard library)
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont

FONTS = {
    "menlo": "/System/Library/Fonts/Menlo.ttc",
    "courier": "/System/Library/Fonts/Courier.dfont",
    "monaco": "/System/Library/Fonts/Monaco.ttf",
}

SOURCE_DIR = "/Users/adelinesetiawan/word soup_fisheye/dome_test_2048/data"
OUTPUT_DIR = "/Users/adelinesetiawan/ASCII-dome"
FONT_NAME = "menlo"
FONT_SIZE = 30


def get_char_brightness(char, font, size=50):
    """
    Render character and return average brightness value.
    
    Renders a character on a grayscale image, centers it, and calculates
    the average pixel brightness. Used for sorting characters by visual weight.
    
    Args:
        char (str): Single character to measure
        font (ImageFont): PIL ImageFont object for rendering
        size (int): Image size for rendering (default: 50)
        
    Returns:
        float: Average brightness value (0.0 = black, 255.0 = white)
    """
    img = Image.new('L', (size, size), color=0)
    draw = ImageDraw.Draw(img)
    try:
        bbox = draw.textbbox((0, 0), char, font=font)
        char_width = bbox[2] - bbox[0]
        char_height = bbox[3] - bbox[1]
        x = (size - char_width) // 2 - bbox[0]
        y = (size - char_height) // 2 - bbox[1]
        draw.text((x, y), char, font=font, fill=255)
    except:
        return 0
    pixels = list(img.getdata())
    return sum(pixels) / len(pixels)


def extract_chars_from_file(filepath):
    """
    Extract unique printable characters from a text or JSON file.
    
    Reads file content and extracts all unique printable ASCII characters.
    Always includes space character at the start (darkest character).
    Filters to printable characters with ASCII codes < 128.
    
    Args:
        filepath (str): Path to text or JSON file
        
    Returns:
        list: List of unique characters, with space first
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Get unique characters, filter to printable ASCII + common punctuation
    chars = set()
    for c in content:
        if c.isprintable() and c != ' ' and ord(c) < 128:
            chars.add(c)

    # Always include space at the start (darkest)
    return [' '] + list(chars)


def sort_chars_by_brightness(chars, font):
    """
    Sort characters from darkest to brightest based on visual rendering.
    
    Measures the brightness of each character when rendered with the given font
    and sorts them from darkest (lowest brightness) to brightest (highest brightness).
    Space character is always placed first (brightness = 0).
    
    Args:
        chars (list): List of characters to sort
        font (ImageFont): PIL ImageFont object for brightness measurement
        
    Returns:
        list: Characters sorted from darkest to brightest
    """
    char_brightness = []
    for char in chars:
        if char == ' ':
            char_brightness.append((char, 0))  # Space is always darkest
        else:
            brightness = get_char_brightness(char, font)
            char_brightness.append((char, brightness))

    char_brightness.sort(key=lambda x: x[1])
    return [c[0] for c in char_brightness]


def process_file(filepath, font, output_dir):
    """
    Process a single file and save sorted characters to JSON.
    
    Extracts characters from file, sorts them by brightness, and saves
    to a JSON file with _sorted suffix in the output directory.
    
    Args:
        filepath (str): Path to input file (txt or json)
        font (ImageFont): PIL ImageFont object for brightness measurement
        output_dir (str): Directory to save output JSON files
        
    Returns:
        str: Path to saved output JSON file
    """
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)

    print(f"\nProcessing: {filename}")

    chars = extract_chars_from_file(filepath)
    print(f"  Found {len(chars)} unique characters")

    sorted_chars = sort_chars_by_brightness(chars, font)

    output_data = {
        "source": filename,
        "characters": "".join(sorted_chars),
        "count": len(sorted_chars)
    }

    output_path = os.path.join(output_dir, f"{name}_sorted.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"  Saved: {name}_sorted.json")
    print(f"  Characters: {output_data['characters'][:50]}...")

    return output_path


def main():
    """
    Main entry point for batch character sorting.
    
    Processes all .txt and .json files in the source directory,
    extracts unique characters, sorts them by visual brightness,
    and saves sorted character sets to the output directory.
    
    Configuration (set at module level):
        SOURCE_DIR: Directory containing input files
        OUTPUT_DIR: Directory for output JSON files
        FONT_NAME: Font to use for brightness measurement
        FONT_SIZE: Font size for rendering
        
    Output:
        Creates JSON files with _sorted suffix containing:
        - source: Original filename
        - characters: Sorted character string (dark to light)
        - count: Number of characters
    """
    font_path = FONTS.get(FONT_NAME, FONT_NAME)
    font = ImageFont.truetype(font_path, FONT_SIZE)
    print(f"Using font: {font_path}")

    # Find all txt and json files (exclude Fonts folder)
    files_to_process = []
    for filename in os.listdir(SOURCE_DIR):
        if filename.startswith('.'):
            continue
        filepath = os.path.join(SOURCE_DIR, filename)
        if os.path.isfile(filepath) and (filename.endswith('.txt') or filename.endswith('.json')):
            files_to_process.append(filepath)

    print(f"\nFound {len(files_to_process)} files to process")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for filepath in sorted(files_to_process):
        process_file(filepath, font, OUTPUT_DIR)

    print(f"\n\nDone! Sorted character files saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
