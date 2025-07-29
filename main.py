
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import shutil
import pandas as pd

app = FastAPI()

# Static for uploaded images
if not os.path.exists("uploaded_images"):
    os.makedirs("uploaded_images")

app.mount("/static", StaticFiles(directory="uploaded_images"), name="static")

@app.post("/upload/")
async def upload_files(
    images: List[UploadFile] = File(...),
    text_file: UploadFile = File(...),
    start_number: int = Form(...)
):
    # Save uploaded text file
    rtf_or_txt_path = os.path.join("uploaded_images", text_file.filename)
    with open(rtf_or_txt_path, "wb") as buffer:
        shutil.copyfileobj(text_file.file, buffer)

    # Read text content
    with open(rtf_or_txt_path, "r", encoding="utf-8", errors="ignore") as f:
        full_text = f.read()

    # Parse after XXXX and after YYYY
    if "XXXX" in full_text:
        text_after_xxxx = full_text.split("XXXX", 1)[1].split("YYYY", 1)[0].strip()
    else:
        text_after_xxxx = ""

    if "YYYY" in full_text:
        keyword_part = full_text.split("YYYY", 1)[1]
        keywords = [k.strip() for k in keyword_part.replace(",", "\n").split("\n")]
    else:
        keywords = []

    return {"text": text_after_xxxx, "keywords": keywords}
