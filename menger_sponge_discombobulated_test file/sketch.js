/*by halfabluebanana*/

let boxes = [];
let NUM_BOXES = 50;

// Recording variables
let capturer = null;
let isRecording = false;
let frameCounter = 0;
let capturedFrames = [];
let lastCaptureTime = 0;
let captureInterval = 1000 / 30; // 30 fps
let recordingIndicator = null;

function setup() {
  createCanvas(2048, 2048, WEBGL);
  pixelDensity(Math.min(2, window.devicePixelRatio || 1));

  for (let i = 0; i < NUM_BOXES; i++) {
    boxes.push(new Box(random(-200, 200), random(-200, 200), random(-200, 200)));
  }
  
  // Add window-level keyboard listener
  if (!window.__recordingListenerAdded) {
    window.addEventListener('keydown', (e) => {
      if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        if (e.key === 'r' || e.key === 'R') {
          e.preventDefault();
          startRecording();
        }
        if (e.key === 's' || e.key === 'S') {
          e.preventDefault();
          stopRecording();
        }
      }
    });
    window.__recordingListenerAdded = true;
  }
  
  console.log('Setup complete. Press R to record, S to stop.');
}

function keyPressed() {
  if (key === 'r' || key === 'R') {
    startRecording();
    return false;
  }
  if (key === 's' || key === 'S') {
    stopRecording();
    return false;
  }
}

function draw() {
  background(0);

  orbitControl(); // optional

  for (let b of boxes) {
    b.update();
    b.draw();
  }
  
  // Capture frame at end of draw
  captureFrame();
}

function windowResized() {
  resizeCanvas(windowWidth, windowHeight);
}

// Recording functions
function startRecording() {
  capturedFrames = [];
  isRecording = true;
  frameCounter = 0;
  lastCaptureTime = millis() - captureInterval;
  
  if (!capturer) {
    capturer = new CCapture({
      format: 'png',
      framerate: 30,
      name: 'p5_frames',
      quality: 100,
      verbose: true
    });
  }
  
  // Create visual indicator
  if (!recordingIndicator) {
    recordingIndicator = document.createElement('div');
    recordingIndicator.id = 'recording-indicator';
    recordingIndicator.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: rgba(255, 0, 0, 0.8);
      color: white;
      padding: 10px 15px;
      border-radius: 5px;
      font-family: monospace;
      font-size: 14px;
      z-index: 10000;
      pointer-events: none;
    `;
    document.body.appendChild(recordingIndicator);
  }
  recordingIndicator.style.display = 'block';
  updateRecordingIndicator();
  
  if (window.indicatorUpdateInterval) {
    clearInterval(window.indicatorUpdateInterval);
  }
  window.indicatorUpdateInterval = setInterval(() => {
    if (isRecording) {
      updateRecordingIndicator();
    }
  }, 200);
  
  console.log('Recording started...');
}

function stopRecording() {
  if (isRecording) {
    isRecording = false;
    
    if (window.indicatorUpdateInterval) {
      clearInterval(window.indicatorUpdateInterval);
      window.indicatorUpdateInterval = null;
    }
    
    if (recordingIndicator) {
      recordingIndicator.style.display = 'none';
    }
    
    console.log(`Recording stopped. ${frameCounter} frames (${capturedFrames.length} captured)...`);
    packageFrames();
  }
}

function updateRecordingIndicator() {
  if (recordingIndicator && isRecording) {
    recordingIndicator.textContent = `● REC ${frameCounter} frames (${capturedFrames.length} captured)`;
  }
}

async function packageFrames() {
  if (capturedFrames.length === 0) {
    console.log('No frames captured.');
    return;
  }
  
  console.log(`Packaging ${capturedFrames.length} frames...`);
  
  if (window.Tar) {
    const tape = new window.Tar();
    
    const promises = capturedFrames.map((blob, index) => {
      const fileName = `frame_${String(index).padStart(6, '0')}.png`;
      
      let bufferPromise;
      if (blob.arrayBuffer) {
        bufferPromise = blob.arrayBuffer();
      } else {
        bufferPromise = new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result);
          reader.onerror = reject;
          reader.readAsArrayBuffer(blob);
        });
      }
      
      return bufferPromise.then(buffer => {
        tape.append(fileName, new Uint8Array(buffer));
      }).catch(err => {
        console.error(`Error processing frame ${index}:`, err);
      });
    });
    
    Promise.all(promises).then(() => {
      const tarBlob = tape.save();
      const url = URL.createObjectURL(tarBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'p5_frames.tar';
      a.click();
      URL.revokeObjectURL(url);
      console.log(`Saved ${capturedFrames.length} frames to p5_frames.tar`);
    });
  } else {
    console.error('Tar library not available.');
  }
}

function captureFrame() {
  if (!isRecording) return;
  
  let canvasElement = null;
  if (canvas && canvas.elt) {
    canvasElement = canvas.elt;
  } else {
    const canvases = document.querySelectorAll('canvas');
    if (canvases.length > 0) {
      canvasElement = canvases[0];
    }
  }
  
  if (!canvasElement) return;
  
  if (width <= 0 || height <= 0) return;
  
  const now = millis();
  if (now - lastCaptureTime >= captureInterval) {
    try {
      if (canvasElement && typeof canvasElement.toBlob === 'function') {
        canvasElement.toBlob((blob) => {
          if (blob && blob.size > 100) {
            capturedFrames.push(blob);
            frameCounter++;
            lastCaptureTime = now;
            
            if (frameCounter <= 5 || frameCounter % 10 === 0) {
              console.log(`✓ Captured frame ${frameCounter}, total: ${capturedFrames.length} frames`);
            }
          }
        }, 'image/png');
        lastCaptureTime = now;
      }
    } catch (e) {
      console.error('Capture error:', e);
    }
  }
}
