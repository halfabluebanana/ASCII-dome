# ASCII Dome Project

A collection of Python scripts for converting various media formats to ASCII art optimized for 2048x2048 dome projection.

## Overview

This project provides tools to convert:
- **Video files** → ASCII art frames → MP4/MOV video
- **PNG image sequences** → ASCII art frames → MP4/MOV video  
- **P5.js WEBGL sketches** → PNG frames → ASCII art frames → MOV video (ProRes)

All outputs are optimized for 2048x2048 dome projection systems.

## Quick Start

### 1. Download Files to Local Path

For p5.js sketches, download the sketch files to your local machine. The scripts can work with:
- A directory containing HTML, JS, and other sketch files
- A direct path to an HTML file

Example:
```bash
# Download a p5.js sketch from the web editor
# Save it to: /Users/yourname/Downloads/my_sketch/
```

### 2. Run the Scripts

All scripts follow a similar pattern:
```bash
python script_name.py <input> --chars <character_set> [options]
```

### 3. Choose a Font

Available fonts:
- **`menlo`** (default) - Monospace font, good for ASCII art
- **`monaco`** - Alternative monospace font
- **`courier`** - Classic monospace font

Use the `--font` option:
```bash
python p5_webgl_to_ascii.py sketch.html --chars chars.json --font menlo
python p5_webgl_to_ascii.py sketch.html --chars chars.json --font courier
```

### 4. Change Font Size

Adjust the font size with `--font-size` (default: 10):
```bash
python p5_webgl_to_ascii.py sketch.html --chars chars.json --font-size 12
python p5_webgl_to_ascii.py sketch.html --chars chars.json --font-size 8
```

Larger font size = fewer characters per frame, smaller font size = more characters per frame.

### 5. Choose Character Set

Select from different JSON files in `chars_sorted/`:
```bash
# Standard ASCII characters
python script.py input --chars chars_sorted/chars_standard.json

# Invisible Cities expanded set
python script.py input --chars chars_sorted/invisible_cities_expanded_sorted.json

# Dictionary-based characters
python script.py input --chars chars_sorted/dictionary_data_sorted.json

# Watts character set
python script.py input --chars chars_sorted/watts_sorted.json

# And many more in chars_sorted/ directory
```

### 6. R and S Keys (for p5.js Scripts)

For `p5_webgl_to_ascii.py` and `p5_local_to_ascii.py`:
- The browser window will open automatically
- **Press 'R'** in the browser window to **START** recording
- **Press 'S'** in the browser window to **STOP** recording
- The script will automatically detect when you stop and download the frames
- You control the recording duration manually

## Scripts Overview

### What Each Script Does:

1. **`video_to_ascii.py`** - Converts video files (MP4, MOV, etc.) to ASCII art frames and video
2. **`png_to_ascii.py`** - Converts a directory of PNG images to ASCII art frames and video
3. **`p5_webgl_to_ascii.py`** - Runs p5.js WEBGL sketches, captures frames using R/S recording, converts to ASCII art, and creates ProRes MOV video
4. **`p5_local_to_ascii.py`** - Works with locally downloaded p5.js sketches, uses R/S recording, converts to ASCII art, and creates MP4 video
5. **`batch_sort_chars.py`** - Batch processes text/JSON files to extract and sort characters by brightness
6. **`sort_characters.py`** - Sorts characters from a single input file (JSON/TXT) by brightness

---

## Detailed Script Documentation

### 1. `video_to_ascii.py`
Converts video files to ASCII art frames and automatically creates MP4 output.

**Usage:**
```bash
python video_to_ascii.py input.mp4 --chars chars_sorted/chars_standard.json
```

**Options:**
- `input` - Input video file path (required)
- `--chars` - Path to JSON file with sorted characters (required)
- `--font` - Font name (menlo) or path (default: menlo)
- `--font-size` - Font size in points (default: 10)
- `--output` - Output directory for ASCII frames (default: ascii_frames/video)
- `--video-output` - Output video file path (default: auto-generated from input name)
- `--skip-video` - Skip video creation, only create PNG frames
- `--preview` - Process only first 30 frames

**Examples:**
```bash
# Basic conversion
python video_to_ascii.py output.mp4 --chars chars_sorted/chars_standard.json

# Custom character set
python video_to_ascii.py output.mp4 --chars chars_sorted/invisible_cities_expanded_sorted.json

# Custom video output name
python video_to_ascii.py output.mp4 --chars chars.json --video-output my_ascii_video.mp4

# Preview mode (first 30 frames only)
python video_to_ascii.py output.mp4 --chars chars.json --preview
```

**Output:**
- Creates `ascii_frames/video/` directory with PNG frames
- Automatically creates `input_ascii.mp4` video file in the same directory

---

### 2. `png_to_ascii.py`
Converts PNG image sequences to ASCII art frames and automatically creates MP4 output.

**Usage:**
```bash
python png_to_ascii.py frames/ --chars chars_sorted/chars_standard.json
```

**Options:**
- `input` - Input directory or image file path (required)
- `--chars` - Path to JSON file with sorted characters (required)
- `--font` - Font name (menlo) or path (default: menlo)
- `--font-size` - Font size in points (default: 10)
- `--output` - Output directory for ASCII frames (default: ascii_frames/png)
- `--video-output` - Output video file path (default: auto-generated from input name)
- `--skip-video` - Skip video creation, only create PNG frames
- `--fps` - FPS for video creation (default: 30)
- `--preview` - Process only first 30 frames

**Examples:**
```bash
# Convert directory of PNGs
python png_to_ascii.py frames/ --chars chars_sorted/chars_standard.json

# Convert single image (finds all images in same directory)
python png_to_ascii.py frame_000001.png --chars chars.json

# Custom FPS
python png_to_ascii.py frames/ --chars chars.json --fps 24
```

**Output:**
- Creates `ascii_frames/png/` directory with PNG frames
- Automatically creates `input_ascii.mp4` video file in the same directory

---

### 3. `p5_webgl_to_ascii.py`
Runs a p5.js WEBGL sketch in a browser, captures frames using manual R/S recording, converts to ASCII art, and automatically creates ProRes MOV video.

**Important: Manual Recording Control**
- Browser window opens automatically (not headless)
- **You must press 'R' in the browser** to start recording
- **You must press 'S' in the browser** to stop recording
- Script waits for you to control recording manually
- Recording duration is controlled by you, not the script

**Usage:**
```bash
python p5_webgl_to_ascii.py /path/to/sketch/directory --chars chars_sorted/chars_standard.json
```

**Options:**
- `input` - Input p5.js sketch directory or HTML file (required)
- `--chars` - Path to JSON file with sorted characters (required)
- `--font` - Font name (menlo, monaco, courier) or path (default: menlo)
- `--font-size` - Font size in points (default: 10)
- `--frames` - Number of frames (informational only, recording duration is manual)
- `--fps` - Frame rate for video creation (default: 30.0)
- `--wait` - Wait time for p5.js to initialize in seconds (default: 2.0)
- `--png-output` - Temporary PNG output directory (default: p5_frames)
- `--output` - Final ASCII output directory (default: ascii_frames/p5_webgl)
- `--video-output` - Output video file path (default: auto-generated, creates .mov)
- `--skip-png` - Skip PNG capture, only convert existing PNGs
- `--skip-ascii` - Skip ASCII conversion, only capture PNGs
- `--skip-video` - Skip video creation, only create PNG frames

**Examples:**
```bash
# Full pipeline with custom font and character set
python p5_webgl_to_ascii.py /path/to/sketch --chars chars_sorted/invisible_cities_expanded_sorted.json --font courier --font-size 12

# Only convert existing PNGs to ASCII
python p5_webgl_to_ascii.py /path/to/sketch --chars chars.json --skip-png

# Only capture PNGs (skip ASCII conversion)
python p5_webgl_to_ascii.py /path/to/sketch --chars chars.json --skip-ascii
```

**Output:**
- Creates `p5_frames/` directory with captured PNG frames (from tar file)
- Creates `ascii_frames/p5_webgl/` directory with ASCII PNG frames
- Automatically creates `sketch_ascii.mov` ProRes video file (high quality, larger file size)

---

### 4. `p5_local_to_ascii.py`
Works with locally downloaded p5.js sketches. Uses manual R/S recording, converts to ASCII art, and creates MP4 video.

**Important: Manual Recording Control**
- Browser window opens automatically
- **You must press 'R' in the browser** to start recording
- **You must press 'S' in the browser** to stop recording
- Script waits for you to control recording manually

**Usage:**
```bash
python p5_local_to_ascii.py /path/to/sketch/directory --chars chars_sorted/chars_standard.json
```

**Options:**
- `sketch_path` - Path to p5.js sketch directory or HTML file (required)
- `--chars` - Path to JSON file with sorted characters (required)
- `--font` - Font name (menlo, monaco, courier) or path (default: menlo)
- `--font-size` - Font size in points (default: 10)
- `--frames` - Number of frames (informational only, recording duration is manual)
- `--fps` - Frame rate for video creation (default: 30.0)
- `--wait` - Wait time for p5.js to initialize (default: 3.0 seconds)
- `--png-output` - Temporary PNG output directory (default: p5_frames)
- `--output` - Final ASCII output directory (default: ascii_frames/p5_local)
- `--video-output` - Output video file path (default: auto-generated)
- `--skip-png` - Skip PNG capture, only convert existing PNGs
- `--skip-ascii` - Skip ASCII conversion, only capture PNGs
- `--skip-video` - Skip video creation, only create PNG frames

**Output:**
- Creates `p5_frames/` directory with captured PNG frames (from tar file)
- Creates `ascii_frames/p5_local/` directory with ASCII PNG frames
- Automatically creates `sketch_ascii.mp4` video file

---

### 5. `sort_characters.py`
Sorts characters by visual brightness for use in ASCII conversion.

**Usage:**
```bash
python sort_characters.py input.json output.json --font menlo
```

**Options:**
- `input` - Input JSON or TXT file (required)
- `output` - Output JSON file (required)
- `--font` - Font name (menlo, courier, monaco) or path (default: menlo)
- `--size` - Render size for brightness measurement (default: 30)

**Examples:**
```bash
# Sort characters from JSON
python sort_characters.py input.json output_sorted.json --font menlo

# Sort characters from text file
python sort_characters.py input.txt output_sorted.json --font courier
```

---

### 5. `batch_sort_chars.py`
Batch processes multiple text/JSON files to extract and sort characters.

**Usage:**
```bash
python batch_sort_chars.py
```

**Configuration:**
Edit the script to set:
- `SOURCE_DIR` - Directory containing input files
- `OUTPUT_DIR` - Directory for output JSON files
- `FONT_NAME` - Font to use (menlo, courier, monaco)
- `FONT_SIZE` - Font size for rendering

**Output:**
Creates `*_sorted.json` files in the output directory.

---

## Character Sets

Character sets are stored in `chars_sorted/` directory. Each JSON file contains characters sorted from darkest to lightest.

### Available Character Sets:
- `chars_standard.json` - Standard 68 characters
- `chars_simple.json` - Simpler character set
- `chars_numbers.json` - Numbers only
- `invisible_cities_expanded_sorted.json` - Expanded set with more characters
- `watts_sorted.json` - Watts character set
- `dictionary_data_sorted.json` - Dictionary-based characters
- And many more...

### Character Set Format:
```json
{
  "characters": " .`'^\",:;!i|\\/)(-_<>...",
  "count": 68
}
```

Or simply:
```json
" .`'^\",:;!i|\\/)(-_<>..."
```

---

## Installation

### Required Dependencies:
```bash
pip install pillow opencv-python
```

### Optional Dependencies:

**For p5_webgl_to_ascii.py and p5_local_to_ascii.py:**
```bash
pip install playwright
playwright install chromium
```

**For video processing:**
```bash
# FFmpeg is required for video creation
# macOS:
brew install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

---

## Output Organization

All scripts save their outputs in organized subdirectories within `ascii_frames/`:

```
ascii_frames/
├── p5_local/          # Local p5.js sketches (p5_local_to_ascii.py)
│   ├── frame_000000.png
│   ├── frame_000001.png
│   └── sketch_ascii.mp4
├── p5_webgl/          # P5.js WEBGL sketches (p5_webgl_to_ascii.py)
│   ├── frame_000000.png
│   ├── frame_000001.png
│   └── sketch_ascii.mp4
├── png/               # PNG sequence conversions (png_to_ascii.py)
│   ├── frame_000000.png
│   ├── frame_000001.png
│   └── input_ascii.mp4
└── video/             # Video conversions (video_to_ascii.py)
    ├── frame_000000.png
    ├── frame_000001.png
    └── video_ascii.mp4
```

Each script automatically creates its own subdirectory to keep outputs organized and prevent conflicts.

## Output Format

All scripts output:
- **PNG frames**: `frame_000000.png`, `frame_000001.png`, etc.
- **Video files**: 
  - `p5_webgl_to_ascii.py` creates **ProRes MOV** files (high quality, larger size)
  - Other scripts create **MP4** files (H.264 with yuv420p pixel format)
- **Resolution**: 2048x2048 pixels (optimized for dome projection)
- **Location**: Each script saves to its own subdirectory in `ascii_frames/`

---

## Workflow Examples

### Convert Video to ASCII:
```bash
python video_to_ascii.py input.mp4 --chars chars_sorted/chars_standard.json
# Output: ascii_frames/video/input_ascii.mp4
```

### Convert PNG Sequence to ASCII:
```bash
python png_to_ascii.py frames/ --chars chars_sorted/invisible_cities_expanded_sorted.json
# Output: ascii_frames/png/frames_ascii.mp4
```

### Convert P5.js WEBGL Sketch to ASCII:
```bash
python p5_webgl_to_ascii.py sketch.html --chars chars_sorted/chars_standard.json --frames 300
# Output: ascii_frames/p5_webgl/sketch_ascii.mp4
```

### Convert Local P5.js Sketch to ASCII:
```bash
python p5_local_to_ascii.py /path/to/sketch --chars chars_sorted/chars_standard.json
# Output: ascii_frames/p5_local/sketch_ascii.mp4
```

---

### 4. `p5_local_to_ascii.py`
Works with locally downloaded p5.js sketches. Uses manual R/S recording, converts to ASCII art, and creates MP4 video.

**Important: Manual Recording Control**
- Browser window opens automatically
- **You must press 'R' in the browser** to start recording
- **You must press 'S' in the browser** to stop recording
- Script waits for you to control recording manually

**Usage:**
```bash
python p5_local_to_ascii.py /path/to/sketch/directory --chars chars_sorted/chars_standard.json
```

**Options:**
- `sketch_path` - Path to p5.js sketch directory or HTML file (required)
- `--chars` - Path to JSON file with sorted characters (required)
- `--font` - Font name (menlo, monaco, courier) or path (default: menlo)
- `--font-size` - Font size in points (default: 10)
- `--frames` - Number of frames (informational only, recording duration is manual)
- `--fps` - Frame rate for video creation (default: 30.0)
- `--wait` - Wait time for p5.js to initialize (default: 3.0 seconds)
- `--png-output` - Temporary PNG output directory (default: p5_frames)
- `--output` - Final ASCII output directory (default: ascii_frames/p5_local)
- `--video-output` - Output video file path (default: auto-generated)
- `--skip-png` - Skip PNG capture, only convert existing PNGs
- `--skip-ascii` - Skip ASCII conversion, only capture PNGs
- `--skip-video` - Skip video creation, only create PNG frames

**Output:**
- Creates `p5_frames/` directory with captured PNG frames (from tar file)
- Creates `ascii_frames/p5_local/` directory with ASCII PNG frames
- Automatically creates `sketch_ascii.mp4` video file

---

### 5. `batch_sort_chars.py`
Batch processes multiple text/JSON files to extract and sort characters by brightness.

**Usage:**
```bash
python batch_sort_chars.py file1.txt file2.json file3.txt
```

**Options:**
- Input files - One or more text or JSON files
- `--font` - Font to use for brightness calculation (default: menlo)
- `--font-size` - Font size for calculation (default: 10)

**Output:**
- Creates `*_sorted.json` files in the same directory as input files

---

### 6. `sort_characters.py`
Sorts characters from a single input file (JSON/TXT) by brightness.

**Usage:**
```bash
python sort_characters.py input.json --font menlo
```

**Output:**
- Creates `input_sorted.json` file

---

## Tips

1. **Character Set Selection**: Different character sets produce different visual effects:
   - `chars_simple.json` - Clean, minimal look
   - `chars_standard.json` - Balanced detail
   - `invisible_cities_expanded_sorted.json` - Rich detail with more characters

2. **Font Selection**: Font affects character spacing and appearance:
   - `menlo` - Monospace, good for ASCII
   - `monaco` - Similar to Menlo
   - `courier` - Classic monospace

3. **Performance**: 
   - Use `--preview` flag to test with first 30 frames
   - Processing speed is tracked and displayed during conversion
   - Target: 30fps processing speed

4. **File Naming**:
   - Videos are automatically named: `input_filename_ascii.mp4`
   - Use `--video-output` for custom naming
   - Use `--skip-video` if you only need PNG frames

---

## Troubleshooting

### ffmpeg not found:
```bash
# macOS
brew install ffmpeg

# Then re-run the script
```

### Playwright/Selenium not found:
```bash
# Install Playwright (recommended)
pip install playwright
playwright install chromium

# OR install Selenium
pip install selenium
```

### Canvas not found (p5.js):
- Ensure the HTML file includes p5.js library
- Check browser console for errors
- Increase `--wait` time if sketch loads slowly

---

## License

MIT

---

## Author

ASCII Dome Project  
Version: 1.0.0  
Date: 2026-01-09

