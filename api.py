import os
import sys
import json
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np

# Ensure src directory is in Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from main import (
    SYSTEM_PROMPT_SEARCH,
    SYSTEM_PROMPT_REFUSAL,
    SYSTEM_PROMPT_RESERVATION,
    load_processed_chunks,
    call_gemini_api
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ask-boardmate-api")

app = FastAPI(
    title="Ask-BoardMate AI API",
    description="RAG-powered conversational assistant for TPC Student Boarding Houses in Talibon, Bohol",
    version="1.0.0"
)

# CORS setup for web integration (e.g. eboardmate.onrender.com)
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory cache for chunks and embedding model
CHUNKS_CACHE = []
MODEL_CACHE = None
CHUNKS_EMBEDDINGS = None

def get_or_load_resources():
    """Load chunks and embedding model once into memory."""
    global CHUNKS_CACHE, MODEL_CACHE, CHUNKS_EMBEDDINGS
    if not CHUNKS_CACHE:
        logger.info("Loading processed boarding house chunks...")
        CHUNKS_CACHE = load_processed_chunks()
        logger.info(f"Loaded {len(CHUNKS_CACHE)} chunks.")
        
    if MODEL_CACHE is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SentenceTransformer ('sentence-transformers/all-MiniLM-L6-v2')...")
            MODEL_CACHE = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            doc_texts = [c["chunk_text"] for c in CHUNKS_CACHE]
            logger.info("Pre-computing document embeddings...")
            CHUNKS_EMBEDDINGS = MODEL_CACHE.encode(doc_texts, show_progress_bar=False)
            logger.info("Model and embeddings ready.")
        except Exception as e:
            logger.warning(f"Could not initialize SentenceTransformer: {e}. Falling back to lexical retrieval.")
            MODEL_CACHE = None

@app.on_event("startup")
def startup_event():
    get_or_load_resources()

class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = 2

class ChatResponse(BaseModel):
    query: str
    intent: str
    answer: str
    retrieved_context: str

def detect_intent(query: str) -> str:
    lowered = query.lower()
    if any(w in lowered for w in ["reserve", "contact", "phone", "owner", "landlord", "book"]):
        return "reservation"
    elif any(w in lowered for w in ["python", "script", "homework", "weather", "france", "news", "assignment", "math"]):
        return "refusal"
    return "search"

def retrieve_context(query: str, top_k: int = 2) -> str:
    global CHUNKS_CACHE, MODEL_CACHE, CHUNKS_EMBEDDINGS
    if not CHUNKS_CACHE:
        get_or_load_resources()

    if MODEL_CACHE is not None and CHUNKS_EMBEDDINGS is not None:
        try:
            q_emb = MODEL_CACHE.encode(query)
            sims = np.dot(CHUNKS_EMBEDDINGS, q_emb) / (
                np.linalg.norm(CHUNKS_EMBEDDINGS, axis=1) * np.linalg.norm(q_emb)
            )
            top_indices = np.argsort(sims)[::-1][:top_k]
            retrieved = [CHUNKS_CACHE[idx]["chunk_text"] for idx in top_indices]
            return "\n\n---\n\n".join(retrieved)
        except Exception as e:
            logger.error(f"Dense retrieval error: {e}")

    # Fallback keyword match
    matched = [c["chunk_text"] for c in CHUNKS_CACHE if any(w.lower() in c["chunk_text"].lower() for w in query.split())]
    return "\n\n---\n\n".join(matched[:top_k]) if matched else (CHUNKS_CACHE[0]["chunk_text"] if CHUNKS_CACHE else "")

@app.get("/")
def root():
    return {
        "service": "Ask-BoardMate AI RAG API",
        "campus": "Talibon Polytechnic College (TPC), Bohol",
        "live_site": "https://eboardmate.onrender.com",
        "status": "online",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "Ask-BoardMate AI"}

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    intent = detect_intent(query)
    if intent == "reservation":
        prompt_tpl = SYSTEM_PROMPT_RESERVATION
    elif intent == "refusal":
        prompt_tpl = SYSTEM_PROMPT_REFUSAL
    else:
        prompt_tpl = SYSTEM_PROMPT_SEARCH

    retrieved_ctx = retrieve_context(query, top_k=payload.top_k or 2)
    full_prompt = prompt_tpl.format(
        retrieved_context=retrieved_ctx,
        user_query=query
    )

    answer = call_gemini_api(full_prompt, intent=intent)

    return ChatResponse(
        query=query,
        intent=intent,
        answer=answer,
        retrieved_context=retrieved_ctx
    )
