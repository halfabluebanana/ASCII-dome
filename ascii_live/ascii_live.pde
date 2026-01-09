/**
 * Live ASCII renderer for dome projection
 * Output: 2048x2048 @ 30fps
 *
 * Modes:
 *   1. Webcam/capture input
 *   2. Load and render a p5.js/Processing sketch as source
 *   3. Load PNG sequence
 *
 * Press 'r' to start recording PNG sequence
 * Press 's' to stop recording
 */

int OUTPUT_SIZE = 2048;
int FONT_SIZE = 10;
String CHARS = " .:-=+*#%@";  // Will be loaded from JSON

PFont mono;
PGraphics source;  // Your input content renders here
PGraphics output;  // ASCII output renders here

int cols, rows;
int charW, charH;

boolean recording = false;
int frameCounter = 0;
String outputDir = "frames";

// Source mode
int sourceMode = 0;  // 0=demo, 1=webcam, 2=png sequence
Capture cam;
String[] pngFiles;
int pngIndex = 0;

void setup() {
  size(1024, 1024);  // Preview window (smaller)
  frameRate(30);

  // Load monospace font - place .vlw font file in data/ folder
  // Create with: Tools > Create Font
  mono = createFont("Courier", FONT_SIZE);
  textFont(mono);

  // Calculate character metrics
  charW = (int)textWidth("W");
  charH = FONT_SIZE + 2;

  cols = OUTPUT_SIZE / charW;
  rows = OUTPUT_SIZE / charH;

  println("Grid: " + cols + "x" + rows);
  println("Char: " + charW + "x" + charH);

  // Create graphics buffers
  source = createGraphics(cols, rows);  // Low-res source
  output = createGraphics(OUTPUT_SIZE, OUTPUT_SIZE);  // Full output

  // Load characters from JSON if exists
  loadCharsFromJSON("chars_sorted.json");

  // Setup source mode
  setupSource();
}

void loadCharsFromJSON(String path) {
  File f = new File(dataPath(path));
  if (f.exists()) {
    JSONObject json = loadJSONObject(path);
    if (json.hasKey("characters")) {
      CHARS = json.getString("characters");
      println("Loaded " + CHARS.length() + " characters from JSON");
    }
  } else {
    println("Using default characters: " + CHARS);
  }
}

void setupSource() {
  // Uncomment the source you want:

  // Demo mode (built-in animation)
  sourceMode = 0;

  // Webcam mode
  // sourceMode = 1;
  // String[] cameras = Capture.list();
  // if (cameras.length > 0) {
  //   cam = new Capture(this, cols, rows, cameras[0]);
  //   cam.start();
  // }

  // PNG sequence mode
  // sourceMode = 2;
  // File dir = new File(dataPath("input_sequence"));
  // pngFiles = dir.list();
  // java.util.Arrays.sort(pngFiles);
}

void draw() {
  // Render source content
  renderSource();

  // Convert to ASCII
  renderASCII();

  // Display preview
  image(output, 0, 0, width, height);

  // Recording
  if (recording) {
    output.save(outputDir + "/frame_" + nf(frameCounter, 6) + ".png");
    frameCounter++;

    // Visual indicator
    fill(255, 0, 0);
    ellipse(20, 20, 15, 15);
  }

  // Stats
  fill(255);
  text("FPS: " + nf(frameRate, 0, 1), 10, height - 10);
}

void renderSource() {
  source.beginDraw();
  source.background(0);

  if (sourceMode == 0) {
    // Demo: animated circles
    source.noStroke();
    for (int i = 0; i < 5; i++) {
      float x = source.width/2 + cos(frameCount * 0.02 + i) * source.width * 0.3;
      float y = source.height/2 + sin(frameCount * 0.03 + i * 0.5) * source.height * 0.3;
      float r = 10 + sin(frameCount * 0.05 + i) * 5;
      source.fill(255 - i * 40);
      source.ellipse(x, y, r, r);
    }
  }
  else if (sourceMode == 1 && cam != null && cam.available()) {
    // Webcam
    cam.read();
    source.image(cam, 0, 0);
  }
  else if (sourceMode == 2 && pngFiles != null) {
    // PNG sequence
    PImage img = loadImage("input_sequence/" + pngFiles[pngIndex]);
    source.image(img, 0, 0, source.width, source.height);
    pngIndex = (pngIndex + 1) % pngFiles.length;
  }

  source.endDraw();
}

void renderASCII() {
  source.loadPixels();

  output.beginDraw();
  output.background(0);
  output.fill(255);
  output.textFont(mono);
  output.textAlign(LEFT, TOP);

  int numChars = CHARS.length();

  for (int row = 0; row < rows; row++) {
    StringBuilder line = new StringBuilder();

    for (int col = 0; col < cols; col++) {
      int idx = row * cols + col;
      color c = source.pixels[idx];
      int brightness = (int)brightness(c);

      // Map brightness to character
      int charIdx = (int)map(brightness, 0, 255, 0, numChars - 1);
      charIdx = constrain(charIdx, 0, numChars - 1);
      line.append(CHARS.charAt(charIdx));
    }

    output.text(line.toString(), 0, row * charH);
  }

  output.endDraw();
}

void keyPressed() {
  if (key == 'r') {
    recording = true;
    frameCounter = 0;
    // Create output directory
    File dir = new File(sketchPath(outputDir));
    if (!dir.exists()) dir.mkdirs();
    println("Recording started...");
  }
  if (key == 's') {
    recording = false;
    println("Recording stopped. " + frameCounter + " frames saved.");
  }
}
