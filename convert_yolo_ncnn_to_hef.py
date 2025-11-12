from ultralytics import YOLO
from pathlib import Path
import subprocess, onnx, os

PROJECT_ROOT = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
onnx_path = PROJECT_ROOT / "yolov8n.onnx"
hef_path = PROJECT_ROOT / "yolov8n.hef"

# Export to ONNX
if not onnx_path.exists():
    print("[INFO] Exporting YOLOv8n to ONNX...")
    model = YOLO("yolov8n.pt")
    model.export(format="onnx", imgsz=640, opset=13, simplify=True, name=str(onnx_path))

# Verify ONNX
onnx_model = onnx.load(str(onnx_path))
input_tensor = onnx_model.graph.input[0]
shape = [d.dim_value or "?" for d in input_tensor.type.tensor_type.shape.dim]
print(f"[INFO] Input tensor: {input_tensor.name}, shape: {shape}")

# Compile with Hailo
try:
    result = subprocess.run([
        "hailo",
        "compile",
        str(onnx_path),
        "--hw-arch", "hailo8",
        "--output", str(hef_path),
        "--input-format", "nhwc",
        "--input-shape", "1,640,640,3"
    ], check=True, capture_output=True, text=True)
    print("[SUCCESS] Compilation complete.")
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("[ERROR] Compilation failed:")
    print(e.stdout, e.stderr)
except FileNotFoundError:
    print("[ERROR] 'hailo' CLI not found in PATH.")