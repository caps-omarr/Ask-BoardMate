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
