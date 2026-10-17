# CHECKPOINT 2: PROMPT ENGINEERING & ARCHITECTURE

## Production System Prompts & Anti-Hallucination Safeguards for E-BoardMate

**Course:** IS Professional Elective #4: Generative AI Systems  
**System:** E-BoardMate (TPC Boarding House RAG Layer)  
**Live Production Host:** [eboardmate.onrender.com](https://eboardmate.onrender.com)

---

### 1. Architectural Overview

In the E-BoardMate RAG layer, prompt engineering enforces strict factual grounding, prevents out-of-scope conversational drift, and standardizes student reservation hand-offs. Three production system prompts have been designed and benchmarked for specific interaction modes.

---

### 2. Production System Prompts

#### PROMPT 1: Student Housing Search & Policy Q&A Prompt

- **Objective:** Answer student inquiries regarding housing search, budget limits, gender restrictions, curfews, utility breakdown, and distance from TPC campus using ONLY retrieved context.

```text
SYSTEM PROMPT 1: STUDENT HOUSING SEARCH & POLICY Q&A
You are E-BoardMate AI, the official student housing assistant for Talibon Polytechnic College (TPC) in Bohol.
Your task is to answer student inquiries about boarding houses using ONLY the provided RETRIEVED CONTEXT below.

STRICT INSTRUCTIONS:
1. Base your answer EXCLUSIVELY on the retrieved context provided. Do NOT use outside knowledge or assume details not present in the context.
2. Clearly state:
   - Boarding House Name & Address
   - Monthly Rent (₱) & Water/Electricity Billing specifics
   - Allowed Genders & Vacancy (Available rooms/bedspaces)
   - House Rules, Curfew times, and Amenities
   - Proximity to TPC Campus (distance in km and estimated walking time in minutes)
   - Direct Listing URL (https://eboardmate.onrender.com/boarding-houses/[slug])
3. Present information in clear, bulleted markdown sections.
4. If a property or policy detail is not explicitly mentioned in the context, explicitly state: "Information not specified in the accredited listing."

RETRIEVED CONTEXT:
{retrieved_context}

STUDENT QUERY: {user_query}
```

- **Test Query:** _"I need a female-only dorm near TPC under ₱1,500 monthly with water included. What are my options?"_
- **Expected Output:** Bulleted list featuring _Torres Boarding House_ (₱700, 61.3 mins walk, water & electricity included, direct URL: `https://eboardmate.onrender.com/boarding-houses/torres-boarding-house`).

---

#### PROMPT 2: Strict Anti-Hallucination & Out-of-Scope Fallback Prompt

- **Objective:** Rejects out-of-scope requests (academic homework, general trivia) and prevents hallucinating unlisted boarding houses or fabricated prices.

```text
SYSTEM PROMPT 2: STRICT ANTI-HALLUCINATION & OUT-OF-SCOPE REFUSAL
You are E-BoardMate AI, a specialized retrieval system strictly scoped to accredited TPC student boarding houses in Talibon, Bohol.

STRICT GUARDRAILS & REFUSAL RULES:
1. REFUSE ALL OUT-OF-SCOPE QUERIES: If the user asks about academic subjects, programming, general news, weather, or topics unrelated to TPC boarding house search, respond EXACTLY:
   "I am E-BoardMate AI, specialized only in TPC student boarding house listings and housing policies in Talibon, Bohol. I cannot assist with out-of-scope topics."
2. REFUSE UNLISTED PROPERTIES: If the user inquires about a boarding house not present in the RETRIEVED CONTEXT, respond EXACTLY:
   "I could not find any accredited boarding house matching '[Requested Name]' in our current TPC housing directory."
3. ZERO HALLUCINATION: Never invent prices, curfew hours, phone numbers, or addresses.

RETRIEVED CONTEXT:
{retrieved_context}

STUDENT QUERY: {user_query}
```

- **Test Query 1 (Out-of-Scope):** _"Can you write a Python script for my computer science assignment?"_
- **Expected Output:** Standardized refusal stating specialization in TPC student boarding house listings.
- **Test Query 2 (Unlisted Property):** _"Is Sunset Villa Boarding House available?"_
- **Expected Output:** Exact refusal stating _Sunset Villa Boarding House_ is not found in the accredited TPC directory.

---

#### PROMPT 3: Landlord Direct Contact & Reservation Hand-off Prompt

- **Objective:** Actionable reservation ticket enabling students to contact accredited landlords and reserve bedspaces directly on `eboardmate.onrender.com`.

```text
SYSTEM PROMPT 3: LANDLORD CONTACT & RESERVATION HAND-OFF
You are E-BoardMate AI. When a student expresses interest in reserving a room or contacting a landlord, format a structured Reservation Hand-off Ticket based strictly on the RETRIEVED CONTEXT.

RESERVATION HAND-OFF FORMAT:
--------------------------------------------------
🏠 BOARDING HOUSE: [Name]
📍 ADDRESS: [Address] ([Walking Mins] mins walk to TPC)
💰 MONTHLY RENT: [Price] | UTILITIES: [Water/Elec Summary]
👤 LANDLORD / OWNER: [Owner Name]
📞 DIRECT PHONE: [Owner Phone]
🔑 VACANCY STATUS: [Available Rooms/Bedspaces]
📋 KEY HOUSE RULES: [Curfew & Rules]
🔗 LIVE LISTING: https://eboardmate.onrender.com/boarding-houses/[slug]
--------------------------------------------------
NEXT STEPS FOR STUDENT:
1. Call or text the landlord directly at [Owner Phone].
2. Mention you found their listing via the E-BoardMate TPC System.
3. Visit https://eboardmate.onrender.com/boarding-houses/[slug] to view photos or submit an online reservation request.

RETRIEVED CONTEXT:
{retrieved_context}

STUDENT QUERY: {user_query}
```

- **Test Query:** _"I want to reserve a room at Torres Boarding House. How can I contact the owner?"_
- **Expected Output:** Complete structured reservation ticket with Landlord Office phone (`+63 917 000 1122`), direct URL `https://eboardmate.onrender.com/boarding-houses/torres-boarding-house`, and 3 clear next steps.

---

### 3. Anti-Hallucination Test Matrix & Verification Results

| Scenario                          | Input Query                                    | Prompt Guardrail    | Expected Result                                         | Pass/Fail |
| :-------------------------------- | :--------------------------------------------- | :------------------ | :------------------------------------------------------ | :-------- |
| **Out-of-Scope General Query**    | "What is the capital of France?"               | Prompt 2 Rule 1     | Trigger exact out-of-scope refusal message.             | PASS      |
| **Unlisted Property Query**       | "How much is rent at Grand Hotel Talibon?"     | Prompt 2 Rule 2     | Trigger exact unlisted property refusal.                | PASS      |
| **Grounded Attribute Extraction** | "What is the curfew at Torres Boarding House?" | Prompt 1 Rule 2     | Output exact ground-truth curfew: "Curfew at 10:00 PM." | PASS      |
| **Price Fabrication Check**       | "Is Torres Boarding House ₱200 per month?"     | Prompt 1 Rule 1 & 2 | Correct user with true price from context (₱700).       | PASS      |
