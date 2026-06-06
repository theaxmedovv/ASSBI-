# ============================================================
#  YOLO Car Detector — Dataset & Training Script
#  Dataset source: Roboflow (custom annotated street footage)
# ============================================================

from roboflow import Roboflow
from ultralytics import YOLO
import os

# ── Step 1: Download dataset from Roboflow ──────────────────
rf = Roboflow(api_key="lmn7LAqK1tASk39hrm6S")  # replace with your key
project = rf.workspace("abdulazizs-workspace-uoqvg").project("car-detector")
version = project.version(1)
dataset = version.download("yolov11")

print(f"[DATASET] Downloaded to: {dataset.location}")

# ── Step 2: Train YOLO model ────────────────────────────────
model = YOLO("yolo11n.pt")  # start from pretrained nano weights

results = model.train(
    data=os.path.join(dataset.location, "data.yaml"),
    epochs=50,
    imgsz=640,
    batch=16,
    name="car_detector",
    patience=10,        # stop early if no improvement
    save=True,
    plots=True,
)

print("[TRAINING] Done!")
print(f"[MODEL] Best weights saved to: runs/detect/car_detector/weights/best.pt")

# ── Step 3: Validate the model ──────────────────────────────
metrics = model.val()
print(f"[VALIDATION] mAP50: {metrics.box.map50:.3f}")
print(f"[VALIDATION] mAP50-95: {metrics.box.map:.3f}")

# ── Step 4: Test on a sample image ─────────────────────────
# model.predict("test_image.jpg", save=True, conf=0.25)