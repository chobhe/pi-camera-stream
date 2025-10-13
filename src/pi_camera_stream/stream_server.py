"""
Flask-based live MJPEG video streamer for Raspberry Pi Camera Module 3.
Works inside a Poetry-managed environment using:
  - picamera2 >= 0.3.31
  - flask >= 3.1.0
  - av == 15.1.0 (built from source)
"""

from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
import io
import time

app = Flask(__name__)

# Try to initialize the camera safely (so app still runs if cam absent)
picam2 = None
try:
    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(main={"size": (1280, 720)})
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

    stream = io.BytesIO()
    while True:
        stream.seek(0)
        stream.truncate()
        picam2.capture_file(stream, format="jpeg")
        frame = stream.getvalue()
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
        </style>
      </head>
      <body>
        <h1>📷 Raspberry Pi Camera Stream</h1>
        <img src="{{ url_for('video_feed') }}" width="720" />
      </body>
    </html>
    """
    return render_template_string(html)


@app.route("/video_feed")
def video_feed():
    """MJPEG video feed endpoint."""
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main():
    print("[INFO] Starting Flask server on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, threaded=True)


if __name__ == "__main__":
    main()