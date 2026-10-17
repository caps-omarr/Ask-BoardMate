# CHECKPOINT 1: PROJECT PROPOSAL & SYSTEM SPECIFICATIONS
## E-BoardMate: Generative AI RAG Layer for TPC Boarding House Locator & Policy Assistant

**Course:** IS Professional Elective #4: Generative AI Systems  
**Institution:** Talibon Polytechnic College (TPC), Bohol, Philippines  
**Project Phase:** Checkpoint 1 (Prelim: Foundation & Data Pipeline)  
**Production Live Platform:** [E-BoardMate Web Portal](https://eboardmate.onrender.com)  

---

### 1. Executive Summary & System Vision
**E-BoardMate** (deployed at `https://eboardmate.onrender.com`) is an intelligent student boarding house locator and reservation system engineered specifically for students at **Talibon Polytechnic College (TPC)** in Bohol. Finding suitable, secure, and affordable housing in Talibon (across San Jose, Poblacion, Tanghaligue, Santo Niño, and San Isidro) is currently a fragmented, manual process.

This project implements a **Retrieval-Augmented Generation (RAG)** layer on top of E-BoardMate. The RAG system allows students to query housing using natural language (e.g., *"Find me a female-only dorm near TPC main gate under ₱1,500 with free water and no strict 8pm curfew"*), receive accurate grounded recommendations with exact spatial proximity, and obtain verified landlord contact details with direct listing links to `eboardmate.onrender.com`.

---

### 2. Problem Statement
TPC students face several severe challenges when securing off-campus housing:
1. **Housing Information Fragmentation:** Boarding house listings are scattered across social media, physical signs, and word-of-mouth, leading to outdated bedspace availability.
2. **Hidden Utility Costs & Ambiguous Billing:** Many listings advertise low base rents (e.g., ₱1,000/month) but omit sub-metered electricity surcharges (e.g., ₱18/kWh) or separate water fees, resulting in unexpected student expenses.
3. **Curfew & Gender Policy Conflicts:** Students often relocate or face landlord friction due to uncommunicated rules regarding curfews (e.g., strict 9:00 PM lockouts), visitor restrictions, or gender-exclusive floors.
4. **Distance Misrepresentation:** Boarding house locations are vaguely described as "near TPC", causing students to unknowingly rent places requiring expensive daily tricycle commutes.

---

### 3. Target User Personas & Stakeholders

| User Persona | Key Needs & Pain Points | System Interaction Mode |
| :--- | :--- | :--- |
| **TPC Student (Fresher / Out-of-town)** | Budget limits (₱800–₱2,500/mo), female/male-only dorms, proximity to campus, clear utility costs. | Natural language search queries, policy Q&A, proximity and rule validation. |
| **Accredited Landlord / Owner** | High vacancy turnover, constant repetitive inquiry calls, need for student reservation hand-offs. | Standardized schema listings, automated inquiry response via grounded RAG layer. |
| **TPC Student Affairs / Admin** | Monitoring student welfare, ensuring accredited housing standards and transparent rental policies. | System auditability, ground-truth verification, and verified listing badges. |

---

### 4. Data Extraction & Pipeline Architecture
Data is extracted from the production platform (`eboardmate.onrender.com`) via `src/fetch_live_data.py` enforcing production SQL query constraints:
- `status = 'approved'`
- `is_verified = 1`
- `owner.status = 'active'`

Raw extracted records are processed in `src/preprocessing.py` to calculate Haversine distance and walking time from the **TPC Campus Anchor (`Latitude: 10.1167, Longitude: 124.2833`)** at a standard walking speed of 4.8 km/h.

#### Listing Data Schema (`data/raw_listings_export.json`):
- `id`, `name`, `slug`, `address`: Primary identification and spatial location.
- `latitude`, `longitude`: Exact WGS84 GPS coordinates for distance calculation.
- `rent_price`: Monthly rental fee in Philippine Pesos (₱800 – ₱2,500).
- `total_rooms`, `available_rooms`, `total_bedspaces`, `available_bedspaces`: Real-time vacancy metrics.
- `allowed_genders`: Categorical scoping (`'Male Only'`, `'Female Only'`, `'Any Gender (All)'`).
- `amenities`: Standardized features (Wi-Fi, Study Lounge, CCTV, Refrigerator, Laundry).
- `rules`: Curfew hours, visitor policies, cooking regulations.
- `includes_water`, `includes_electricity`: Boolean indicators paired with granular billing breakdowns (`water_billing_details`, `electricity_billing_details`).
- `owner_name`, `owner_phone`: Landlord contact details for reservation hand-off.

---

### 5. Measurable Success Criteria & Benchmark Targets

```
+-----------------------------------------------------------------------+
|                       MEASURABLE SUCCESS CRITERIA                     |
+-----------------------------------------------------------------------+
| 1. Citation & Grounding Accuracy : >= 95% verified factual output    |
| 2. End-to-End Retrieval Latency  : < 300 ms (ChromaDB + Vector Query)  |
| 3. Anti-Hallucination Refusal    : 100% rejection for unlisted houses |
| 4. Proximity & Spatial Accuracy  : Exact Haversine distance & walking  |
|                                    minutes computed from TPC          |
+-----------------------------------------------------------------------+
```

1. **Citation & Factuality Accuracy (≥ 95%):** Every generated answer must strictly cite ground-truth listing metadata (rent price, owner contact, curfew).
2. **Retrieval Sub-system Latency (< 300 ms):** ChromaDB metadata-filtered vector queries must return candidate context chunks in under 300 ms.
3. **Out-of-Scope & Hallucination Resistance (100%):** The system must reject non-housing queries and explicitly declare unlisted properties as unavailable.
4. **Spatial Computing Precision:** Spatial metrics must compute exact Haversine distance and walking time based on 4.8 km/h human walking speed.
