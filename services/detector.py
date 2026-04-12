import os
import json
import io
import numpy as np
import time
from PIL import Image, ImageDraw

CLASS_COLORS = {
    "Ромашка": "#e2e2e2",     # Светло-серый (белый)
    "Одуванчик": "#f9d71c",   # Желтый
    "Роза": "#e63946",        # Красный
    "Подсолнечник": "#ffb703", # Оранжево-желтый
    "Тюльпан": "#ff4d6d"      # Розовый
}
DEFAULT_COLOR = "#2d6a4f"

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
        models_dir = os.path.join(base_path, "..", "models")

        pt_path = os.path.join(models_dir, pt_model)
        onnx_path = os.path.join(models_dir, onnx_model)
        classes_path = os.path.join(models_dir, classes_file)

        if HAS_ULTRALYTICS and os.path.exists(pt_path):
            try:
                self.model_pt = YOLO(pt_path)
                self.classes = self.model_pt.names
                print(f"✅ Режим PyTorch (.pt) активен")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки .pt: {e}")

        if self.model_pt is None and os.path.exists(onnx_path):
            try:
                opt = ort.SessionOptions()
                opt.intra_op_num_threads = 2
                self.session_onnx = ort.InferenceSession(onnx_path, sess_options=opt,
                                                         providers=['CPUExecutionProvider'])
                if os.path.exists(classes_path):
                    with open(classes_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.classes = {int(k): v for k, v in data.items()}
                print(f"✅ Режим ONNX активен")
            except Exception as e:
                print(f"❌ Ошибка ONNX: {e}")

    @property
    def is_loaded(self):
        return self.model_pt is not None or self.session_onnx is not None

    def predict(self, image_bytes: bytes):
        if self.model_pt:
            return self._predict_pt(image_bytes)
        elif self.session_onnx:
            return self._predict_onnx(image_bytes)
        return None, None, "Модель не загружена"

    def _predict_pt(self, image_bytes: bytes):
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            results = self.model_pt(np.array(img), conf=0.25, verbose=False)
            r = results[0]
            detections = [{"class_id": int(box.cls[0]),
                           "class_name": self.classes.get(int(box.cls[0]), "Unknown"),
                           "confidence": round(float(box.conf[0]) * 100, 2),
                           "bbox": list(map(int, box.xyxy[0]))} for box in r.boxes]
            return Image.fromarray(r.plot()), detections, None
        except Exception as e:
            return None, None, str(e)

    def _predict_onnx(self, image_bytes: bytes):
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            orig_w, orig_h = img.size
            img_resized = img.resize((640, 640))
            img_np = np.array(img_resized).astype(np.float32) / 255.0
            img_np = np.transpose(img_np, (2, 0, 1))
            img_np = np.expand_dims(img_np, axis=0)

            outputs = self.session_onnx.run(None, {self.session_onnx.get_inputs()[0].name: img_np})
            output = outputs[0][0].transpose()

            raw_detections = []
            for pred in output:
                scores = pred[4:]
                cls_id = np.argmax(scores)
                conf = scores[cls_id]
                if conf > 0.30:
                    xc, yc, w, h = pred[:4]
                    raw_detections.append({
                        "class_name": self.classes.get(int(cls_id), f"ID {cls_id}"),
                        "confidence": round(float(conf) * 100, 1),
                        "bbox": [int((xc - w / 2) * (orig_w / 640)), int((yc - h / 2) * (orig_h / 640)),
                                 int((xc + w / 2) * (orig_w / 640)), int((yc + h / 2) * (orig_h / 640))]
                    })

            # NMS (фильтрация дублей)
            detections = []
            raw_detections.sort(key=lambda x: x['confidence'], reverse=True)
            for d in raw_detections:
                is_duplicate = False
                for final_d in detections:
                    if self._iou(d['bbox'], final_d['bbox']) > 0.45:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    detections.append(d)

            draw = ImageDraw.Draw(img)

            # Попытка загрузить шрифт (если нет, будет стандартный)
            try:
                # Путь к твоему Gothic.ttf
                font_path = os.path.join(os.path.dirname(__file__), "..", "web", "static", "fonts", "GOTHIC.TTF")
                font = ImageFont.truetype(font_path, size=max(18, int(orig_w / 40)))
            except:
                font = ImageFont.load_default()

            for det in detections[:15]:
                name = det['class_name']
                color = CLASS_COLORS.get(name, DEFAULT_COLOR)
                bbox = det['bbox']
                label = f"{name} {det['confidence']}%"

                # 1. Рисуем основную рамку объекта
                draw.rectangle(bbox, outline=color, width=4)

                # 2. Вычисляем размер текста для подложки
                text_bbox = draw.textbbox((bbox[0], bbox[1]), label, font=font)

                # 3. Рисуем закрашенный прямоугольник под текст (как в YOLO)
                draw.rectangle([text_bbox[0], text_bbox[1] - 5, text_bbox[2] + 5, text_bbox[3]], fill=color)

                # 4. Рисуем белый текст поверх цветной подложки
                draw.text((bbox[0] + 2, bbox[1] - font.size), label, fill="white", font=font)

            return img, detections, None
        except Exception as e:
            return None, None, str(e)

    def _iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
        boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
        boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
        return interArea / float(boxAArea + boxBArea - interArea)

    def delete_after_delay(self, file_path: str, delay: int = 3600):
        time.sleep(delay)
        if os.path.exists(file_path): os.remove(file_path)


detector_service = YOLOService()