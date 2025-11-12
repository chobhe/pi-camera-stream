"""Camera initialization and frame capture."""
from picamera2 import Picamera2
import io
import numpy as np
import cv2
from ultralytics import YOLO
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "yolov8n_ncnn_model"

class CameraManager:
    def __init__(self):
        self.picam2 = None
        self._initialize()
        self.model = YOLO(str(MODEL_PATH), verbose=False)
    
    def _initialize(self):
        # Camera initialization logic
        try:
            self.picam2 = Picamera2()
            video_config = self.picam2.create_video_configuration(main={"size": (1920, 1080)})
            self.picam2.configure(video_config)
            self.picam2.start()
            print("[INFO] Camera initialized successfully.")
        except Exception as e:
            print(f"[WARN] Could not initialize camera: {e}")
            self.picam2 = None
    
    def capture_frame(self):
        # Frame capture logic
        if not self.picam2:
            return None

        stream = io.BytesIO()
        stream.seek(0)
        stream.truncate()
        self.picam2.capture_file(stream, format="jpeg")
        frame = stream.getvalue()

        # Convert JPEG data to OpenCV format
        np_arr = np.frombuffer(frame, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        # Perform object detection
        results = self.model(img)
        annotated_frame = results[0].plot()
        
        # Encode image back to JPEG  
        _, annotated_frame_jpeg = cv2.imencode('.jpg', annotated_frame)
        return annotated_frame_jpeg.tobytes()
    
    def is_available(self):
        return self.picam2 is not None