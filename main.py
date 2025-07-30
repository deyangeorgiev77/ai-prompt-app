from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List
import os
import shutil
import pandas as pd
import re

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

# Ensure required directories exist
for folder in ['uploaded_images', 'uploaded_texts', 'generated_csv']:
    (BASE_DIR / folder).mkdir(exist_ok=True)

# Mount static directories
app.mount('/static', StaticFiles(directory=str(BASE_DIR / 'uploaded_images')), name='static')
app.mount('/csv', StaticFiles(directory=str(BASE_DIR / 'generated_csv')), name='csv')

templates = Jinja2Templates(directory=str(BASE_DIR / 'templates'))

def rtf_to_text(rtf_content: str) -> str:
    text = re.sub(r'[{}]', '', rtf_content)
    text = re.sub(r'\\[a-zA-Z]+\d*', '', text)
    text = re.sub(r'\\', '', text)
    text = re.sub(r'\[a-zA-Z]+', '', text)
    return ' '.join(text.split())

# List of variation phrases for unique prompts
VARIATIONS = [
    "Begin with a sweeping aerial shot to capture the full coastal panorama",
    "Transition into an intimate close-up emphasizing the subjects' emotions",
    "Pan slowly from port to starboard highlighting the vessel's details",
    "Capture reflections of sunlight on the water with gentle camera movements",
    "Focus on the interaction between the subjects and the environment",
    "Include subtle ambient sounds of waves and breeze for texture",
    "Showcase the interplay of light and shadow along the coastline",
    "Zoom out for a grand panoramic reveal of the scenic backdrop"
]

@app.get('/', response_class=HTMLResponse)
async def form_get(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.post('/upload', response_class=HTMLResponse)
async def upload_and_generate(
    request: Request,
    start_number: int = Form(...),
    text_file: UploadFile = File(...),
    task: str = Form(...),
    images: List[UploadFile] = File(...)
):
    # Save and read text
    text_path = BASE_DIR / 'uploaded_texts' / text_file.filename
    with open(text_path, 'wb') as f:
        shutil.copyfileobj(text_file.file, f)
    raw = text_path.read_bytes().decode('utf-8', errors='ignore')
    content = rtf_to_text(raw)

    # Extract between XXXX and YYYY
    part_xxxx = ''
    if 'XXXX' in content and 'YYYY' in content:
        part_xxxx = content.split('XXXX',1)[1].split('YYYY',1)[0].strip()
    # Extract keywords after YYYY
    keywords = []
    if 'YYYY' in content:
        raw_kw = content.split('YYYY',1)[1]
        keywords = [kw.strip('. ,') for kw in raw_kw.splitlines() if kw.strip()][:40]

    html = '<h2>Results</h2>'
    for idx, img in enumerate(images):
        num = start_number + idx
        img_name = f'AI_{num:05d}.jpg'
        csv_name = f'AI-video_{num:05d}.csv'

        # Save image
        img_path = BASE_DIR / 'uploaded_images' / img_name
        with open(img_path, 'wb') as f:
            shutil.copyfileobj(img.file, f)

        # Select variation for this image
        variation = VARIATIONS[idx % len(VARIATIONS)]

        # Build prompt: no prefix, just part_xxxx, keywords, variation
        prompt_text = f"{part_xxxx}. Keywords: {', '.join(keywords)}. {variation} > {csv_name}"

        # Prepare metadata fields
        title = f"{part_xxxx} Visual Story {num}"
        description = f"{variation} focusing on {part_xxxx}"
        headline = f"{part_xxxx} Adventure"

        # Save CSV
        row = {
            'FileName': f'AI-video_{num:05d}.mp4',
            'Title': title,
            'Description': description,
            'Headline': headline,
            'Keywords': ', '.join(keywords)
        }
        df = pd.DataFrame([row])
        df.to_csv(BASE_DIR / 'generated_csv' / csv_name, index=False)

        # Append HTML
        html += (
            f"<div style='margin-bottom:30px;'>"
            f"<img src='/static/{img_name}' width='300'><br>"
            f"<a href='/csv/{csv_name}'>Download {csv_name}</a><br>"
            f"<pre style='white-space:pre-wrap; background:#f4f4f4; padding:10px;'>{prompt_text}</pre>"
            "</div>"
        )

    return HTMLResponse(content=html)