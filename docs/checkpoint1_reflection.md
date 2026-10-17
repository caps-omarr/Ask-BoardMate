# CHECKPOINT 1: DATA ENGINEERING REFLECTION
## Real-World Data Anomalies, Noise Extraction, and Sanitization Pipeline

**Course:** IS Professional Elective #4: Generative AI Systems  
**System:** E-BoardMate (TPC Boarding House RAG Layer)  
**Live Data Source:** [eboardmate.onrender.com](https://eboardmate.onrender.com)  

---

### 1. Executive Overview
Real-world boarding house data extracted from the live `eboardmate.onrender.com` platform and local landlord submissions in Talibon, Bohol exhibits significant heterogeneity, informal phrasing, unescaped HTML tags, and non-standardized utility notes. Relying on raw text directly for RAG indexing leads to vector embedding degradation, noisy LLM context windows, and hallucinated answers. This reflection documents the specific data anomalies observed from the live system and the engineering sanitization pipeline implemented in `src/preprocessing.py`.

---

### 2. Taxonomy of Encountered Data Anomalies

#### A. Raw HTML Markup & Visual Tags
Landlord description entries contained embedded raw HTML formatting, such as `<p><b>Clean and safe dorm for female TPC students!</b></p> <br>`.
* **Impact:** HTML tags inflate token counts unnecessarily and distort word frequency distributions in dense vector embeddings.
* **Resolution:** Implemented HTML entity unescaping (`html.unescape`) and regular expression sanitization (`re.sub(r'<[^>]+>', ' ', text)`) combined with whitespace normalization in `src/preprocessing.py`.

#### B. Informal Shorthand & Gender Casing Inconsistencies
Raw descriptions contained localized colloquialisms and shorthand (e.g., *"BARATO RA! ₱950/month ALL IN"*, *"fem only"*, *"₱1.2k/mo"*).
* **Impact:** Vector models might miscalculate similarity between formal queries like "Female Only" and informal text like "fem only".
* **Resolution:** Standardized gender terms to `'Female Only'`, `'Male Only'`, or `'Any Gender (All)'` and added explicit metadata headers (`Allowed Genders: Female Only`, `Monthly Rent: ₱1,200`) inside the RAG chunk formatter.

#### C. Utility Cost Ambiguity & Sub-metering Details
Landlords frequently report conflicting utility details (e.g., setting `includes_water: false` while describing `"₱150/mo water fee"` or stating `includes_electricity: false` with `"Sub-metered billing at ₱18 per kWh"`).
* **Impact:** Simple boolean flags fail to capture the true financial requirements for student budgeting.
* **Resolution:** Structured the preprocessor to generate explicit utility status clauses (`Water Utility: Separate billing (Flat rate ₱150/month per head)`), ensuring the LLM receives complete context during retrieval.

#### D. Subjective Distance Claims vs. Spatial Haversine Computing
Listings routinely describe locations subjectively as "2 minutes away" or "near TPC gate", which varies greatly depending on transport mode.
* **Impact:** Subjective and inconsistent proximity descriptions in RAG answers.
* **Resolution:** Computed exact **Haversine Distance** from TPC campus anchor (`10.1167, 124.2833`) and standardized walking time using an average human speed of 4.8 km/h ($4.8 \text{ km/h} = 80 \text{ m/min}$):
$$\text{walking\_mins} = \text{round}\left(\frac{\text{distance\_km}}{4.8} \times 60, 1\right)$$

---

### 3. Engineering Outcome & Impact on RAG Quality
By running `src/fetch_live_data.py` and `src/preprocessing.py`, verified active listings were transformed into uniform, token-efficient text chunks saved in `data/processed_chunks.json`. Each chunk (~120-160 tokens) combines rich narrative text with normalized metadata, guaranteeing high precision during ChromaDB vector indexing and zero ambiguous utility responses during LLM generation.
