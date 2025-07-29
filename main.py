from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os
import pandas as pd
from typing import List
from uuid import uuid4

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

UPLOAD_DIR = "uploaded_images"
CSV_DIR = "generated_csv"
HTML_DIR = "generated_html"
RTF_DIR = "uploaded_rtf"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(RTF_DIR, exist_ok=True)

app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")
app.mount("/csv", StaticFiles(directory=CSV_DIR), name="csv")
app.mount("/html", StaticFiles(directory=HTML_DIR), name="html")

@app.get("/", response_class=HTMLResponse)
def form():
    return """
    <html>
        <head><title>Upload JPGs + RTF File</title></head>
        <body>
            <h1>📤 Upload JPG Images and RTF Task File</h1>
            <form action="/generate" enctype="multipart/form-data" method="post">
                <p><b>Upload JPG images:</b></p>
                <input type="file" name="files" accept=".jpg" multiple required><br><br>
                <p><b>Upload RTF file with XXXX and YYYY:</b></p>
                <input type="file" name="rtf" accept=".rtf" required><br><br>
                <input type="submit" value="Generate">
            </form>
            <hr>
            <p>🔗 <a href="/html/results.html" target="_blank">View Results Page</a></p>
        </body>
    </html>
    """

@app.post("/generate", response_class=HTMLResponse)
async def generate(files: List[UploadFile] = File(...), rtf: UploadFile = File(...)):
    rtf_path = os.path.join(RTF_DIR, rtf.filename)
    with open(rtf_path, "wb") as f:
        shutil.copyfileobj(rtf.file, f)

    with open(rtf_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    if "XXXX" in content and "YYYY" in content:
        task_text = content.split("XXXX")[1].split("YYYY")[0].strip()
        keyword_block = content.split("YYYY")[1].strip()
        keywords = [k.strip() for k in keyword_block.split(",") if k.strip()]
    else:
        task_text = "Missing XXXX section"
        keywords = []

    image_names, html_blocks = [], []

    for file in files:
        filename = f"{uuid4().hex[:6]}_{file.filename}"
        image_path = os.path.join(UPLOAD_DIR, filename)
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        prompt = f"🎬 AI Video Prompt: Визуализирай {filename}, комбинирай го със следното описание: {task_text}. Използвай ключови думи като: {', '.join(keywords[:10])}."
        mp4_name = filename.replace(".jpg", ".mp4")
        csv_name = filename.replace(".jpg", ".csv")
        csv_path = os.path.join(CSV_DIR, csv_name)

        row = {
            "FileName": mp4_name,
            "Title": f"Title for {filename}",
            "Description": f"Generated based on image + task.",
            "Headline": f"Prompt: {prompt[:50]}...",
            "Keywords": ", ".join(keywords[:15])
        }
        pd.DataFrame([row]).to_csv(csv_path, index=False)

        html_blocks.append(f"""
        <div style='margin-bottom:30px;'>
            <h3>{filename}</h3>
            <img src='/images/{filename}' style='max-width:400px'><br>
            <pre>{prompt}</pre>
            <a href='/csv/{csv_name}' download>⬇ Download CSV</a>
        </div>
        """)
        image_names.append(filename)

    full_html = f"<html><body><h1>✅ Results</h1>{''.join(html_blocks)}</body></html>"
    with open(os.path.join(HTML_DIR, "results.html"), "w", encoding="utf-8") as f:
        f.write(full_html)

    return f"""
    <h2>✅ Processed {len(image_names)} images</h2>
    <ul>{''.join([f"<li>{img}</li>" for img in image_names])}</ul>
    <p>🔗 <a href='/html/results.html' target='_blank'>View Results Page</a></p>
    """
