import os
from ultralytics import YOLO
from PIL import Image

class ProductDetector:
    def __init__(self):
        # Resolve the path to best.pt relative to this file's location
        model_path = os.path.join(os.path.dirname(__file__), "..", "runs", "detect", "train6", "weights", "best.pt")
        model_path = os.path.abspath(model_path)

        if not os.path.exists(model_path) or os.path.getsize(model_path) == 0:
            raise FileNotFoundError(f"❌ Model file not found or corrupted at: {model_path}")
        
        try:
            self.model = YOLO(model_path)
        except Exception as e:
            raise RuntimeError(f"❌ Failed to load model: {e}")

    def detect(self, image_path):
        try:
            results = self.model.predict(image_path, conf=0.4, verbose=False)

            if not results or len(results[0].boxes) == 0:
                return None, None

            result = results[0]
            class_id = int(result.boxes.cls[0])
            label = self.model.names[class_id]
            confidence = float(result.boxes.conf[0])
            return label, confidence
        except Exception as e:
            print(f"❌ Detection error: {e}")
            return None, None
