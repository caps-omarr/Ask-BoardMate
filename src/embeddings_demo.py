import os
import sys
import json
import time
import warnings
import logging
import numpy as np

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

def generate_embeddings_demo():
    """
    Demonstrate embedding generation using sentence-transformers/all-MiniLM-L6-v2.
    Displays dimensions, vector slices, generation latency, and architectural justification.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    chunks_path = os.path.join(base_dir, "data", "processed_chunks.json")
    
    if not os.path.exists(chunks_path):
        raise FileNotFoundError(f"Processed chunks not found at {chunks_path}. Run preprocessing.py first.")
        
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
        
    print("="*70)
    print(" E-BOARDMATE EMBEDDING GENERATION DEMO & MODEL JUSTIFICATION ")
    print("="*70)
    
    print("\n[1] Loading Embedding Model: sentence-transformers/all-MiniLM-L6-v2 ...")
    start_load = time.time()
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    except ImportError:
        print("ERROR: sentence-transformers package not installed. Installing or fallback needed.")
        raise
        
    load_time = time.time() - start_load
    print(f"    Model loaded successfully in {load_time:.2f} seconds.")
    
    # Select 3 sample chunks
    sample_chunks = chunks[:3]
    sample_texts = [c["chunk_text"] for c in sample_chunks]
    
    print(f"\n[2] Encoding {len(sample_texts)} sample boarding house chunks into dense vectors...")
    start_embed = time.time()
    embeddings = model.encode(sample_texts, show_progress_bar=False)
    embed_time = time.time() - start_embed
    
    avg_per_doc = (embed_time / len(sample_texts)) * 1000
    
    print(f"    Encoding finished in {embed_time:.3f} seconds ({avg_per_doc:.1f} ms per document).")
    print(f"    Embeddings shape: {embeddings.shape}")
    print(f"    Vector dimensions: {embeddings.shape[1]}")
    
    print("\n[3] Inspection of Generated Vectors:")
    for idx, (chunk, emb) in enumerate(zip(sample_chunks, embeddings)):
        slice_vals = [round(float(v), 5) for v in emb[:6]]
        l2_norm = np.linalg.norm(emb)
        print(f"\n    Sample #{idx+1}: {chunk['name']}")
        print(f"    - Embedding Dimension : {len(emb)}")
        print(f"    - First 6 Vector Slices: {slice_vals} ...")
        print(f"    - L2 Norm (Magnitude) : {l2_norm:.4f} (Normalized = {np.isclose(l2_norm, 1.0)})")
        
    print("\n" + "="*70)
    print(" ARCHITECTURAL EMBEDDING MODEL JUSTIFICATION ")
    print("="*70)
    justification = """
    Selected Model: sentence-transformers/all-MiniLM-L6-v2

    Why all-MiniLM-L6-v2 for the E-BoardMate Capstone Project?
    
    1. COMPACT FOOTPRINT & LATENCY:
       Produces 384-dimensional dense vectors. Compared to 1536-dim (OpenAI text-embedding-3-small)
       or 768-dim (Gemini text-embedding-004), MiniLM requires 50-75% less storage space in 
       vector databases (ChromaDB) and reduces vector distance computation time significantly.
       
    2. CPU EFFICIENCY FOR LOCAL DEPLOYMENT:
       With only ~22.7 Million parameters, MiniLM runs blazingly fast on standard CPUs without requiring
       expensive GPU hardware. Sub-10ms per chunk embedding latency allows real-time indexing 
       and query resolution on student/local servers.
       
    3. SEMANTIC ACCURACY FOR SEARCH & RAG:
       Trained on over 1 Billion sentence pairs using contrastive learning. It achieves top-tier
       retrieval performance on semantic textual similarity benchmarks (STS), making it ideal
       for matching student query intents (e.g., "cheap female dorm near TPC with free wifi")
       against structured boarding house text chunks.
       
    4. ZERO API COST & RATE LIMIT RESILIENCE:
       Local execution eliminates external API keys, rate limits, and network latency bottlenecks
       for vector generation during batch pipeline runs and local search requests.
    """
    print(justification)
    print("="*70)

if __name__ == "__main__":
    generate_embeddings_demo()
