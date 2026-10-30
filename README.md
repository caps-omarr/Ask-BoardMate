# Ask-BoardMate: Generative AI RAG System Layer
> **Intelligent Retrieval-Augmented Generation (RAG) Housing Assistant for Talibon Polytechnic College (TPC)**  
> *Coursework & Capstone Submission for IS Professional Elective: Generative AI Systems*

[![Live Deployed App](https://img.shields.io/badge/Live%20App-Railway%20Deployment-00C7B7?style=for-the-badge&logo=railway&logoColor=white)](https://eboardrag-production.up.railway.app)
[![Live Production Host](https://img.shields.io/badge/Production%20Portal-eboardmate.onrender.com-1B4D3E?style=for-the-badge)](https://eboardmate.onrender.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Uvicorn-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Gemini API](https://img.shields.io/badge/LLM-Google%20Gemini%20API-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)

---

## 📌 1. Project Title & Purpose

### Project Title
**Ask-BoardMate: AI-Powered RAG Student Housing Assistant**

### Problem Statement
Finding accredited, safe, and affordable student boarding houses near **Talibon Polytechnic College (TPC)** in Talibon, Bohol, Philippines is traditionally stressful and tedious. Students often search door-to-door, face unexpected utility surcharges, misunderstand curfew or gender restrictions, or struggle to reach verified landlords.

### Solution Purpose
**Ask-BoardMate** is an intelligent, conversational Retrieval-Augmented Generation (RAG) assistant that empowers TPC students to query verified boarding house listings in natural language (English, Taglish, and Bisaya/Cebuano). It provides:
- Instant, grounded details on monthly rent, utility billing (water/electricity), room and bedspace vacancies.
- Accurate walking distances and estimated walking time to the TPC campus anchor point (`10.1167, 124.2833`).
- Direct landlord contact info and official reservation hand-off links.
- Conversational multi-turn memory across turns and page refreshes.
- Zero-hallucination guardrails that strictly refuse out-of-scope queries (e.g. homework, general trivia) or unlisted properties.

---

## 🌐 2. Live Deployed Application 

| Item | Details / Links |
| :--- | :--- |
| **Live Deployed App URL** | [https://eboardrag-production.up.railway.app](https://eboardrag-production.up.railway.app) *(or live Railway deployment URL)* |
| **Production Web Portal** | [https://eboardmate.onrender.com](https://eboardmate.onrender.com) |
| **Public GitHub Repo** | [https://github.com/caps-omarr/Ask-BoardMate](https://github.com/caps-omarr/Ask-BoardMate) |
| **Access Requirements** | **No login, no authentication, and no installation required** — open directly in any desktop or mobile browser. |

---

## ⚠️ 3. Usage Limits & API Quota Notice (Requirement 1.6)

> [!NOTE]  
> **Evaluator / Instructor Notice on Free-Tier API Quotas:**  
> This application connects to the **Google Gemini API** (`google-genai` SDK) using a developer tier key.
> - **Primary Active Models:** `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite` (with automatic rollover to `gemini-flash-latest`, `gemini-3.6-flash`, and `gemini-3.8-flash`).
> - **Rate Limit Headroom:** Free-tier limits allow **15 requests per minute (RPM)** and up to **1,500 requests per day (RPD)**.
> - **Graceful Grounded Fallbacks:** If the external Gemini API is momentarily unavailable or rate-limited (`429 RESOURCE_EXHAUSTED`), Ask-BoardMate automatically fails over to internal zero-hallucination grounded handlers. It continues to deliver verified listing details, curfew rules, landlord contact hand-offs, and polite refusal messages without crashing or hallucinating.

---

## 📂 4. Knowledge Source & Sample Documents Origin

All RAG knowledge chunks originate from real, verified boarding house records extracted directly from the live production portal [eboardmate.onrender.com](https://eboardmate.onrender.com):
- **Source Dataset:** `data/raw_listings_export.json` and `data/processed_chunks.json`.
- **Scope & Verification:** 15 accredited boarding houses in Talibon, Bohol, verified under strict accreditation filters (`status = 'approved'`, `is_verified = 1`, and `owner.status = 'active'`).
- **Extracted Attributes:**
  - Boarding House Name, Barangay / Sitio Address, and Landlord Name.
  - Monthly Rent (₱) and specific billing policies (water and electricity inclusions/sub-metering).
  - Allowed Genders (`Female Only`, `Male Only`, `Any Gender (All)`).
  - Available Room count and Bedspace vacancies.
  - House Rules, Curfew hours (e.g., 10:00 PM curfew), and Amenities (Wi-Fi, study area, cooking access).
  - Landlord Direct Contact Phone numbers.
  - GPS Coordinates (`latitude`, `longitude`) used to calculate exact Haversine distance and walking time in minutes to TPC campus.
  - Direct live URLs (`https://eboardmate.onrender.com/boarding-houses/[slug]`) and photo gallery URLs.

---

## 🛠️ 5. Technology Stack & Architecture

```
                          ASK-BOARDMATE RAG ARCHITECTURE
  +-------------------------------------------------------------------------+
  |                                                                         |
  |   1. INGESTION & PREPROCESSING                                          |
  |      eboardmate.onrender.com -> raw_listings_export.json                |
  |      -> Text Cleaning, Normalization & Haversine Distance Calculation   |
  |      -> data/processed_chunks.json                                      |
  |                                                                         |
  |   2. EMBEDDINGS & VECTOR STORE                                          |
  |      sentence-transformers/all-MiniLM-L6-v2 (384-dimensional dense vectors)|
  |      Indexed via ChromaDB + NumPy Cosine Similarity Matrix              |
  |                                                                         |
  |   3. RETRIEVAL & QUERY AUGMENTATION                                     |
  |      User Query -> Coreference Resolution & Preference Filtering       |
  |      -> Top-K Dense Semantic Chunks + 15-Listing Directory Overview     |
  |                                                                         |
  |   4. GENERATION & GUARDRAILS                                            |
  |      Google Gemini API (gemini-3.5-flash-lite / gemini-3.1-flash-lite)  |
  |      System Instruction: Strict Grounding + Multi-turn Memory + Refusal|
  |                                                                         |
  |   5. SERVING & INTERFACE                                                |
  |      FastAPI + Uvicorn Python Backend                                  |
  |      Vanilla HTML5 / Modern CSS (Claude-aesthetic) / JavaScript        |
  |      Containerized on Docker & Publicly Deployed on Railway            |
  +-------------------------------------------------------------------------+
```

### Detailed Component Specifications:
1. **Embedding Model (`sentence-transformers/all-MiniLM-L6-v2`):**
   - Generates 384-dimensional dense vector embeddings.
   - Selected for high semantic fidelity, fast inference (<15ms on CPU), and zero GPU dependency.
2. **Vector Indexing & Retrieval:**
   - **ChromaDB** client with persistent vector store in `chroma_db/`.
   - **NumPy Dense Cosine Similarity** matrix for ultra-fast in-memory retrieval on cloud containers.
   - **Metadata Filtering:** Filters by budget thresholds, gender restrictions, and room availability.
3. **Large Language Model (LLM):**
   - **Google Gemini API** (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-flash-latest`) via `google-genai`.
   - Conversational multi-turn history with coreference resolution (e.g. resolving "its curfew" to the previously discussed property).
   - Tone adaptation: Fluently matches student vibes in English, Taglish, or Bisaya.
4. **Backend Framework:**
   - **FastAPI** with asynchronous request handlers.
   - Endpoints: `POST /api/chat`, `POST /api/chat/reset`, `GET /health`, `GET /api/status`, `GET /`.
5. **Frontend UI/UX:**
   - Claude-inspired aesthetic utilizing smooth Alabaster (`#F8F7F4`) and Sage gradients (no harsh plain white).
   - Sidebar conversation management with multi-session history, new chat creation, and collapsible toggle.
   - Dark Mode / Light Mode theme switch with persistent `localStorage`.
   - Quick suggestion prompt chips and mobile-responsive layout.

---

## ⚙️ 6. How to Run Locally

### Prerequisites
- Python 3.10 or higher
- Git
- Google Gemini API Key ([Get a free key at Google AI Studio](https://aistudio.google.com/))

### Step 1: Clone the Repository
```bash
git clone https://github.com/caps-omarr/Ask-BoardMate.git
cd Ask-BoardMate
```

### Step 2: Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Packages
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env` and insert your Gemini API Key:
```bash
cp .env.example .env
```
Inside `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### Step 5: Launch the Application
You can run the web server or the CLI version:

#### Option A: Web Application (FastAPI + Modern UI)
```bash
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```
Open your browser and navigate to: **`http://localhost:8000`**

#### Option B: Terminal Student CLI
```bash
python main.py
```

---

## 🧪 7. Sample Questions & RAG Grounding Verification

The table below details benchmark queries demonstrating full RAG functionality, including multi-turn memory and out-of-scope anti-hallucination refusals:

| Test Category | Student Query | Expected RAG Pipeline Behavior | Grounded Output Summary |
| :--- | :--- | :--- | :--- |
| **1. Grounded Housing Search** | *"I am a female student looking for an affordable dorm near TPC under 1000 pesos with water included."* | Vector retrieval filters by gender (`Female Only`) and rent (`<= 1000`). Injects Torres Boarding House chunk into Gemini prompt. | Recommends **Torres Boarding House** (₱700/mo, San Isidro, water & electricity included, 2 rooms available, 4.91 km ~61.3 mins walk, live link). |
| **2. Multi-Turn Coreference & Contact** | *"What are its curfew hours and how do I contact the landlord to reserve?"* | Session memory resolves *"its"* to Torres Boarding House without re-stating name. Formats Landlord Ticket. | Returns 10:00 PM curfew, cleanliness rules, Landlord Office direct phone (`+63 917 000 1122`), and reservation link. |
| **3. Conversational Gratitude / Vibe** | *"ahh wala mna bai, salamat kau bai"* | Intent classified as `closing`. Suppresses listing search to avoid unwanted dumps. Matches Bisaya dialect. | Warmly replies in Bisaya: *"Way sapayan bai! Walay problema gyud. Kung magkinahanglan ka'g tabang... chat lang diri bisan kanus-a."* |
| **4. Out-of-Scope Refusal (Cannot Answer)** | *"Can you write a Python script for my calculus programming homework?"* | Guardrail triggers on non-housing query (`homework`, `script`). Rejects out-of-scope generation. | *"I am Ask BoardMate, specialized only in TPC student boarding house listings and housing policies in Talibon, Bohol. How can I assist you with your boarding house search?"* |
| **5. Unlisted Property Refusal** | *"How much is monthly rent at Sunset Villa Boarding House?"* | Scans 15 accredited listings; property not found in knowledge chunks. Anti-hallucination triggers. | Accurately states that *Sunset Villa Boarding House* is not an accredited listing in the official TPC directory. Refuses to invent prices. |

---


## 📁 8. Repository Directory Layout

```text
eboardrag/
├── data/
│   ├── raw_listings_export.json        # Verified active listing records from eboardmate.onrender.com
│   └── processed_chunks.json           # Cleaned, normalized, and tokenized text chunks
├── docs/
│   ├── checkpoint1_proposal.md         # Project Proposal & Success Criteria
│   ├── checkpoint1_reflection.md       # Data engineering reflection & live data sanitation
│   ├── checkpoint2_prompt_engineering.md # Structured system prompts & anti-hallucination tests
│   └── checkpoint2_distance_metrics.md # Comparative analysis (Cosine vs Euclidean vs Dot Product)
├── src/
│   ├── main.py                         # Conversational RAG logic & LLM generation handlers
│   ├── fetch_live_data.py              # Export active listings from eboardmate.onrender.com
│   ├── preprocessing.py                # Preprocessing pipeline with Haversine distance calculations
│   ├── embeddings_demo.py              # Dense vector embedding generation script & model justification
│   ├── vector_store.py                 # ChromaDB indexing with metadata filtering & similarity queries
│   ├── distance_benchmark.py           # Mathematical comparison of Cosine, Euclidean (L2), and Dot Product
│   └── chat_api_demo.py                # LLM API script testing 3 prompts with grounded outputs
├── static/
│   ├── index.html                      # Modern Claude-style web interface
│   ├── style.css                       # Responsive stylesheet with dark/light themes & Alabaster palette
│   ├── chat.js                         # Chat UI state, session persistence, and API integration
│   ├── askboardmate.jfif               # Circular Ask-BoardMate emblem
│   └── logo.png                        # E-BoardMate branding asset
├── Ask_BoardMate_Demo_Video_Script.docx # 5-8 minute screen recording script for capstone submission
├── sample_student_queries.txt          # Benchmark student test queries across 4 categories
├── Dockerfile                          # Production container configuration for Railway deployment
├── api.py                              # FastAPI backend application with session state & RAG endpoints
├── main.py                             # Root CLI entrypoint launcher
├── requirements.txt                    # Python package dependencies
├── .env.example                        # Example environment variables template (no secrets)
└── README.md                           # Comprehensive project documentation
```

---

## 🔒 9. Security & Responsible AI Practices

- **Zero API Keys in Repository:** All secrets and credentials are read strictly from environment variables via `os.getenv("GEMINI_API_KEY")`.
- **`.env.example` Included:** Provides variable names without sensitive values.
- **Strict Grounding:** The model is prohibited from fabricating prices, contact numbers, or rules. When information is missing, it explicitly notes that the listing does not specify it.
- **Public Accessibility:** Configured to run freely on public cloud infrastructure (Railway) with no user tracking or authentication barriers.
