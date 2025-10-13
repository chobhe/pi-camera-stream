"""
Flask-based live MJPEG video streamer for Raspberry Pi Camera Module 3.
Works inside a Poetry-managed environment using:
  - picamera2 >= 0.3.31
  - flask >= 3.1.0
  - av == 15.1.0 (built from source)
"""

from flask import Flask, Response, render_template_string, jsonify
from picamera2 import Picamera2
import io
import time
import psutil
from ultralytics import YOLO
import numpy as np  
import cv2         

app = Flask(__name__)

# Try to initialize the camera safely (so app still runs if cam absent)
picam2 = None
try:
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(main={"size": (1920, 1080)})
    picam2.configure(video_config)
    picam2.start()
    print("[INFO] Camera initialized successfully.")
except Exception as e:
    print(f"[WARN] Could not initialize camera: {e}")
    picam2 = None


# ----------------------------------------------------------------------
# Streaming generator
# ----------------------------------------------------------------------
def generate_frames():
    """Continuously capture JPEG frames from the camera and yield them."""
    if not picam2:
      # If camera missing, yield a blank placeholder every few seconds
      while True:
          time.sleep(1)
          yield (
              b"--frame\r\n"
              b"Content-Type: image/jpeg\r\n\r\n" +
              open("/usr/share/icons/Adwaita/256x256/status/dialog-error.png", "rb").read() +
              b"\r\n"
          )

    model = YOLO("yolov8n_ncnn_model", verbose=False)
    stream = io.BytesIO()
    while True:
      stream.seek(0)
      stream.truncate()
      picam2.capture_file(stream, format="jpeg")
      frame = stream.getvalue()

      # Convert JPEG data to OpenCV format
      np_arr = np.frombuffer(frame, np.uint8)
      img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
      
      # Perform object detection
      results = model(img)
      annotated_frame = results[0].plot()
      
      # Encode image back to JPEG
      _, annotated_frame_jpeg = cv2.imencode('.jpg', annotated_frame)

      yield (
          b"--frame\r\n"
          b"Content-Type: image/jpeg\r\n\r\n" + annotated_frame_jpeg.tobytes() + b"\r\n"
      )


# ----------------------------------------------------------------------
# Flask routes
# ----------------------------------------------------------------------
@app.route("/")
def index():
    """Main page with embedded video feed."""
    html = """
    <html>
      <head>
        <title>Raspberry Pi Live Stream</title>
        <style>
          body { background:#111; color:#eee; text-align:center; font-family:sans-serif; }
          img { border-radius:10px; margin-top:20px; box-shadow:0 0 20px #000; }
          .stats { 
            display: flex; 
            justify-content: center; 
            gap: 30px; 
            margin: 20px 0; 
            font-size: 18px;
          }
          .stat-box { 
            background: #333; 
            padding: 15px; 
            border-radius: 8px; 
            min-width: 150px;
          }
          .stat-value { 
            font-size: 24px; 
            font-weight: bold; 
            color: #4CAF50; 
          }
          .temp-normal { color: #4CAF50; }
          .temp-warm { color: #FF9800; }
          .temp-hot { color: #F44336; }
        </style>
      </head>
      <body>
        <h1>📷 Raspberry Pi Camera Stream</h1>
        <div class="stats">
          <div class="stat-box">
            <div>CPU Usage</div>
            <div class="stat-value" id="cpu">--%</div>
          </div>
          <div class="stat-box">
            <div>Memory Usage</div>
            <div class="stat-value" id="memory">--%</div>
          </div>
          <div class="stat-box">
            <div>Memory Used</div>
            <div class="stat-value" id="memory-used">-- GB</div>
          </div>
          <div class="stat-box">
            <div>CPU Temperature</div>
            <div class="stat-value" id="temp">--°C</div>
          </div>
        </div>
        <img src="{{ url_for('video_feed') }}" width="1080" />
        
        <script>
          function updateStats() {
            fetch('/stats')
              .then(response => response.json())
              .then(data => {
                document.getElementById('cpu').textContent = data.cpu_percent.toFixed(1) + '%';
                document.getElementById('memory').textContent = data.memory_percent.toFixed(1) + '%';
                document.getElementById('memory-used').textContent = data.memory_used_gb + ' / ' + data.memory_total_gb + ' GB';
                document.getElementById('temp').textContent = (data.cpu_temp ? data.cpu_temp + '°C' : 'N/A');
              })
              .catch(error => console.error('Error fetching stats:', error));
          }
          
          // Update stats every 2 seconds
          updateStats();
          setInterval(updateStats, 2000);
        </script>
      </body>
    </html>
    """
    return render_template_string(html)


@app.route("/video_feed")
def video_feed():
    """MJPEG video feed endpoint."""
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/stats")
def stats():
    """System statistics endpoint."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Get CPU temperature
    temps = psutil.sensors_temperatures()
    cpu_temp = None
    if 'cpu_thermal' in temps:
        cpu_temp = temps['cpu_thermal'][0].current
    elif 'coretemp' in temps:
        cpu_temp = temps['coretemp'][0].current
    
    return jsonify({
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_used_gb": round(memory.used / (1024**3), 2),
        "memory_total_gb": round(memory.total / (1024**3), 2),
        "cpu_temp": round(cpu_temp, 1) if cpu_temp else None
    })


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main():
    print("[INFO] Starting Flask server on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True)


if __name__ == "__main__":
    main()