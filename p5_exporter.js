/**
 * p5.js PNG Sequence Exporter
 *
 * Add this to your sketch to export frames.
 * Press 'r' to start recording, 's' to stop.
 *
 * Uses CCapture.js for fast frame capture.
 * Include: <script src="https://cdn.jsdelivr.net/npm/ccapture.js@1.1.0/build/CCapture.all.min.js"></script>
 */

let capturer = null;
let isRecording = false;
let frameCounter = 0;

function setupExporter() {
  capturer = new CCapture({
    format: 'png',
    framerate: 30,
    name: 'p5_frames',
    quality: 100,
    verbose: true
  });
}

function startRecording() {
  if (!capturer) setupExporter();
  capturer.start();
  isRecording = true;
  frameCounter = 0;
  console.log('Recording started...');
}

function stopRecording() {
  if (isRecording) {
    capturer.stop();
    capturer.save();
    isRecording = false;
    console.log(`Recording stopped. ${frameCounter} frames captured.`);
  }
}

function captureFrame() {
  if (isRecording && capturer) {
    capturer.capture(document.getElementById('defaultCanvas0'));
    frameCounter++;
  }
}

// Add to your keyPressed function:
// if (key === 'r') startRecording();
// if (key === 's') stopRecording();

// Add at end of draw():
// captureFrame();


/* ============================================
   ALTERNATIVE: Simple built-in method (slower)
   ============================================ */

let simpleRecording = false;
let simpleFrameCount = 0;

function toggleSimpleRecord() {
  simpleRecording = !simpleRecording;
  if (simpleRecording) {
    simpleFrameCount = 0;
    console.log('Simple recording started...');
  } else {
    console.log(`Stopped. ${simpleFrameCount} frames saved.`);
  }
}

function simpleCapture() {
  if (simpleRecording) {
    saveCanvas(`frame_${nf(simpleFrameCount, 6)}`, 'png');
    simpleFrameCount++;
  }
}

// Usage in draw():
// simpleCapture();
