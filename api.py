import os
import sys
import json
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
    SYSTEM_PROMPT_CONVERSATIONAL,
    load_processed_chunks,
    call_gemini_api,
    call_gemini_conversational
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

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    query: str
    history: Optional[list[ChatMessage]] = []
    top_k: Optional[int] = 2

class ChatResponse(BaseModel):
    query: str
    intent: str
    answer: str
    retrieved_context: str

GREETING_WORDS = {
    "hi", "hello", "hey", "good morning", "good afternoon", 
    "good evening", "good day", "hi there", "hello po", 
    "hi po", "sup", "yo", "kumusta", "who are you", "what can you do"
}

def detect_intent(query: str) -> str:
    lowered = query.lower().strip()
    words = set(lowered.split())
    
    # Check if this is purely a greeting / chit-chat
    housing_keywords = [
        "house", "dorm", "room", "rent", "price", "curfew", "san isidro", "torres", "gm", 
        "bedspace", "female", "male", "budget", "near", "photo", "photos", "picture", 
        "pictures", "pic", "pics", "image", "images", "look like", "view"
    ]
    has_housing_intent = any(k in lowered for k in housing_keywords)
    
    if (lowered in GREETING_WORDS or (len(words) <= 2 and words.intersection(GREETING_WORDS))) and not has_housing_intent:
        return "greeting"
    elif any(w in lowered for w in ["reserve", "contact", "phone", "owner", "landlord", "book"]):
        return "reservation"
    elif any(w in lowered for w in ["python", "script", "homework", "weather", "france", "news", "assignment", "math"]):
        return "refusal"
    return "search"

def get_directory_overview() -> str:
    """Provide a compact listing overview of all accredited boarding houses in the dataset."""
    global CHUNKS_CACHE
    if not CHUNKS_CACHE:
        get_or_load_resources()
    lines = []
    for c in CHUNKS_CACHE:
        meta = c.get("metadata", {})
        name = meta.get("name", c.get("name", "Unknown"))
        rent = meta.get("rent_price", "")
        addr = meta.get("address", "")
        avail_rooms = meta.get("available_rooms", 0)
        avail_beds = meta.get("available_bedspaces", 0)
        genders = meta.get("allowed_genders", "Any Gender (All)")
        slug = meta.get("slug", "")
        lines.append(f"- **{name}**: ₱{rent}/mo | Address: {addr} | Allowed: {genders} | Available: {avail_rooms} rooms, {avail_beds} bedspaces | Link: https://eboardmate.onrender.com/boarding-houses/{slug}")
    return f"DIRECTORY OVERVIEW ({len(CHUNKS_CACHE)} total accredited boarding houses in Talibon, Bohol):\n" + "\n".join(lines)

def retrieve_context(query: str, top_k: int = 5) -> str:
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

# Mount static files directory if present
static_dir = os.path.join(current_dir, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def root():
    index_path = os.path.join(current_dir, "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "service": "Ask-BoardMate AI RAG API",
        "status": "online"
    }

@app.get("/api/status")
def api_status():
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
    
    # Only perform vector retrieval if the student is inquiring or reserving
    if intent in ["greeting", "refusal"]:
        retrieved_ctx = ""
    else:
        search_query = query
        if len(query.split()) < 4 and payload.history:
            prev_user_queries = [h.content for h in payload.history if h.role == "user"]
            if prev_user_queries:
                search_query = f"{prev_user_queries[-1]} {query}"
        detailed_chunks = retrieve_context(search_query, top_k=payload.top_k or 5)
        dir_overview = get_directory_overview()
        retrieved_ctx = f"{dir_overview}\n\nDETAILED LISTING PROFILES:\n{detailed_chunks}"

    history_dicts = [{"role": h.role, "content": h.content} for h in (payload.history or [])]
    answer = call_gemini_conversational(
        query=query,
        retrieved_context=retrieved_ctx,
        history=history_dicts,
        intent=intent
    )

    return ChatResponse(
        query=query,
        intent=intent,
        answer=answer,
        retrieved_context=retrieved_ctx
    )
