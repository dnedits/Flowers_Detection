import os
import json
import io
import numpy as np
import time
import onnxruntime as ort
from PIL import Image


class YOLOService:
    def __init__(self, model_filename="best.onnx", classes_filename="classes.json"):
        self.session = None
        self.classes = {}
        base_path = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_path, "..", "models", model_filename)
        classes_path = os.path.join(base_path, "..", "models", classes_filename)

        if os.path.exists(model_path):
            try:
                self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
                if os.path.exists(classes_path):
                    with open(classes_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.classes = {int(k): v for k, v in data.items()}
                print(f"✅ ONNX модель загружена: {model_path}")
            except Exception as e:
                print(f"❌ Ошибка инициализации ONNX: {e}")
        else:
            print(f"⚠️ Файл модели .onnx НЕ найден: {model_path}")

    def predict(self, image_bytes: bytes):
        if self.session is None:
            return None, None, "Модель не инициализирована."

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            original_width, original_height = img.size

            img_resized = img.resize((640, 640))
            img_np = np.array(img_resized).astype(np.float32) / 255.0
            img_np = np.transpose(img_np, (2, 0, 1))  # HWC -> CHW
            img_np = np.expand_dims(img_np, axis=0)  # Добавляем batch dimension

            outputs = self.session.run(None, {self.session.get_inputs()[0].name: img_np})

            output = outputs[0][0]
            detections = []


            return img, detections, None

        except Exception as e:
            return None, None, str(e)

    def delete_after_delay(self, file_path: str, delay: int = 3600):
        try:
            time.sleep(delay)
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass


detector_service = YOLOService()