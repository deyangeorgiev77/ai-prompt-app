
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import os

app = FastAPI()

# Създаване на папка за качени файлове
os.makedirs("uploaded_images", exist_ok=True)
os.makedirs("uploaded_rtf", exist_ok=True)

# Монтиране на папката за изображения като статични файлове
app.mount("/static", StaticFiles(directory="uploaded_images"), name="static")

# Задаване на директорията за шаблони
templates = Jinja2Templates(directory="templates")

# Начална страница - зарежда index.html
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Рут за обработка на формата
@app.post("/process/")
async def process_form(
    request: Request,
    start_number: int = Form(...),
    rtf_file: UploadFile = File(...),
    images: List[UploadFile] = File(...)
):
    # Запазване на .rtf/.txt файла
    rtf_path = os.path.join("uploaded_rtf", rtf_file.filename)
    with open(rtf_path, "wb") as f:
        f.write(await rtf_file.read())

    # Запазване на JPG файловете
    saved_filenames = []
    current_number = start_number
    for image in images:
        filename = f"AI_{current_number}.jpg"
        path = os.path.join("uploaded_images", filename)
        with open(path, "wb") as f:
            f.write(await image.read())
        saved_filenames.append(filename)
        current_number += 1

    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": f"Успешно качени {len(saved_filenames)} снимки и {rtf_file.filename}."
    })
