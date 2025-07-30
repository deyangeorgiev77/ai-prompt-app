import os
import shutil
import json
import pandas as pd
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import List
import re
import openai

# Initialize OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

# Ensure directories
for folder in ['uploaded_images', 'uploaded_texts', 'generated_csv']:
    (BASE_DIR / folder).mkdir(exist_ok=True)

app.mount('/static', StaticFiles(directory=str(BASE_DIR / 'uploaded_images')), name='static')
app.mount('/csv', StaticFiles(directory=str(BASE_DIR / 'generated_csv')), name='csv')
templates = Jinja2Templates(directory=str(BASE_DIR / 'templates'))

def rtf_to_text(rtf_content: str) -> str:
    text = re.sub(r'[{}]', '', rtf_content)
    text = re.sub(r'\\[a-zA-Z]+\d*', '', text)
    text = re.sub(r'\\', '', text)
    text = re.sub(r'\[a-zA-Z]+', '', text)
    return ' '.join(text.split())

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
    # Save and read text file
    text_path = BASE_DIR / 'uploaded_texts' / text_file.filename
    with open(text_path, 'wb') as f:
        shutil.copyfileobj(text_file.file, f)
    raw = text_path.read_bytes().decode('utf-8', errors='ignore')
    content = rtf_to_text(raw)

    # Extract after XXXX and keywords after YYYY
    part_xxxx = content.split('XXXX',1)[1].split('YYYY',1)[0].strip() if 'XXXX' in content and 'YYYY' in content else ''
    raw_kw = content.split('YYYY',1)[1] if 'YYYY' in content else ''
    keywords = [kw.strip(' .,') for kw in raw_kw.splitlines() if kw.strip()][:40]

    html = '<h2>Results</h2>'
    for idx, img in enumerate(images):
        num = start_number + idx
        img_name = f'AI_{num:05d}.jpg'
        csv_name = f'AI-video_{num:05d}.csv'

        # Save image
        img_path = BASE_DIR / 'uploaded_images' / img_name
        with open(img_path, 'wb') as f:
            shutil.copyfileobj(img.file, f)

        # Call OpenAI for prompt, title, description, headline, keywords
        system_msg = "You are a creative AI assistant specialized in generating detailed video prompts."
        user_msg = f"""Generate for the following:
Image Description: {part_xxxx}
Keywords: {', '.join(keywords)}
Instructions: Create a detailed AI video prompt (>=300 characters, no mention of clip length), a Title (14-60 words), a Description (16-20 words), a Headline (14-16 words), and 34-40 unique keywords (first 8 single words). Return a JSON object with keys: prompt, title, description, headline, keywords."""
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ]
        )
        data = json.loads(response.choices[0].message.content)

        # Save CSV
        row = {
            'FileName': f'AI-video_{num:05d}.mp4',
            'Title': data['title'],
            'Description': data['description'],
            'Headline': data['headline'],
            'Keywords': ', '.join(data['keywords'])
        }
        df = pd.DataFrame([row])
        csv_path = BASE_DIR / 'generated_csv' / csv_name
        df.to_csv(csv_path, index=False)

        # Append HTML
        prompt_text = f"{data['prompt']} > {csv_name}"
        html += (
            f"<div style='margin-bottom:30px;'>"
            f"<img src='/static/{img_name}' width='300'><br>"
            f"<a href='/csv/{csv_name}' target='_blank'>Download {csv_name}</a><br>"
            f"<pre style='white-space:pre-wrap; background:#f4f4f4; padding:10px;'>{prompt_text}</pre>"
            "</div>"
        )

    return HTMLResponse(content=html)