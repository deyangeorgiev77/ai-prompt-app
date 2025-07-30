from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import os
import shutil
import pandas as pd

app = FastAPI()

# Create necessary directories
for d in ['uploaded_images', 'uploaded_texts', 'generated_csv']:
    os.makedirs(d, exist_ok=True)

# Mount static directories
app.mount("/static", StaticFiles(directory="uploaded_images"), name="static")
app.mount("/csv", StaticFiles(directory="generated_csv"), name="csv")

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload(
    request: Request,
    start_number: int = Form(...),
    text_file: UploadFile = File(...),
    task: str = Form(...),
    images: List[UploadFile] = File(...)
):
    # Save text file
    text_path = os.path.join('uploaded_texts', text_file.filename)
    with open(text_path, "wb") as f:
        shutil.copyfileobj(text_file.file, f)
    content = open(text_path, encoding='utf-8', errors='ignore').read()
    part_xxxx = content.split("XXXX")[1].split("YYYY")[0].strip() if "XXXX" in content and "YYYY" in content else ""
    keywords = [kw.strip() for kw in content.split("YYYY")[1].splitlines() if kw.strip()] if "YYYY" in content else []

    # Generate CSV
    rows = []
    for idx, img in enumerate(images):
        num = start_number + idx
        img_name = f"AI_{num}.jpg"
        img_path = os.path.join("uploaded_images", img_name)
        with open(img_path, "wb") as f:
            shutil.copyfileobj(img.file, f)
        rows.append({
            "FileName": f"AI-video_{num}.mp4",
            "Title": f"Generated Title {num}",
            "Description": part_xxxx,
            "Headline": f"AI Headline {num}",
            "Keywords": ", ".join(keywords)
        })
    df = pd.DataFrame(rows)
    csv_name = f"AI-video_{start_number}.csv"
    csv_path = os.path.join("generated_csv", csv_name)
    df.to_csv(csv_path, index=False)

    # Render results
    html = "<h2>Results</h2>"
    for idx, row in df.iterrows():
        html += f"<div><b>{row.FileName}</b> - <a href='/csv/{csv_name}'>{csv_name}</a></div><br>"
    return HTMLResponse(content=html)