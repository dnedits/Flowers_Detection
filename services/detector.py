import os
import json
import io
import numpy as np
import time
from ultralytics import YOLO
from PIL import Image


class YOLOService:
    def __init__(self, model_filename="best.pt", classes_filename="classes.json"):
        self.model = None
        self.classes = {}

        base_path = os.path.dirname(os.path.abspath(__file__))

        model_path = os.path.join(base_path, "..", "models", model_filename)
        classes_path = os.path.join(base_path, "..", "models", classes_filename)

        if os.path.exists(model_path):
            try:
                self.model = YOLO(model_path)
                if os.path.exists(classes_path):
                    with open(classes_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.classes = {int(k): v for k, v in data.items()}
                print(f"✅ YOLO модель загружена: {model_path}")
            except Exception as e:
                print(f"❌ Ошибка инициализации модели: {e}")
        else:
            print(f"⚠️ Файл модели НЕ найден по пути: {model_path}")

    def predict(self, image_bytes: bytes):
        if self.model is None:
            return None, None, "Модель нейросети не инициализирована."

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            img_np = np.array(img)

            results = self.model(
                img_np,
                conf=0.05,
                iou=0.25,
                max_det=1000,
                save=False,
                verbose=False
            )

            r = results[0]
            detections = []

            if r.boxes is not None:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    detections.append({
                        "class_id": cls_id,
                        "class_name": self.classes.get(cls_id, str(cls_id)),
                        "confidence": round(conf * 100, 2),
                        "bbox": [x1, y1, x2, y2]
                    })

            annotated_img_np = r.plot()
            annotated_img = Image.fromarray(annotated_img_np)

            return annotated_img, detections, None

        except Exception as e:
            return None, None, str(e)

    def delete_after_delay(self, file_path: str, delay: int = 3600):
        try:
            time.sleep(delay)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑 Удалён файл: {file_path}")
        except Exception as e:
            print(f"Ошибка удаления файла: {e}")


detector_service = YOLOService()