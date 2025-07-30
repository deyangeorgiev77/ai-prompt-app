
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil, os, zipfile

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate/")
async def generate(
    request: Request,
    start_number: int = Form(...),
    textfile: UploadFile = File(...),
    images: list[UploadFile] = File(...),
):
    upload_dir = BASE_DIR / "uploads"
    output_dir = BASE_DIR / "output"
    upload_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    # Save RTF/TXT file
    text_path = upload_dir / textfile.filename
    with open(text_path, "wb") as f:
        f.write(await textfile.read())

    # Save images
    image_paths = []
    for img in images:
        img_path = upload_dir / img.filename
        with open(img_path, "wb") as f:
            f.write(await img.read())
        image_paths.append(img_path)

    # Dummy processing step (create a result.txt file)
    result_path = output_dir / f"AI-video_{start_number:05d}.csv"
    with open(result_path, "w") as f:
        f.write("FileName,Title,Description,Headline,Keywords\n")
        for i, img in enumerate(image_paths):
            name = f"AI-video_{start_number + i:05d}.mp4"
            f.write(f"{name},Sample Title,Sample Description,Sample Headline,keyword1; keyword2\n")

    # Zip output
    zip_path = output_dir / "results.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.write(result_path, arcname=result_path.name)

    return FileResponse(zip_path, media_type="application/zip", filename="results.zip")
