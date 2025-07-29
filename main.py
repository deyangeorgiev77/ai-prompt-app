
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import os
import pandas as pd

app = FastAPI()
app.mount("/static", StaticFiles(directory="uploaded_images"), name="static")

UPLOAD_FOLDER = "uploaded_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("templates/index.html", "r") as f:
        return f.read()

@app.post("/generate")
async def generate(
    start_number: int = Form(...),
    text_file: UploadFile = File(...),
    files: List[UploadFile] = File(...)
):
    # Прочети текста от .rtf/.txt
    raw_text = (await text_file.read()).decode("utf-8", errors="ignore")
    if "XXXX" not in raw_text or "YYYY" not in raw_text:
        return {"error": "Missing XXXX or YYYY section in the uploaded text file."}

    # Извличане на текст и ключови думи
    text_part = raw_text.split("XXXX")[1].split("YYYY")[0].strip()
    keyword_part = raw_text.split("YYYY")[1].strip()
    keywords = [k.strip() for k in keyword_part.replace(",", "
").splitlines() if k.strip()]

    # Създаване на output CSV
    rows = []
    current = start_number
    for file in files:
        filename = f"AI-video_{current:05}.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Примерен промпт
        prompt = (
            f"This image shows something visually descriptive. {text_part}. "
            f"It includes important elements such as: {', '.join(keywords[:10])}."
        )

        rows.append({
            "Filename": f"AI-video_{current:05}.csv",
            "Title": f"Generated video prompt {current}",
            "Description": prompt[:200],
            "Headline": "AI-generated prompt",
            "Keywords": ", ".join(keywords[:49])
        })
        current += 1

    df = pd.DataFrame(rows)
    csv_path = f"{UPLOAD_FOLDER}/AI-video_{start_number:05}.csv"
    df.to_csv(csv_path, index=False)

    return {"message": f"Generated metadata for {len(rows)} images.", "csv": csv_path}
