import os
import json
import io
import numpy as np
import time
import onnxruntime as ort
from PIL import Image, ImageDraw


class YOLOService:
    def __init__(self, model_filename="best.onnx", classes_filename="classes.json"):
        self.session = None
        self.classes = {}
        base_path = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_path, "..", "models", model_filename)
        classes_path = os.path.join(base_path, "..", "models", classes_filename)

        if os.path.exists(model_path):
            try:
                options = ort.SessionOptions()
                options.intra_op_num_threads = 2
                options.inter_op_num_threads = 2

                self.session = ort.InferenceSession(
                    model_path,
                    sess_options=options,
                    providers=['CPUExecutionProvider']
                )

                if os.path.exists(classes_path):
                    with open(classes_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.classes = {int(k): v for k, v in data.items()}
                print(f"✅ ONNX модель (640) загружена: {model_path}")
            except Exception as e:
                print(f"❌ Ошибка инициализации ONNX: {e}")
        else:
            print(f"⚠️ Файл модели .onnx НЕ найден: {model_path}")

    def predict(self, image_bytes: bytes):
        if self.session is None:
            return None, None, "Модель не инициализирована."

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
            orig_w, orig_h = img.size

            input_size = 640
            img_resized = img.resize((input_size, input_size))
            img_np = np.array(img_resized).astype(np.float32) / 255.0
            img_np = np.transpose(img_np, (2, 0, 1))
            img_np = np.expand_dims(img_np, axis=0)

            outputs = self.session.run(None, {self.session.get_inputs()[0].name: img_np})

            output = outputs[0][0]
            output = output.transpose()

            detections = []
            conf_threshold = 0.25

            for pred in output:
                scores = pred[4:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                if confidence > conf_threshold:
                    xc, yc, w, h = pred[:4]

                    x1 = (xc - w / 2) * (orig_w / input_size)
                    y1 = (yc - h / 2) * (orig_h / input_size)
                    x2 = (xc + w / 2) * (orig_w / input_size)
                    y2 = (yc + h / 2) * (orig_h / input_size)

                    detections.append({
                        "class_id": int(class_id),
                        "class_name": self.classes.get(int(class_id), f"ID {class_id}"),
                        "confidence": round(float(confidence) * 100, 2),
                        "bbox": [int(x1), int(y1), int(x2), int(y2)]
                    })

            detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)[:15]

            draw = ImageDraw.Draw(img)
            for det in detections:
                box = det['bbox']
                draw.rectangle(box, outline="green", width=4)

                text = f"{det['class_name']} {det['confidence']}%"
                draw.text((box[0] + 5, box[1] + 5), text, fill="green")

            return img, detections, None

        except Exception as e:
            return None, None, f"Ошибка детекции: {str(e)}"

    def delete_after_delay(self, file_path: str, delay: int = 3600):
        try:
            time.sleep(delay)
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass


detector_service = YOLOService()