
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import os
import shutil
import pandas as pd

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

# Create required directories
for d in ['uploaded_images', 'uploaded_texts', 'generated_csv']:
    os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)

# Mount static routes
app.mount('/static', StaticFiles(directory=os.path.join(BASE_DIR, 'uploaded_images')), name='static')
app.mount('/csv', StaticFiles(directory=os.path.join(BASE_DIR, 'generated_csv')), name='csv')

templates = Jinja2Templates(directory=str(BASE_DIR / 'templates'))

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
    # Save text file
    text_path = BASE_DIR / 'uploaded_texts' / text_file.filename
    with open(text_path, 'wb') as f:
        shutil.copyfileobj(text_file.file, f)
    content = text_path.read_text(encoding='utf-8', errors='ignore')
    # Parse parts
    part_xxxx = content.split('XXXX')[1].split('YYYY')[0].strip() if 'XXXX' in content and 'YYYY' in content else ''
    keywords = [kw.strip() for kw in content.split('YYYY')[1].splitlines() if kw.strip()] if 'YYYY' in content else []

    # Generate per-image CSV and build HTML
    html = '<h2>Results</h2>'
    for idx, img in enumerate(images):
        num = start_number + idx
        img_name = f'AI_{num:05d}.jpg'
        csv_name = f'AI-video_{num:05d}.csv'
        # Save image
        img_path = BASE_DIR / 'uploaded_images' / img_name
        with open(img_path, 'wb') as f:
            shutil.copyfileobj(img.file, f)
        # Create single-row DataFrame
        row = {
            'FileName': f'AI-video_{num:05d}.mp4',
            'Title': f'Generated Title {num}',
            'Description': part_xxxx,
            'Headline': f'AI Headline {num}',
            'Keywords': ', '.join(keywords)
        }
        df = pd.DataFrame([row])
        # Save CSV
        csv_path = BASE_DIR / 'generated_csv' / csv_name
        df.to_csv(csv_path, index=False)
        # Build prompt for this image
        prompt = f"""{task.strip()} {part_xxxx} Keywords: {', '.join(keywords)} > {csv_name}"""
        # Append to HTML
        html += f"<div style='margin-bottom:30px;'>"
        html += f"<img src='/static/{img_name}' alt='{img_name}' width='300'><br>"
        html += f"<a href='/csv/{csv_name}'>Download {csv_name}</a><br>"
        html += f"<pre style='white-space:pre-wrap; background:#f4f4f4; padding:10px;'>{prompt}</pre>"
        html += "</div>"
    return HTMLResponse(content=html)
