
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import shutil
from pathlib import Path

app = FastAPI()
upload_dir = Path("uploaded_images")
upload_dir.mkdir(exist_ok=True)

app.mount("/images", StaticFiles(directory=upload_dir), name="images")

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
        <head>
            <title>AI Video Metadata Generator</title>
        </head>
        <body>
            <h1>Upload JPG Images and Submit Task</h1>
            <form action="/generate" enctype="multipart/form-data" method="post">
                <input name="files" type="file" accept=".jpg" multiple><br><br>
                <label>Starting number for filenames:</label>
                <input name="start_number" type="number" min="0" value="32000"><br><br>
                <textarea name="task" rows="15" cols="120" placeholder="Enter your task instructions here..."></textarea><br><br>
                <input type="submit" value="Generate">
            </form>
        </body>
    </html>
    """

@app.post("/generate")
async def generate(files: List[UploadFile] = File(...), task: str = Form(...), start_number: int = Form(...)):
    filenames = []
    for file in files:
        file_location = upload_dir / file.filename
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        filenames.append(file_location.name)

    return {
        "message": "Files uploaded successfully!",
        "images": [f"/images/{f}" for f in filenames],
        "start_number": start_number,
        "task_received": task
    }
