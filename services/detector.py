import os
import json
import io
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont

# Проверяем наличие ultralytics для поддержки .pt
try:
    from ultralytics import YOLO

    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False

import onnxruntime as ort


class YOLOService:
    def __init__(self, pt_model="best.pt", onnx_model="best.onnx", classes_file="classes.json"):
        self.model_pt = None
        self.session_onnx = None
        self.classes = {}

        base_path = os.path.dirname(os.path.abspath(__file__))
        self.models_dir = os.path.join(base_path, "..", "models")

        pt_path = os.path.join(self.models_dir, pt_model)
        onnx_path = os.path.join(self.models_dir, onnx_model)
        classes_path = os.path.join(self.models_dir, classes_file)

        # 1. Пытаемся загрузить .pt (Приоритет)
        if HAS_ULTRALYTICS and os.path.exists(pt_path):
            try:
                self.model_pt = YOLO(pt_path)
                # Берем имена классов напрямую из модели
                self.classes = self.model_pt.names
                print(f"🚀 Запущено в режиме PyTorch (.pt): {pt_model}")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки .pt: {e}")

        # 2. Если .pt не загрузился, пробуем .onnx
        if self.model_pt is None and os.path.exists(onnx_path):
            try:
                opt = ort.SessionOptions()
                opt.intra_op_num_threads = 2
                self.session_onnx = ort.InferenceSession(onnx_path, sess_options=opt,
                                                         providers=['CPUExecutionProvider'])

                # Для ONNX нужны внешние классы
                if os.path.exists(classes_path):
                    with open(classes_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.classes = {int(k): v for k, v in data.items()}
                print(f"☁️ Запущено в режиме ONNX (.onnx): {onnx_model}")
            except Exception as e:
                print(f"❌ Ошибка инициализации ONNX: {e}")

    def predict(self, image_bytes: bytes):
        if self.model_pt:
            return self._predict_pt(image_bytes)
        elif self.session_onnx:
            return self._predict_onnx(image_bytes)
        else:
            return None, None, "Ни одна модель не загружена."

    def _predict_pt(self, image_bytes: bytes):
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            results = self.model_pt(np.array(img), conf=0.25, verbose=False)
            r = results[0]

            detections = []
            for box in r.boxes:
                cls_id = int(box.cls[0])
                detections.append({
                    "class_id": cls_id,
                    "class_name": self.classes.get(cls_id, str(cls_id)),
                    "confidence": round(float(box.conf[0]) * 100, 2),
                    "bbox": list(map(int, box.xyxy[0]))
                })

            return Image.fromarray(r.plot()), detections, None
        except Exception as e:
            return None, None, f"Ошибка PT: {e}"

    def _predict_onnx(self, image_bytes: bytes):
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            orig_w, orig_h = img.size
            input_size = 640

            # Подготовка
            img_resized = img.resize((input_size, input_size))
            img_np = np.array(img_resized).astype(np.float32) / 255.0
            img_np = np.transpose(img_np, (2, 0, 1))
            img_np = np.expand_dims(img_np, axis=0)

            outputs = self.session_onnx.run(None, {self.session_onnx.get_inputs()[0].name: img_np})
            output = outputs[0][0].transpose()

            detections = []
            for pred in output:
                scores = pred[4:]
                cls_id = np.argmax(scores)
                conf = scores[cls_id]
                if conf > 0.25:
                    xc, yc, w, h = pred[:4]
                    x1 = int((xc - w / 2) * (orig_w / input_size))
                    y1 = int((yc - h / 2) * (orig_h / input_size))
                    x2 = int((xc + w / 2) * (orig_w / input_size))
                    y2 = int((yc + h / 2) * (orig_h / input_size))
                    detections.append({
                        "class_id": int(cls_id),
                        "class_name": self.classes.get(int(cls_id), f"ID {cls_id}"),
                        "confidence": round(float(conf) * 100, 2),
                        "bbox": [x1, y1, x2, y2]
                    })

            detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)[:10]

            # Рисование с нормальным шрифтом
            draw = ImageDraw.Draw(img)
            # Авто-размер шрифта: 3% от высоты картинки
            font_size = max(20, int(orig_h * 0.03))

            try:
                font_path = os.path.join(os.path.dirname(__file__), "..", "static", "fonts", "GOTHIC.ttf")
                font = ImageFont.truetype(font_path, font_size)
            except:
                font = ImageFont.load_default()

            for det in detections:
                b = det['bbox']
                draw.rectangle(b, outline="#2d6a4f", width=max(3, int(orig_w / 200)))
                draw.text((b[0], b[1] - font_size - 5), f"{det['class_name']} {det['confidence']}%", fill="#2d6a4f",
                          font=font)

            return img, detections, None
        except Exception as e:
            return None, None, f"Ошибка ONNX: {e}"

    def delete_after_delay(self, file_path: str, delay: int = 3600):
        try:
            time.sleep(delay)
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass


detector_service = YOLOService()