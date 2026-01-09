"""
Sorts characters by visual brightness (dark to light).
Renders each character, measures average pixel value, and sorts from darkest to brightest.

This module processes a single input file (JSON or TXT), extracts characters,
measures their visual brightness when rendered with a specified font, and
saves the sorted character set to a JSON file.

Author: ASCII Dome Project
Version: 1.0.0
Date: 2026-01-09
License: MIT

Usage:
    python sort_characters.py input.json output.json --font menlo
    python sort_characters.py input.txt output.json --font courier --size 30

Input formats:
    JSON: {"characters": "ABC123!@#"} or {"chars": "ABC123"} or ["A", "B", "C"]
    TXT: Raw characters (one line or multiple lines)

Dependencies:
    - Pillow (PIL)
    - json (standard library)
"""

import json
import argparse
from PIL import Image, ImageDraw, ImageFont

FONTS = {
    "menlo": "/System/Library/Fonts/Menlo.ttc",
    "courier": "/System/Library/Fonts/Courier.dfont",
    "monaco": "/System/Library/Fonts/Monaco.ttf",
}


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

    bbox = draw.textbbox((0, 0), char, font=font)
    char_width = bbox[2] - bbox[0]
    char_height = bbox[3] - bbox[1]

    x = (size - char_width) // 2 - bbox[0]
    y = (size - char_height) // 2 - bbox[1]

    draw.text((x, y), char, font=font, fill=255)

    pixels = list(img.getdata())
    return sum(pixels) / len(pixels)


def load_characters(file_path):
    """
    Load characters from JSON or TXT file.
    
    Supports multiple JSON formats:
    - {"characters": "ABC123"} or {"chars": "ABC123"}
    - ["A", "B", "C", "1", "2", "3"]
    - "ABC123" (string)
    
    For TXT files, extracts unique characters from file content.
    
    Args:
        file_path (str): Path to JSON or TXT file
        
    Returns:
        list: List of characters extracted from file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON file is invalid
        ValueError: If JSON format is unrecognized
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if file_path.endswith('.json'):
        data = json.loads(content)
        if isinstance(data, list):
            return list(data)
        elif isinstance(data, dict):
            if 'characters' in data:
                chars = data['characters']
                return list(chars) if isinstance(chars, str) else chars
            elif 'chars' in data:
                chars = data['chars']
                return list(chars) if isinstance(chars, str) else chars
        raise ValueError("Unrecognized JSON format")
    else:
        # TXT: unique characters from file
        chars = list(set(content.replace('\n', '').replace('\r', '')))
        return chars


def sort_by_brightness(chars, font):
    """
    Sort characters from darkest to brightest based on visual rendering.
    
    Measures the brightness of each character when rendered with the given font
    and sorts them from darkest (lowest brightness) to brightest (highest brightness).
    Prints brightness values for each character during processing.
    
    Args:
        chars (list): List of characters to sort
        font (ImageFont): PIL ImageFont object for brightness measurement
        
    Returns:
        list: Characters sorted from darkest to brightest
    """
    char_brightness = []
    for char in chars:
        brightness = get_char_brightness(char, font)
        char_brightness.append((char, brightness))
        print(f"  '{char}': {brightness:.2f}")

    char_brightness.sort(key=lambda x: x[1])
    return [c[0] for c in char_brightness]


def main():
    """
    Main entry point for character sorting.
    
    Processes command-line arguments, loads characters from input file,
    sorts them by visual brightness, and saves to output JSON file.
    
    Command-line arguments:
        input: Input JSON or TXT file path (required)
        output: Output JSON file path (required)
        --font: Font name (menlo, courier, monaco) or path (default: menlo)
        --size: Render size for brightness measurement (default: 30)
        
    Output:
        Creates JSON file with:
        - characters: Sorted character string (dark to light)
        - chars_list: Sorted character list
        - count: Number of characters
        
    Note:
        Prints brightness values for each character during sorting process.
    """
    parser = argparse.ArgumentParser(description='Sort characters by brightness')
    parser.add_argument('input', help='Input JSON or TXT file')
    parser.add_argument('output', help='Output JSON file')
    parser.add_argument('--font', default='menlo', help='Font name (menlo/courier/monaco) or path')
    parser.add_argument('--size', type=int, default=30, help='Render size for measurement')
    args = parser.parse_args()

    font_path = FONTS.get(args.font.lower(), args.font)
    font = ImageFont.truetype(font_path, args.size)
    print(f"Font: {font_path}")

    print(f"Loading characters from {args.input}...")
    chars = load_characters(args.input)
    print(f"Found {len(chars)} characters")

    print("\nMeasuring brightness...")
    sorted_chars = sort_by_brightness(chars, font)

    output_data = {
        "characters": "".join(sorted_chars),
        "chars_list": sorted_chars,
        "count": len(sorted_chars)
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nSorted characters (dark to light):")
    print(f"  {''.join(sorted_chars)}")
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
