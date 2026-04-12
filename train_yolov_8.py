from ultralytics import YOLO
import torch
import multiprocessing
import json

DATA_YAML = "dataset/data.yaml"
MODEL_NAME = "yolov8m.pt"
#MODEL_NAME = "runs/flowers/weights/last.pt"
EPOCHS = 60
IMGSZ = 512
BATCH = 30
DEVICE = 0
PROJECT = "runs/"
NAME = "flowers"
WORKERS = 0


def main():
    print("CUDA доступно:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))

    model = YOLO(MODEL_NAME)

    model.train(
        data=DATA_YAML,
        epochs=EPOCHS,
        imgsz=IMGSZ,
        batch=BATCH,
        device=DEVICE,
        project=PROJECT,
        name=NAME,
        patience=30,
        cos_lr=True,
        plots=True,
        workers=WORKERS,
        #resume=True
    )

    print("\nОбучение!")
    print(f"Лучшая модель сохранена в: {PROJECT}/{NAME}/weights/best.pt")

    class_names = model.names

    with open(f"{PROJECT}/{NAME}/classes.json", "w", encoding="utf-8") as f:
        json.dump(class_names, f, ensure_ascii=False, indent=4)

    print("Классы сохранены рядом с моделью")


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()