import os
import sys
import json
import warnings
import logging
from typing import List, Dict, Any

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

def init_and_index_vector_store(chunks_filepath: str, db_dir: str = None):
    """
    Ingest processed boarding house chunks into ChromaDB with relational metadata.
    """
    import chromadb
    from sentence_transformers import SentenceTransformer

    if not os.path.exists(chunks_filepath):
        raise FileNotFoundError(f"Chunks file not found at {chunks_filepath}. Run preprocessing.py first.")
        
    with open(chunks_filepath, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print("="*70)
    print(" CHROMADB VECTOR INDEXING & METADATA-FILTERED RETRIEVAL DEMO ")
    print("="*70)
    
    # Initialize embedding model
    print("\n[1] Initializing SentenceTransformer ('sentence-transformers/all-MiniLM-L6-v2')...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    # Initialize ChromaDB client (Persistent or Ephemeral)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        client = chromadb.PersistentClient(path=db_dir)
        print(f"[2] Initialized ChromaDB Persistent Client at: {db_dir}")
    else:
        client = chromadb.EphemeralClient()
        print("[2] Initialized ChromaDB Ephemeral Client")

    collection_name = "eboardmate_listings"
    # Reset collection if exists
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    ids = []
    documents = []
    metadatas = []

    print(f"\n[3] Preparing {len(chunks)} document chunks for embedding and indexing...")
    for item in chunks:
        ids.append(item["chunk_id"])
        documents.append(item["chunk_text"])
        metadatas.append(item["metadata"])

    # Batch embedding generation
    embeddings = model.encode(documents, show_progress_bar=False).tolist()

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"    Successfully indexed {collection.count()} listings into ChromaDB collection '{collection_name}'.")
    return client, collection, model

def run_sample_queries(collection, model):
    """Run vector search queries with metadata pre-filtering."""
    print("\n" + "="*70)
    print(" METADATA-FILTERED VECTOR QUERY EXECUTION ")
    print("="*70)

    # Test Query 1: Female-only dorms under ₱1,500
    query_1_text = "Female dorm near TPC main gate under 1500 pesos with free water"
    where_filter_1 = {
        "$and": [
            {"rent_price": {"$lte": 1500}},
            {"allowed_genders": {"$eq": "Female Only"}}
        ]
    }
    
    print(f"\nQUERY 1: '{query_1_text}'")
    print(f"METADATA FILTER: rent_price <= 1500 AND allowed_genders == 'Female Only'")
    
    q1_embedding = model.encode([query_1_text]).tolist()
    results_1 = collection.query(
        query_embeddings=q1_embedding,
        n_results=3,
        where=where_filter_1
    )
    print_query_results(results_1)

    # Test Query 2: Budget male bedspaces under ₱1,000 with available slots
    query_2_text = "Cheap male bedspace under 1000 pesos all-in near campus"
    where_filter_2 = {
        "$and": [
            {"rent_price": {"$lte": 1000}},
            {"allowed_genders": {"$eq": "Male Only"}},
            {"has_available_slot": {"$eq": True}}
        ]
    }

    print(f"\nQUERY 2: '{query_2_text}'")
    print(f"METADATA FILTER: rent_price <= 1000 AND allowed_genders == 'Male Only' AND has_available_slot == True")

    q2_embedding = model.encode([query_2_text]).tolist()
    results_2 = collection.query(
        query_embeddings=q2_embedding,
        n_results=3,
        where=where_filter_2
    )
    print_query_results(results_2)

def print_query_results(results):
    """Helper to display retrieved candidate listings from ChromaDB."""
    ids = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]

    for idx, (doc_id, dist, meta, doc) in enumerate(zip(ids, distances, metadatas, documents)):
        sim_score = 1 - dist  # Cosine similarity score
        print(f"  [{idx+1}] ID: {doc_id} | Cosine Sim: {sim_score:.4f} (Dist: {dist:.4f})")
        print(f"      Name: {meta['name']} | Rent: ₱{meta['rent_price']:,} | Gender: {meta['allowed_genders']}")
        print(f"      Proximity: {meta['distance_km']} km ({meta['walking_mins']} mins walk) | Phone: {meta['owner_phone']}")
        print(f"      Link: https://eboardmate.onrender.com/boarding-houses/{meta.get('slug', '')}")
        excerpt = doc.splitlines()[0] if doc.splitlines() else ""
        print(f"      Excerpt: {excerpt}\n")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chunks_path = os.path.join(base_dir, "data", "processed_chunks.json")
    db_path = os.path.join(base_dir, "chroma_db")
    client, collection, model = init_and_index_vector_store(chunks_path, db_path)
    run_sample_queries(collection, model)
