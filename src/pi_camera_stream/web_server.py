
from flask import Flask, Response, render_template_string, jsonify
import psutil
from .camera import CameraManager
import time
app = Flask(__name__)


camera_manager = CameraManager()
# ----------------------------------------------------------------------
# Streaming generator
# ----------------------------------------------------------------------
def generate_frames(camera_manager):
    if not camera_manager.is_available():
        error_msg = b"Camera not available"
        while True:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + error_msg + b"\r\n"
            )
            time.sleep(1)

    while True:
        frame = camera_manager.capture_frame()
        if frame is None:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
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
    global camera_manager
    """MJPEG video feed endpoint."""
    return Response(generate_frames(camera_manager),
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

