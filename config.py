import os
from dotenv import load_dotenv
import time
from fastapi import HTTPException

load_dotenv()  # загружаем переменные из .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MAX_GPT_REQUESTS_PER_UPLOAD = 10
MAX_GLOBAL_REQUESTS_PER_HOUR = 100

REQUEST_LOG = []

def check_global_limit():
    now = time.time()
    one_hour_ago = now - 3600
    global REQUEST_LOG
    REQUEST_LOG = [t for t in REQUEST_LOG if t > one_hour_ago]
    if len(REQUEST_LOG) >= MAX_GLOBAL_REQUESTS_PER_HOUR:
        raise HTTPException(status_code=429, detail="Слишком много запросов. Попробуйте позже.")
    REQUEST_LOG.append(now)
