import time
import pdfplumber
import openai
import json
from fastapi import UploadFile, HTTPException
from config import MAX_GPT_REQUESTS_PER_UPLOAD, OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def chunk_text(text, max_words=200):
    words = text.split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

async def process_pdf(file: UploadFile):
    contents = await file.read()
    with pdfplumber.open(file.file) as pdf:
        full_text = "\n".join([p.extract_text() or '' for p in pdf.pages])

    chunks = chunk_text(full_text)
    responses = []

    for i, chunk in enumerate(chunks):
        if i >= MAX_GPT_REQUESTS_PER_UPLOAD:
            break

        points = extract_theses(chunk)
        questions = extract_questions(points)
        responses.append({"theses": points, "questions": questions})

    return {"results": responses}

def extract_theses(text):
    system_prompt = "Ты ассистент преподавателя. Выдели 3–5 ключевых тезисов по входному академическому тексту. Список."
    res = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text}],
        max_tokens=400
    )
    return res.choices[0].message.content

def extract_questions(theses):
    prompt = (
        "Сгенерируй 3 тестовых вопроса по этим тезисам в JSON-массиве. "
        "Каждый объект должен содержать:\n"
        "- question\n- type ('single', 'multi', 'true_false')\n- options\n- answer"
    )
    res = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": theses}],
        max_tokens=600
    )

    raw = res.choices[0].message.content.strip()

    # Очистка от обёртки ```json ... ```
    if raw.startswith("```json"):
        raw = raw[len("```json"):].strip()
    if raw.endswith("```"):
        raw = raw[:-3].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print("⚠️ Ошибка парсинга JSON:", e)
        print("📦 GPT ответ:", raw)
        raise HTTPException(status_code=500, detail="Ошибка при парсинге JSON-ответа от GPT.")
