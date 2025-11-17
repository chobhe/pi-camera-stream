import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
import numpy as np
import pathlib
import hailo
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from detection_pipeline import GStreamerDetectionApp
from queue import Queue
import cv2

# Global variable to store detection frames
detection_frames_queue = Queue(maxsize=10) # Queue to store detection frames
detection_app = None 


# User-defined class to be used in the callback function: Inheritance from the app_callback_class
class user_app_callback_class(app_callback_class):

    def detect_target(self, frame):
        # TODO: Detect Target(James) and return whether the target is detected
        pass
       

# User-defined callback function: This is the callback function that will be called when data is available from the pipeline
def app_callback(pad, info, user_data):
    buffer = info.get_buffer()  # Get the GstBuffer from the probe info
    if buffer is None:  # Check if the buffer is valid
        return Gst.PadProbeReturn.OK
    
    user_data.increment()  # Using the user_data to count the number of frames

    # Get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    # Parse the detections
    for detection in detections:
        track_id = 0
        track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
        if len(track) > 0:
            track_id = track[0].get_id()
       
        print(f'Frame {user_data.frame_count}, Detection {detection.get_label()} ({track_id})')


     # Extract frame from buffer and add to queue for Flask to serve
    try:
        # Map the buffer to get access to the data
        success, map_info = buffer.map(Gst.MapFlags.READ)
        if success:
            # Get frame data - this depends on your pipeline format
            # Assuming RGB format, adjust if different
            width = roi.get_width()
            height = roi.get_height()
            
            # Create numpy array from buffer data
            frame_data = np.frombuffer(map_info.data, dtype=np.uint8)
            frame = frame_data.reshape((height, width, 3)) # Reshaping for RGB format
            
            # Encode frame as JPEG
            _, jpeg_frame = cv2.imencode('.jpg', frame)
            frame_bytes = jpeg_frame.tobytes()
            
            # Put frame in queue (non-blocking, drop if queue is full)
            if not detection_frames_queue.full():
                detection_frames_queue.put(frame_bytes)
            
            buffer.unmap(map_info)
    except Exception as e:
        print(f"Error extracting frame: {e}")

    return Gst.PadProbeReturn.OK


def start_detection_pipeline():
    """Start the detection pipeline in a background thread"""
    global detection_app
    user_data = user_app_callback_class()
    detection_app = GStreamerDetectionApp(
        app_callback, 
        user_data, 
        pathlib.Path(__file__).parent.resolve()
    )
    detection_app.run()

