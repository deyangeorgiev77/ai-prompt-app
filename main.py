from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os
from typing import List

app = FastAPI()

# Allow all CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")

@app.get("/", response_class=HTMLResponse)
def form():
    return """
    <html>
        <head>
            <title>AI Prompt Generator</title>
        </head>
        <body>
            <h1>Upload JPG Images and Submit Task</h1>
            <form action="/generate" enctype="multipart/form-data" method="post">
                <input type="file" name="files" accept=".jpg" multiple required><br><br>
                <textarea name="task" rows="10" cols="80" placeholder="Enter your task instructions here..." required></textarea><br><br>
                <input type="submit" value="Generate">
            </form>
        </body>
    </html>
    """

@app.post("/generate")
def generate(files: List[UploadFile] = File(...), task: str = Form(...)):
    image_names = []
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        image_names.append(file.filename)

    return {
        "message": "Files uploaded successfully!",
        "images": [f"/images/{img}" for img in image_names],
        "task_received": task
    }
