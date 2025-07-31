from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from rag_agent import rag_query
import logging
from dotenv import load_dotenv
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()])

feedback_logger = logging.getLogger("feedback")
feedback_handler = logging.FileHandler("logs/feedback.log")
feedback_logger.addHandler(feedback_handler)
feedback_logger.setLevel(logging.INFO)

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class Query(BaseModel):
    text: str

class Feedback(BaseModel):
    query: str
    response: str
    rating: int  # e.g., 1-5
    comment: str = None

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/query")
@limiter.limit("5/minute")
async def handle_query(q: Query):
    try:
        response = rag_query(q.text)
        def stream_response():
            yield response
        logging.info(f"API query processed: {q.text}")
        return StreamingResponse(stream_response(), media_type="text/plain")
    except Exception as e:
        logging.error(f"API error: {str(e)}")
        return {"error": str(e), "response": "Fallback: Unable to process query due to internal error."}

@app.post("/feedback")
async def receive_feedback(fb: Feedback):
    feedback_logger.info(f"Feedback received: Query='{fb.query}', Response='{fb.response}', Rating={fb.rating}, Comment='{fb.comment}'")
    return {"status": "feedback logged"}

# Run: uvicorn src.api:app --reload
# Dockerfile:
# FROM python:3.12
# COPY . /app
# WORKDIR /app
# RUN pip install -r requirements.txt
# CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0"]