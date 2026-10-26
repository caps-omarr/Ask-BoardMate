import json
import math
import re
import os
import sys
import html
from typing import Dict, List, Any

# Ensure UTF-8 output encoding for Windows terminals
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Talibon Polytechnic College (TPC) Campus Anchor Coordinates
TPC_LAT = 10.1167
TPC_LON = 124.2833
WALKING_SPEED_KMH = 4.8  # Standard human walking speed in km/h

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two GPS points 
    (in decimal degrees) in kilometers using the Haversine formula.
    """
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def clean_html_entities_and_whitespace(text: str) -> str:
    """Unescape HTML entities, strip HTML tags, and normalize whitespace."""
    if not text:
        return ""
    # Unescape HTML entities (e.g. &amp;, &lt;, &nbsp;)
    unescaped = html.unescape(text)
    # Remove HTML tags
    cleaned = re.sub(r'<[^>]+>', ' ', unescaped)
    # Replace multiple whitespaces/newlines with single space
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def normalize_gender_restriction(raw_gender: str) -> str:
    """Normalize inconsistent gender casing and informal dialect terms."""
    if not raw_gender:
        return "Any Gender (All)"
    normalized = raw_gender.strip().lower()
    if "fem" in normalized or "lady" in normalized or "girl" in normalized or "women" in normalized:
        return "Female Only"
    elif "male" in normalized or "boy" in normalized or "men" in normalized or "gent" in normalized:
        return "Male Only"
    else:
        return "Any Gender (All)"

def estimate_walking_minutes(distance_km: float) -> float:
    """Estimate walking time in minutes at standard 4.8 km/h speed."""
    hours = distance_km / WALKING_SPEED_KMH
    return round(hours * 60, 1)

def format_listing_chunk(listing: Dict[str, Any], dist_km: float, walking_mins: float, clean_desc: str) -> str:
    """Assemble structured text chunk containing complete property context."""
    water_detail = listing.get("water_billing_details") or "No specific water billing terms provided."
    elec_detail = listing.get("electricity_billing_details") or "No specific electricity billing terms provided."
    
    water_status = "Included in rent" if listing.get("includes_water") else f"Separate billing ({water_detail})"
    elec_status = "Included in rent" if listing.get("includes_electricity") else f"Separate billing ({elec_detail})"
    
    amenities_list = listing.get("amenities", [])
    amenities_str = ", ".join(amenities_list) if amenities_list else "Basic student accommodations"

    photos_list = listing.get("photos", [])
    photos_str = " ".join([f"![{listing['name']} Photo]({url})" for url in photos_list]) if photos_list else "None available"
    
    chunk = (
        f"BOARDING HOUSE LISTING: {listing['name']}\n"
        f"Address: {listing['address']}\n"
        f"Proximity to TPC Campus: {dist_km:.2f} km (~{walking_mins} mins walk)\n"
        f"Monthly Rent: ₱{listing['rent_price']:,}\n"
        f"Allowed Genders: {listing['allowed_genders']}\n"
        f"Room Availability: {listing.get('available_rooms', 0)} rooms available out of {listing.get('total_rooms', 0)}\n"
        f"Bedspace Availability: {listing.get('available_bedspaces', 0)} bedspaces available out of {listing.get('total_bedspaces', 0)}\n"
        f"Water Utility: {water_status}\n"
        f"Electricity Utility: {elec_status}\n"
        f"Amenities: {amenities_str}\n"
        f"House Rules & Curfew: {listing.get('rules', 'Standard quiet house rules apply.')}\n"
        f"Landlord Contact: {listing.get('owner_name', 'Landlord')} ({listing.get('owner_phone', 'N/A')})\n"
        f"Direct Listing Link: https://eboardmate.onrender.com/boarding-houses/{listing.get('slug', '')}\n"
        f"Available Listing Photos:\n{photos_str}\n"
        f"Description: {clean_desc}"
    )
    return chunk

def process_raw_listings(raw_filepath: str, output_filepath: str) -> List[Dict[str, Any]]:
    """Clean, normalize, tokenize, and format raw listings into RAG chunks."""
    # Fallback path if raw_listings_export.json not found
    if not os.path.exists(raw_filepath):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        fallback_path = os.path.join(base_dir, "data", "raw_listings.json")
        if os.path.exists(fallback_path):
            raw_filepath = fallback_path
        else:
            raise FileNotFoundError(f"Neither {raw_filepath} nor fallback {fallback_path} exists.")

    print("="*70)
    print(" E-BOARDMATE PREPROCESSING & TOKENS SANITATION PIPELINE ")
    print("="*70)
    print(f"Ingesting raw listings from: {raw_filepath}\n")

    with open(raw_filepath, 'r', encoding='utf-8') as f:
        raw_listings = json.load(f)

    processed_chunks = []

    for idx, listing in enumerate(raw_listings):
        # 1. Clean HTML markup and whitespace
        raw_desc = listing.get("description", "")
        clean_desc = clean_html_entities_and_whitespace(raw_desc)

        # 2. Normalize gender casing
        norm_gender = normalize_gender_restriction(listing.get("allowed_genders", ""))
        listing["allowed_genders"] = norm_gender

        # 3. Compute spatial metrics from TPC Anchor (10.1167, 124.2833)
        dist_km = haversine_distance(TPC_LAT, TPC_LON, float(listing["latitude"]), float(listing["longitude"]))
        walking_mins = estimate_walking_minutes(dist_km)

        # 4. Assemble structured chunk
        chunk_text = format_listing_chunk(listing, dist_km, walking_mins, clean_desc)
        token_count_approx = len(chunk_text.split())

        has_available_slot = listing.get("available_bedspaces", 0) > 0 or listing.get("available_rooms", 0) > 0

        record = {
            "chunk_id": f"chunk-{listing['id']}",
            "listing_id": listing["id"],
            "name": listing["name"],
            "slug": listing["slug"],
            "chunk_text": chunk_text,
            "token_count_approx": token_count_approx,
            "metadata": {
                "id": listing["id"],
                "name": listing["name"],
                "slug": listing["slug"],
                "address": listing["address"],
                "rent_price": listing["rent_price"],
                "allowed_genders": norm_gender,
                "available_rooms": listing.get("available_rooms", 0),
                "available_bedspaces": listing.get("available_bedspaces", 0),
                "has_available_slot": has_available_slot,
                "distance_km": round(dist_km, 3),
                "walking_mins": walking_mins,
                "includes_water": listing.get("includes_water", False),
                "includes_electricity": listing.get("includes_electricity", False),
                "owner_name": listing.get("owner_name", ""),
                "owner_phone": listing.get("owner_phone", ""),
                "photos": listing.get("photos", []),
                "is_verified": listing.get("is_verified", True)
            }
        }
        processed_chunks.append(record)

        # Print BEFORE / AFTER tokenization sample for first 2 records
        if idx < 2:
            print(f"--------------------------------------------------")
            print(f"SAMPLE RECORD #{idx+1}: {listing['name']}")
            print(f"--------------------------------------------------")
            print(f"[RAW BEFORE CLEANING]:")
            print(f"  Description: {raw_desc}")
            print(f"  Allowed Genders (Raw): {listing.get('allowed_genders')}")
            print(f"\n[AFTER SANITATION & COMPUTATION]:")
            print(f"  Cleaned Description: {clean_desc}")
            print(f"  Normalized Gender  : {norm_gender}")
            print(f"  Spatial Proximity  : {dist_km:.3f} km from TPC Campus (~{walking_mins} mins walk)")
            print(f"  Approx Token Count : {token_count_approx} words")
            print(f"\n[GENERATED RAG CHUNK TEXT]:\n{chunk_text}\n")

    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(processed_chunks, f, indent=2, ensure_ascii=False)

    print("="*70)
    print(f" Successfully processed {len(processed_chunks)} boarding house chunks.")
    print(f" Saved normalized RAG dataset to: {output_filepath}")
    print("="*70)
    return processed_chunks

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_export_path = os.path.join(base_dir, "data", "raw_listings_export.json")
    out_chunks_path = os.path.join(base_dir, "data", "processed_chunks.json")
    process_raw_listings(raw_export_path, out_chunks_path)
