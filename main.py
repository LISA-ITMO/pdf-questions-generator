from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from logic import process_pdf
from config import MAX_GLOBAL_REQUESTS_PER_HOUR, REQUEST_LOG, check_global_limit

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/upload")
@limiter.limit("5/hour")  # 5 запросов на IP в час
async def upload_pdf(file: UploadFile = File(...), request: Request = None):
    check_global_limit()
    return await process_pdf(file)
