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
import time
import re
import uuid

# In-memory session store
SESSION_STORE: dict[str, dict] = {}

def get_or_create_session(session_id: Optional[str]) -> dict:
    if not session_id:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = {
            "session_id": session_id,
            "current_property": None,
            "preferences": {},
            "history": [],
            "created_at": time.time(),
            "updated_at": time.time()
        }
    return SESSION_STORE[session_id]

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    history: Optional[list[ChatMessage]] = []
    top_k: Optional[int] = 5

class ChatResponse(BaseModel):
    query: str
    session_id: str
    intent: str
    current_property: Optional[str] = None
    answer: str
    retrieved_context: str

class ResetRequest(BaseModel):
    session_id: str

def extract_mentioned_property(text: str) -> Optional[str]:
    """Identify if any accredited boarding house name or alias is mentioned in the text."""
    global CHUNKS_CACHE
    if not CHUNKS_CACHE:
        get_or_load_resources()
    lowered = text.lower()
    for c in CHUNKS_CACHE:
        name = c.get("name", "")
        if name.lower() in lowered:
            return name
        alias = name.split()[0].lower()
        if len(alias) >= 3 and alias in lowered:
            return name
    return None

FOLLOWUP_KEYWORDS = [
    "it", "its", "this", "that", "that one", "water", "electricity", "curfew", 
    "rent", "price", "photo", "photos", "pic", "pics", "picture", "pictures", 
    "owner", "landlord", "contact", "number", "phone", "reserve", "book", 
    "rules", "how far", "distance", "walking", "available", "rooms", "bedspace"
]

CLOSING_PHRASES = [
    "salamat", "thank you", "thanks", "thx", "ty", "daghang salamat",
    "wala na", "wala mna", "wala mn", "wala na bai", "wala na po", "wala na lods",
    "ok na", "okay na", "ok na bai", "okay na bai", "ok na po", "okay na po",
    "kana lang", "kana ra", "kana ra bai", "kana lang bai", "kana lang sa", "kana ra sa",
    "bye", "goodbye", "cge bai", "sige bai", "sige po", "cge po", "sige salamat", "cge salamat"
]

def is_followup_query(query: str) -> bool:
    lowered = query.lower().strip()
    words = lowered.split()
    if any(p in lowered for p in CLOSING_PHRASES):
        return False
    if len(words) <= 5:
        return any(k in lowered for k in FOLLOWUP_KEYWORDS)
    return any(p in words for p in ["it", "its", "this", "that", "here", "there"])

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
        "pictures", "pic", "pics", "image", "images", "look like", "view", "available",
        "kwarto", "tagpila", "pila", "abang", "abangan", "asa", "location", "wifi"
    ]
    has_housing_intent = any(k in lowered for k in housing_keywords)
    
    # Check for closing / gratitude
    if any(p in lowered for p in CLOSING_PHRASES) and not has_housing_intent:
        return "closing"

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
            "reset": "/api/chat/reset",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "Ask-BoardMate AI"}

@app.post("/api/chat/reset")
def reset_session(payload: ResetRequest):
    if payload.session_id in SESSION_STORE:
        del SESSION_STORE[payload.session_id]
        logger.info(f"Reset session {payload.session_id}")
    return {"status": "ok", "message": "Session reset successfully", "session_id": payload.session_id}

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # 1. Retrieve or create session state
    session = get_or_create_session(payload.session_id)
    session_id = session["session_id"]
    session["updated_at"] = time.time()

    # 2. Extract mentioned property if specified in query
    mentioned = extract_mentioned_property(query)
    if mentioned:
        session["current_property"] = mentioned

    # 3. Coreference Resolution / Query Expansion for follow-ups
    active_property = session.get("current_property")
    search_query = query
    if not mentioned and active_property and is_followup_query(query):
        search_query = f"{active_property} {query}"

    # 4. User preference detection
    lowered = query.lower()
    if "female" in lowered or "girl" in lowered or "lady" in lowered or "women" in lowered:
        session["preferences"]["gender"] = "Female Only"
    elif "male" in lowered or "boy" in lowered or "gentlemen" in lowered or "men" in lowered:
        session["preferences"]["gender"] = "Male Only"

    budget_match = re.search(r'(?:under|below|budget|max|limit|around)?\s*₱?\s*(\d{3,4})', lowered)
    if budget_match:
        try:
            session["preferences"]["budget"] = int(budget_match.group(1))
        except Exception:
            pass

    # 5. Intent detection
    intent = detect_intent(query)
    
    # 6. Context retrieval with state enrichment
    if intent in ["greeting", "closing", "refusal"]:
        retrieved_ctx = ""
    else:
        detailed_chunks = retrieve_context(search_query, top_k=payload.top_k or 5)
        dir_overview = get_directory_overview()
        
        context_parts = [dir_overview]
        if active_property:
            context_parts.append(f"CURRENT CONVERSATION FOCUS: The student is asking about or following up on '{active_property}'.")
        if session.get("preferences"):
            pref_str = ", ".join([f"{k}: {v}" for k, v in session["preferences"].items()])
            context_parts.append(f"STUDENT STATED PREFERENCES: {pref_str}")
        context_parts.append(f"DETAILED LISTING PROFILES:\n{detailed_chunks}")
        retrieved_ctx = "\n\n".join(context_parts)

    # 7. Merge history from payload or session
    history_dicts = [{"role": h.role, "content": h.content} for h in (payload.history or [])]
    if not history_dicts and session["history"]:
        history_dicts = session["history"][-10:]

    answer = call_gemini_conversational(
        query=query,
        retrieved_context=retrieved_ctx,
        history=history_dicts,
        intent=intent
    )

    # 8. Record property discussed in answer if not already set
    if not session.get("current_property"):
        ans_prop = extract_mentioned_property(answer)
        if ans_prop:
            session["current_property"] = ans_prop

    # 9. Update server session history
    session["history"].append({"role": "user", "content": query})
    session["history"].append({"role": "assistant", "content": answer})
    if len(session["history"]) > 20:
        session["history"] = session["history"][-20:]

    return ChatResponse(
        query=query,
        session_id=session_id,
        intent=intent,
        current_property=session.get("current_property"),
        answer=answer,
        retrieved_context=retrieved_ctx
    )

