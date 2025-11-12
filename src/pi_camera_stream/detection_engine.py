# Import necessary classes and pipeline helpers
from hailo_apps.hailo_gstreamer.gstreamer_app import GStreamerApp
from hailo_apps.hailo_gstreamer.gstreamer_helper_pipelines import (
    SOURCE_PIPELINE, INFERENCE_PIPELINE, DISPLAY_PIPELINE
)
from pathlib import Path
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "yolov8n_ncnn_model"

# 1. Create a class that inherits from GStreamerApp
class GStreamerDetectionApp(GStreamerApp):
    def __init__(self, args, user_data):
        # Call the parent constructor
        super().__init__(args, user_data)

        # Set up application-specific properties
        self.hef_path = MODEL_PATH
        self.post_process_so = "path/to/your/postprocess.so"
        # ... other parameters

    # 2. Override this method to define your pipeline
    def get_pipeline_string(self):
        # Use helper functions to build the pipeline components
        source = SOURCE_PIPELINE(video_source=self.video_source, ...)
        infer = INFERENCE_PIPELINE(hef_path=self.hef_path, ...)
        display = DISPLAY_PIPELINE(...)

        # Link the components together with '!'
        pipeline_string = f"{source} ! {infer} ! {display}"
        print(pipeline_string)
        return pipeline_string