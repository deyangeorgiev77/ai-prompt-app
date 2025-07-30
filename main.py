from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List
import shutil
import os

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process/")
async def handle_upload(
    request: Request,
    start_number: int = Form(...),
    template: str = Form(...),
    text_file: UploadFile = File(...),
    images: List[UploadFile] = File(...)
):
    output_dir = BASE_DIR / "outputs"
    output_dir.mkdir(exist_ok=True)

    text_path = UPLOAD_DIR / text_file.filename
    with open(text_path, "wb") as f:
        shutil.copyfileobj(text_file.file, f)

    image_paths = []
    for img in images:
        img_path = UPLOAD_DIR / img.filename
        with open(img_path, "wb") as f:
            shutil.copyfileobj(img.file, f)
        image_paths.append(img_path)

    # Dummy HTML generation placeholder
    html_content = "<h2>Uploaded files processed.</h2><ul>"
    html_content += f"<li>Start number: {start_number}</li>"
    html_content += f"<li>Template content: {template[:100]}...</li>"
    html_content += f"<li>Text file: {text_file.filename}</li>"
    html_content += "<li>Images:</li><ul>"
    for img in image_paths:
        html_content += f"<li>{img.name}</li>"
    html_content += "</ul></ul>"

    return HTMLResponse(content=html_content)
