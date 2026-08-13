from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import rag

app = FastAPI()


class HistoryTurn(BaseModel):
    role: str
    text: str


class ChatRequest(BaseModel):
    message: str
    history: list[HistoryTurn] = []


class ChatResponse(BaseModel):
    answer: str
    meta: str


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="message boş olamaz")
    try:
        text, meta = rag.answer(message, [t.model_dump() for t in req.history])
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Yanıt oluşturulamadı, birazdan tekrar deneyin.",
        )
    return ChatResponse(answer=text, meta=meta)


@app.get("/api/health")
def health():
    return {"status": "ok"}


_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=_static_dir, html=True), name="static")
