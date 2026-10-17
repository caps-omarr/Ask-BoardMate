# E-BoardMate: Generative AI RAG System Layer
### Capstone Project for IS Professional Elective #4: Generative AI Systems
**Target Campus:** Talibon Polytechnic College (TPC), Bohol, Philippines  
**Live Production Host:** [https://eboardmate.onrender.com](https://eboardmate.onrender.com)  

---

## 📌 Project Overview
**E-BoardMate** is an intelligent student boarding house locator and reservation system engineered for **Talibon Polytechnic College (TPC)** students in Bohol. This repository contains the complete implementation for:
- **CHECKPOINT 1 (Prelim: Foundation & Data Pipeline)**
- **CHECKPOINT 2 (Midterm: Prompt Architecture & Vector Indexing)**

---

## 📂 Repository Directory Structure

```text
eboardrag/
├── data/
│   ├── raw_listings_export.json        # Verified active listing records extracted from eboardmate.onrender.com
│   └── processed_chunks.json           # Cleaned, normalized, and tokenized text chunks
├── docs/
│   ├── checkpoint1_proposal.md         # 1-2 page Project Proposal & Success Criteria
│   ├── checkpoint1_reflection.md       # 1/2 page reflection on live data anomalies & sanitation
│   ├── checkpoint2_prompt_engineering.md # 3 structured system prompts + anti-hallucination tests
│   └── checkpoint2_distance_metrics.md # 1 page comparative analysis (Cosine vs Euclidean vs Dot Product)
├── src/
│   ├── main.py                         # Primary E-BoardMate AI Interactive Student CLI
│   ├── fetch_live_data.py              # Script to extract/export active listings from eboardmate.onrender.com
│   ├── preprocessing.py                # Cleaning, normalization, tokenization, and walking-distance pipeline
│   ├── embeddings_demo.py              # Dense vector embedding generation script & model justification
│   ├── vector_store.py                 # ChromaDB indexing with metadata filtering & similarity queries
│   ├── distance_benchmark.py           # Mathematical comparison of Cosine, Euclidean (L2), and Dot Product
│   └── chat_api_demo.py                # LLM API script testing 3 prompts with grounded outputs
├── main.py                             # Root CLI entrypoint launcher
├── .env.example
├── requirements.txt
└── README.md                           # Setup and checkpoint execution guide
```

---

## ⚙️ Environment Setup & Installation

### 1. Prerequisites
- Python 3.10+ installed
- Virtual environment (recommended)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and set your Google Gemini API Key:
```bash
cp .env.example .env
```

---

## 🤖 MAIN STUDENT CLI (E-BOARDMATE AI)

Launch the interactive student CLI terminal where TPC students ask housing questions in real-time:

```bash
python main.py
```
*(or run `python src/main.py`)*

### Interactive Features:
- **Natural Language Search**: Ask for budget dorms, gender restrictions, or walking distance.
- **Landlord Contact Tickets**: Get landlord phone numbers and direct links to `https://eboardmate.onrender.com/boarding-houses/[slug]`.
- **Anti-Hallucination Guardrails**: Auto-refuses out-of-scope non-housing queries (homework, general trivia).

---

## 🚀 Step-by-Step Execution Guide by Checkpoint

### CHECKPOINT 1 (Prelim: Data Pipeline & Preprocessing)

#### Step 1: Extract Verified Live Listings
Pulls active listings from `eboardmate.onrender.com`, enforcing `status = 'approved'`, `is_verified = 1`, and `owner.status = 'active'`. Outputs `data/raw_listings_export.json`.
```bash
python src/fetch_live_data.py
```

#### Step 2: Execute Data Preprocessing Pipeline
Sanitizes raw HTML, normalizes text/gender terms, computes Haversine distance and walking time to TPC campus anchor (`10.1167, 124.2833`), and outputs `data/processed_chunks.json`.
```bash
python src/preprocessing.py
```

#### Step 3: Generate Vector Embeddings & View Model Justification
Loads `sentence-transformers/all-MiniLM-L6-v2`, generates 384-dimensional dense vectors, and displays model latency justification.
```bash
python src/embeddings_demo.py
```

---

### CHECKPOINT 2 (Midterm: Prompt Architecture & Vector Indexing)

#### Step 4: ChromaDB Vector Indexing & Metadata Filtering
Ingests `data/processed_chunks.json` into ChromaDB and executes metadata-filtered queries (e.g., `rent_price <= 1500` AND `allowed_genders == 'Female Only'`).
```bash
python src/vector_store.py
```

#### Step 5: Run Distance Metrics Comparative Benchmark
Computes and compares **Cosine Similarity**, **Euclidean ($L_2$) Distance**, and **Dot Product (Inner Product)** using NumPy/SciPy across 3 student test queries.
```bash
python src/distance_benchmark.py
```

#### Step 6: Execute RAG LLM Chat API Demonstration
Connects retrieved context and system prompts to Google Gemini API (`gemini-2.5-flash` via `google-genai`). Evaluates housing search, landlord reservation hand-off, and out-of-scope refusal prompts.
```bash
python src/chat_api_demo.py
```

---

## 📄 Documentation Summary (`docs/`)

- [`docs/checkpoint1_proposal.md`](docs/checkpoint1_proposal.md): Project Proposal, problem statement, target users, live data source, and success criteria.
- [`docs/checkpoint1_reflection.md`](docs/checkpoint1_reflection.md): Data engineering reflection detailing HTML cleaning, dialect handling, utility booleans, and spatial Haversine distance calculations.
- [`docs/checkpoint2_prompt_engineering.md`](docs/checkpoint2_prompt_engineering.md): Comprehensive specification of 3 production system prompts and anti-hallucination test results.
- [`docs/checkpoint2_distance_metrics.md`](docs/checkpoint2_distance_metrics.md): Mathematical formulations and empirical comparison recommending Cosine Similarity for text chunk retrieval.
