
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import os
import shutil
import pandas as pd
from typing import List

app = FastAPI()

app.mount("/static", StaticFiles(directory="uploaded_images"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "uploaded_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("uploaded_texts", exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_files(
    request: Request,
    start_number: int = Form(...),
    text_file: UploadFile = File(...),
    files: List[UploadFile] = File(...)
):
    text_path = f"uploaded_texts/{text_file.filename}"
    with open(text_path, "wb") as f:
        f.write(await text_file.read())

    with open(text_path, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        xxxx_text = content.split("XXXX")[1].split("YYYY")[0].strip()
        yyyy_keywords = [kw.strip() for kw in content.split("YYYY")[1].splitlines() if kw.strip()]
    except IndexError:
        xxxx_text = "No XXXX found"
        yyyy_keywords = ["keyword1", "keyword2"]

    output_html = ""
    for idx, img in enumerate(files):
        filename = f"AI_{start_number + idx}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, "wb") as f:
            f.write(await img.read())

        prompt = f"This is a test prompt for image {filename}. Integrated text: {xxxx_text}. Keywords: {', '.join(yyyy_keywords[:10])}"
        csv_filename = f"AI-video_{start_number + idx}.csv"
        df = pd.DataFrame([{
            "FileName": f"AI-video_{start_number + idx}.mp4",
            "Title": f"Generated title for {filename}",
            "Description": f"Generated description for {filename}",
            "Headline": f"Generated headline for {filename}",
            "Keywords": ", ".join(yyyy_keywords)
        }])
        df.to_csv(f"/mnt/data/{csv_filename}", index=False)

        output_html += f"""
<div style='margin-bottom: 20px'>
  <img src='/static/{filename}' width='300'><br>
  <b>{filename}</b><br>
  <textarea rows='6' cols='80'>{prompt} > {csv_filename}</textarea><br>
  <a href='sandbox:/mnt/data/{csv_filename}' target='_blank'>Download {csv_filename}</a>
</div>
"""

    return HTMLResponse(content=output_html, status_code=200)
