from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import os
from typing import List
import pandas as pd
from uuid import uuid4

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
CSV_DIR = "generated_csv"
HTML_DIR = "generated_html"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)

app.mount("/images", StaticFiles(directory=UPLOAD_DIR), name="images")
app.mount("/csv", StaticFiles(directory=CSV_DIR), name="csv")
app.mount("/html", StaticFiles(directory=HTML_DIR), name="html")

@app.get("/", response_class=HTMLResponse)
def form():
    return """
    <html>
        <head><title>AI Prompt Generator</title></head>
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

@app.post("/generate", response_class=HTMLResponse)
def generate(files: List[UploadFile] = File(...), task: str = Form(...)):
    image_names = []
    prompts = []
    html_blocks = []
    csv_rows = []

    for file in files:
        unique_id = uuid4().hex[:8]
        filename = f"{unique_id}_{file.filename}"
        image_path = os.path.join(UPLOAD_DIR, filename)
        with open(image_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        image_names.append(filename)

        prompt = f"Auto-generated prompt for {filename}: Based on task -> {task}"
        prompts.append(prompt)

        # Save CSV
        mp4_name = filename.replace(".jpg", ".mp4")
        csv_filename = filename.replace(".jpg", ".csv")
        csv_path = os.path.join(CSV_DIR, csv_filename)
        row = {
            "FileName": mp4_name,
            "Title": f"Title for {filename}",
            "Description": f"Description based on {filename}",
            "Headline": f"Headline for {filename}",
            "Keywords": "keyword1, keyword2, keyword3"
        }
        pd.DataFrame([row]).to_csv(csv_path, index=False)

        # HTML block
        html_block = f"""
        <div style='margin-bottom:20px;'>
            <h3>{filename}</h3>
            <img src='/images/{filename}' style='max-width:400px;'><br>
            <pre>{prompt}</pre>
            <a href='/csv/{csv_filename}' download>Download CSV</a>
        </div>
        """
        html_blocks.append(html_block)

    html_output = "<html><body><h1>Results</h1>" + "".join(html_blocks) + "</body></html>"
    html_file = os.path.join(HTML_DIR, "results.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_output)

    return f"""
    <h2>✅ Files Processed: {len(image_names)}</h2>
    <ul>{''.join([f'<li>{img}</li>' for img in image_names])}</ul>
    <p>📄 <a href='/html/results.html' target='_blank'>View Full HTML Report</a></p>
    """
