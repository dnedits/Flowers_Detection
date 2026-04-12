import os
import uuid
from fastapi import FastAPI, File, UploadFile, Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from services.detector import detector_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Web-сайт детектирования")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "classes": detector_service.classes,
        "model_loaded": detector_service.session is not None
    })

@app.post("/predict_image")
async def predict(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    contents = await file.read()

    annotated_img, detections, error = detector_service.predict(contents)

    if error:
        return templates.TemplateResponse(request, "result.html", {"error": error})

    res_dir = os.path.join(BASE_DIR, "static", "results", "web")
    os.makedirs(res_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.jpg"
    res_path = os.path.join(res_dir, filename)

    annotated_img.save(res_path)

    background_tasks.add_task(detector_service.delete_after_delay, res_path, 3600)

    return templates.TemplateResponse(request, "result.html", {
        "image_url": f"/static/results/web/{filename}",
        "detections": detections,
        "filename": file.filename,
        "count": len(detections)
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)