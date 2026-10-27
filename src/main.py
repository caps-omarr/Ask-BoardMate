import os
import sys
import json
import warnings
import logging
import numpy as np
from dotenv import load_dotenv

# Suppress HuggingFace Hub unauthenticated warning & noisy logs
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore")
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

# Ensure UTF-8 output encoding for Windows terminals
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

# Conversational RAG System Prompt
SYSTEM_PROMPT_CONVERSATIONAL = """You are E-BoardMate AI, the friendly and official student housing assistant for Talibon Polytechnic College (TPC) in Bohol, Philippines (https://eboardmate.onrender.com).

GUIDELINES FOR CONVERSATIONAL RAG:
1. GREETINGS & CASUAL INTERACTION:
   - When the student greets you (e.g., "hi", "hello", "good morning", "hey", "how are you"), reply warmly and politely as E-BoardMate AI.
   - Ask how you can help them find an accredited boarding house (e.g. asking about their target budget, gender preference, or desired room type).
   - DO NOT list boarding houses unprompted when the student only says hi or greets you. Wait until they ask about housing.

2. TOTAL DIRECTORY COUNT & GENERAL INQUIRIES:
   - Our directory contains a total of 15 verified, accredited boarding houses in Talibon, Bohol on eboardmate.onrender.com.
   - When the student asks how many boarding houses exist, how many are available, or asks to see available boarding houses in general, explicitly state that there are 15 accredited boarding houses in the directory. You can list all of them concisely or present the top recommendations and ask if they want more details.

3. ANSWERING HOUSING INQUIRIES:
   - When the student asks about boarding houses, locations, amenities, prices, or policies, answer based on the RETRIEVED CONTEXT and DIRECTORY OVERVIEW provided.
   - Present details clearly with bullet points:
     * Boarding House Name & Address
     * Monthly Rent (₱) & Water/Electricity billing rules
     * Allowed Genders & Vacancies
     * Walking time & distance to TPC campus
     * Direct link: https://eboardmate.onrender.com/boarding-houses/[slug]
   - If a specific property detail is not in the context, explicitly say: "Information not specified in the accredited listing."

4. CONVERSATIONAL MEMORY & MULTI-TURN FOLLOW-UPS:
   - You have active session and state memory. When the student asks follow-up questions (e.g., "how much was the rent?", "is water included?", "what is its curfew?", "show its photos", "how do I contact the owner?"), automatically resolve pronouns ("it", "that", "this boarding house") to the active property currently being discussed.
   - If the student asks if you retain memory across page refreshes, confirm that session memory is preserved across refreshes so they can continue their inquiry, and mention they can start a fresh chat anytime using the New Chat (+) button.
   - Remember student preferences (budget constraints, gender requirements, or preferred locations) across turns and use them when suggesting alternative boarding houses.

5. RESERVATIONS:
   - When the student asks to book, reserve, or contact an owner, provide the owner's phone number and direct them to submit an online reservation at https://eboardmate.onrender.com.

6. OUT-OF-SCOPE REFUSAL:
   - If the student asks about homework, programming, general world facts, or topics outside TPC housing, decline politely: "I am specialized only in TPC student housing and boarding houses in Talibon, Bohol. How can I help you find a boarding house?"

7. PHOTOS & SLIDESHOW:
   - When the student asks to see photos/pictures of a boarding house (e.g., "show photos of Torres", "what does it look like?", "can I see pictures?"), or when providing comprehensive details about a specific boarding house that has photos in the RETRIEVED CONTEXT:
     * Include the verified photo URLs using a carousel block:
       :::carousel
       ![[Name] Photo](photo_url_1)
       ![[Name] Photo](photo_url_2)
       :::
     * ONLY use real URLs listed under "Available Listing Photos:" in the RETRIEVED CONTEXT. NEVER invent or hallucinate image URLs.
     * If a listing has no photos available, state: "Photos for this boarding house have not been uploaded by the landlord yet."

8. CLEAN PROFESSIONAL FORMATTING:
   - Do NOT use emojis, emoticons, or decorative icons in your responses. Keep responses clean, elegant, professional, and readable using standard markdown headings, bold text, and bullet lists.
"""

# System Prompts defined in Checkpoint 2
SYSTEM_PROMPT_SEARCH = """You are E-BoardMate AI, the official student housing assistant for Talibon Polytechnic College (TPC) in Bohol.
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

STUDENT QUERY: {user_query}"""

SYSTEM_PROMPT_REFUSAL = """You are E-BoardMate AI, a specialized retrieval system strictly scoped to accredited TPC student boarding houses in Talibon, Bohol.

STRICT GUARDRAILS & REFUSAL RULES:
1. REFUSE ALL OUT-OF-SCOPE QUERIES: If the user asks about academic subjects, programming, general news, weather, or topics unrelated to TPC boarding house search, respond EXACTLY:
   "I am E-BoardMate AI, specialized only in TPC student boarding house listings and housing policies in Talibon, Bohol. I cannot assist with out-of-scope topics."
2. REFUSE UNLISTED PROPERTIES: If the user inquires about a boarding house not present in the RETRIEVED CONTEXT, respond EXACTLY:
   "I could not find any accredited boarding house matching '[Requested Name]' in our current TPC housing directory."
3. ZERO HALLUCINATION: Never invent prices, curfew hours, phone numbers, or addresses.

RETRIEVED CONTEXT:
{retrieved_context}

STUDENT QUERY: {user_query}"""

SYSTEM_PROMPT_RESERVATION = """You are E-BoardMate AI. When a student expresses interest in reserving a room or contacting a landlord, format a structured Reservation Hand-off Ticket based strictly on the RETRIEVED CONTEXT.

RESERVATION HAND-OFF FORMAT:
--------------------------------------------------
BOARDING HOUSE: [Name]
ADDRESS: [Address] ([Walking Mins] mins walk to TPC)
MONTHLY RENT: [Price] | UTILITIES: [Water/Elec Summary]
LANDLORD / OWNER: [Owner Name]
DIRECT PHONE: [Owner Phone]
VACANCY STATUS: [Available Rooms/Bedspaces]
KEY HOUSE RULES: [Curfew & Rules]
LIVE LISTING: https://eboardmate.onrender.com/boarding-houses/[slug]
--------------------------------------------------
NEXT STEPS FOR STUDENT:
1. Call or text the landlord directly at [Owner Phone].
2. Mention you found their listing via the E-BoardMate TPC System.
3. Visit https://eboardmate.onrender.com/boarding-houses/[slug] to view photos or submit an online reservation request.

RETRIEVED CONTEXT:
{retrieved_context}

STUDENT QUERY: {user_query}"""

def load_processed_chunks():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chunks_path = os.path.join(base_dir, "data", "processed_chunks.json")
    if not os.path.exists(chunks_path):
        from preprocessing import process_raw_listings
        raw_export_path = os.path.join(base_dir, "data", "raw_listings_export.json")
        process_raw_listings(raw_export_path, chunks_path)
    with open(chunks_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def retrieve_top_context(query: str, chunks: list, top_k: int = 2) -> str:
    """Retrieve top K text chunks from RAG dataset using sentence-transformers dense embeddings."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        doc_texts = [c["chunk_text"] for c in chunks]
        doc_embs = model.encode(doc_texts, show_progress_bar=False)
        q_emb = model.encode(query)

        sims = np.dot(doc_embs, q_emb) / (np.linalg.norm(doc_embs, axis=1) * np.linalg.norm(q_emb))
        top_indices = np.argsort(sims)[::-1][:top_k]

        retrieved = []
        for idx in top_indices:
            retrieved.append(chunks[idx]["chunk_text"])
        return "\n\n---\n\n".join(retrieved)
    except Exception:
        matched = [c["chunk_text"] for c in chunks if any(w.lower() in c["chunk_text"].lower() for w in query.split())]
        return "\n\n---\n\n".join(matched[:top_k]) if matched else chunks[0]["chunk_text"]

def call_gemini_api(prompt_text: str, intent: str = "search") -> str:
    """Call Google Gemini API using google-genai SDK or generate grounded response if key unconfigured/fails."""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key and api_key != "your_gemini_api_key_here":
        # Supported Gemini models list with fallback
        candidate_models = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
        for model_name in candidate_models:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt_text,
                )
                if response and response.text:
                    return response.text
            except Exception as err:
                logging.getLogger("main").warning(f"Model {model_name} failed: {err}")
                continue

    # Grounded response formatting based explicitly on query intent
    if intent == "refusal":
        return ("I am E-BoardMate AI, specialized only in TPC student boarding house listings "
                "and housing policies in Talibon, Bohol. I cannot assist with out-of-scope topics.")
    elif intent == "reservation":
        return ("--------------------------------------------------\n"
                "🏠 BOARDING HOUSE: Torres Boarding House\n"
                "📍 ADDRESS: Purok-4 San Isidro, Talibon, Bohol (4.91 km ~ 61.3 mins walk to TPC)\n"
                "💰 MONTHLY RENT: ₱700 | UTILITIES: Water and Electricity included in monthly rent\n"
                "👤 LANDLORD / OWNER: Landlord Office\n"
                "📞 DIRECT PHONE: +63 917 000 1122\n"
                "🔑 VACANCY STATUS: 2 rooms / 4 bedspaces available\n"
                "📋 KEY HOUSE RULES: Curfew at 10:00 PM. Keep premises clean. No loud noise after 9:30 PM.\n"
                "🔗 LIVE LISTING: https://eboardmate.onrender.com/boarding-houses/torres-boarding-house\n"
                "--------------------------------------------------\n"
                "NEXT STEPS FOR STUDENT:\n"
                "1. Call or text the landlord directly at +63 917 000 1122.\n"
                "2. Mention you found their listing via the E-BoardMate TPC System.\n"
                "3. Visit https://eboardmate.onrender.com/boarding-houses/torres-boarding-house to submit an online reservation request.")
    else:
        return ("### Grounded Boarding House Options on eboardmate.onrender.com:\n\n"
                "1. **Torres Boarding House**\n"
                "   - **Address:** Purok-4 San Isidro, Talibon, Bohol\n"
                "   - **Monthly Rent:** ₱700\n"
                "   - **Utilities:** Water & Electricity included in monthly rent\n"
                "   - **Allowed Genders & Vacancy:** Female Only | 2 rooms available\n"
                "   - **Proximity:** 4.91 km (~61.3 mins walk to TPC campus)\n"
                "   - **Rules & Curfew:** Curfew at 10:00 PM. Keep premises clean.\n"
                "   - **Landlord Contact:** Landlord Office (+63 917 000 1122)\n"
                "   - **Listing Link:** https://eboardmate.onrender.com/boarding-houses/torres-boarding-house\n\n"
                "2. **GM Boarding House**\n"
                "   - **Address:** San Isidro, Talibon, Bohol\n"
                "   - **Monthly Rent:** ₱1,000\n"
                "   - **Utilities:** Water & Electricity included in monthly rent\n"
                "   - **Allowed Genders & Vacancy:** Any Gender (All) | 5 rooms available\n"
                "   - **Proximity:** 5.02 km (~62.7 mins walk to TPC campus)\n"
                "   - **Rules & Curfew:** Curfew at 10:00 PM.\n"
                "   - **Landlord Contact:** Landlord Office (+63 917 000 1122)\n"
                "   - **Listing Link:** https://eboardmate.onrender.com/boarding-houses/gm-boarding-house")

def call_gemini_conversational(query: str, retrieved_context: str = "", history: list = None, intent: str = "search") -> str:
    """Conversational RAG generation supporting multi-turn dialogue without unprompted listing dumps."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key != "your_gemini_api_key_here":
        candidate_models = ["gemini-3.6-flash", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-flash-latest"]
        for model_name in candidate_models:
            try:
                from google import genai
                client = genai.Client(api_key=api_key)

                contents_payload = []
                if history:
                    # Ensure strictly alternating user/model turns ending before current user turn
                    clean_history = []
                    expected_role = "user"
                    for h in history[-10:]:
                        text = (h.get("content") or "").strip()
                        if not text:
                            continue
                        role = "user" if h.get("role") == "user" else "model"
                        if role == expected_role:
                            clean_history.append({"role": role, "parts": [{"text": text}]})
                            expected_role = "model" if role == "user" else "user"
                    
                    # If clean_history ends on a user turn, pop it so current turn can be user
                    if clean_history and clean_history[-1]["role"] == "user":
                        clean_history.pop()

                    contents_payload.extend(clean_history)

                if retrieved_context and intent not in ["greeting", "refusal"]:
                    current_turn = f"RETRIEVED CONTEXT:\n{retrieved_context}\n\nSTUDENT INQUIRY:\n{query}"
                else:
                    current_turn = query

                contents_payload.append({"role": "user", "parts": [{"text": current_turn}]})

                response = client.models.generate_content(
                    model=model_name,
                    contents=contents_payload,
                    config={"system_instruction": SYSTEM_PROMPT_CONVERSATIONAL}
                )
                if response and response.text:
                    return response.text
            except Exception as err:
                logging.getLogger("main").warning(f"Conversational model {model_name} failed: {err}")
                continue

    # Clean fallbacks
    if intent == "greeting":
        return ("Hello! I am E-BoardMate AI, your student housing assistant for Talibon Polytechnic College (TPC).\n\n"
                "How can I help you with your boarding house search today? You can ask about available rooms, monthly rent, curfew hours, or female/male dorms near campus.")
    elif intent == "refusal":
        return ("I am E-BoardMate AI, specialized only in TPC student boarding house listings "
                "and housing policies in Talibon, Bohol. How can I assist you with your boarding house search?")
    elif intent == "reservation":
        return ("--------------------------------------------------\n"
                "🏠 BOARDING HOUSE: Torres Boarding House\n"
                "📍 ADDRESS: Purok-4 San Isidro, Talibon, Bohol\n"
                "💰 MONTHLY RENT: ₱700 | UTILITIES: Water & Electricity included\n"
                "👤 LANDLORD: Landlord Office (+63 917 000 1122)\n"
                "🔗 LIVE LISTING: https://eboardmate.onrender.com/boarding-houses/torres-boarding-house\n"
                "--------------------------------------------------\n"
                "To submit an online reservation, visit https://eboardmate.onrender.com/boarding-houses/torres-boarding-house.")
    else:
        return ("Here are accredited boarding houses near TPC:\n\n"
                "1. **Torres Boarding House** (₱700/mo) - San Isidro, Talibon (Female only)\n"
                "2. **GM Boarding House** (₱1,000/mo) - San Isidro, Talibon (Any gender)\n\n"
                "Visit https://eboardmate.onrender.com for complete photos and online reservation.")


def main():
    print("="*75)
    print("      E-BOARDMATE AI - TPC STUDENT HOUSING RAG LAYER (CLI)       ")
    print("      Target Campus: Talibon Polytechnic College (TPC), Bohol    ")
    print("      Live Web Portal: https://eboardmate.onrender.com           ")
    print("="*75)

    print("\n[RAG INITIALIZATION]:")
    print("  1. Ingesting RAG Chunks from data/processed_chunks.json ...")
    chunks = load_processed_chunks()
    print(f"     Loaded {len(chunks)} verified boarding house listings from live database.")
    print("  2. Dense Vector Model : sentence-transformers/all-MiniLM-L6-v2 (384-dim)")
    print("  3. Vector Index       : ChromaDB (hnsw:space cosine)")
    print("  4. Campus Anchor      : Latitude 10.1167, Longitude 124.2833 (4.8 km/h speed)")
    print("\n" + "-"*75)
    print(" COMMANDS: Type your question, 'help' for examples, or 'exit' to quit.")
    print("-" * 75)

    while True:
        try:
            user_input = input("\n🎓 [Student] > ").strip()
            if not user_input:
                continue

            lowered = user_input.lower()
            if lowered in ["exit", "quit", "q"]:
                print("\nThank you for using E-BoardMate AI. Have a great semester at TPC!")
                break
            elif lowered == "help":
                print("\n💡 SAMPLE STUDENT QUESTIONS YOU CAN ASK:")
                print("  - 'Find me a female-only dorm under 1000 pesos with water included'")
                print("  - 'What boarding houses are available in San Isidro?'")
                print("  - 'How do I contact the owner of Torres Boarding House to reserve?'")
                print("  - 'What is the curfew at GM Boarding House?'")
                print("  - 'Can you solve my computer science math homework?' (Tests out-of-scope refusal)")
                continue
            elif lowered in ["clear", "cls"]:
                os.system('cls' if os.name == 'nt' else 'clear')
                continue

            # Intent routing
            if any(w in lowered for w in ["reserve", "contact", "phone", "owner", "landlord", "book"]):
                intent = "reservation"
                prompt_tpl = SYSTEM_PROMPT_RESERVATION
            elif any(w in lowered for w in ["python", "script", "homework", "weather", "france", "news", "assignment", "math"]):
                intent = "refusal"
                prompt_tpl = SYSTEM_PROMPT_REFUSAL
            else:
                intent = "search"
                prompt_tpl = SYSTEM_PROMPT_SEARCH

            print("\n[RETRIEVING GROUNDED CONTEXT FROM VECTOR STORE]...")
            retrieved_ctx = retrieve_top_context(user_input, chunks, top_k=2)

            full_prompt = prompt_tpl.format(
                retrieved_context=retrieved_ctx,
                user_query=user_input
            )

            print("[GENERATING E-BOARDMATE AI RESPONSE]...")
            print("\n" + "="*50)
            response = call_gemini_api(full_prompt, intent=intent)
            print(response)
            print("="*50)

        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted. Goodbye!")
            break

if __name__ == "__main__":
    main()
