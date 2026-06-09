import os
import pickle
import time
import numpy as np

# Configure offline environments
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from logger import logger

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vectordb")
INDEX_FILE = os.path.join(VECTOR_DB_DIR, "faiss.index")
METADATA_FILE = os.path.join(VECTOR_DB_DIR, "metadata.pkl")

# Retrieval Config
TOP_K = 6
SEARCH_K = 30
MIN_SCORE = 0.35
RERANKER_MODEL = "BAAI/bge-reranker-base"
EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"

# Detect Low-RAM Mode (Render Free Tier 512MB RAM constraint)
LOW_RAM_MODE = (
    os.getenv("LOW_RAM_MODE", "false").lower() == "true"
    or os.getenv("RENDER", "false").lower() == "true"
)

# Placeholders for heavy ML variables
embedding_model = None
reranker = None
index = None
texts = []
metadata = []

# Always load the lightweight metadata cache if it exists
try:
    with open(METADATA_FILE, "rb") as f:
        db = pickle.load(f)
    texts = db["texts"]
    metadata = db["metadata"]
    print(f"Loaded {len(texts):,} chunks from metadata cache.")
except Exception as cache_err:
    print(f"Warning: Failed to load metadata cache: {cache_err}")

# Load heavy libraries and models dynamically only if not in LOW_RAM_MODE
if LOW_RAM_MODE:
    print("INFO:     LOW_RAM_MODE is active. Skipping heavy ML models (SentenceTransformer, FAISS, reranker) to prevent OOM crashes.")
else:
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
        from FlagEmbedding import FlagReranker
        import torch

        # Restrict PyTorch thread count to avoid FastAPI background thread deadlocks on Windows CPU
        torch.set_num_threads(1)

        print(f"\nLoading {EMBEDDING_MODEL_NAME} embedding model...")
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
        print("Embedding Model Loaded.")

        print("Loading reranker model...")
        reranker = FlagReranker(RERANKER_MODEL, use_fp16=False)
        print("Reranker Loaded.")

        print("Loading FAISS Index...")
        index = faiss.read_index(INDEX_FILE)
        print(f"FAISS Index Loaded successfully with {len(texts):,} items.")
    except Exception as ml_err:
        print(f"ERROR:    Failed to initialize heavy ML models: {ml_err}. Falling back to LOW_RAM_MODE.")
        LOW_RAM_MODE = True

# =====================================================
# RERANKER
# =====================================================

def rerank_results(query, candidates, final_k=TOP_K):
    if len(candidates) == 0:
        return []

    # If running in Low-RAM Mode or reranker failed to load, skip neural reranking
    if LOW_RAM_MODE or not reranker:
        return candidates[:final_k]

    pairs = [(query, item["content"]) for item in candidates]
    
    try:
        rerank_scores = reranker.compute_score(pairs)
        if not isinstance(rerank_scores, list):
            rerank_scores = [rerank_scores]
            
        for item, score in zip(candidates, rerank_scores):
            item["rerank_score"] = float(score)

        candidates.sort(key=lambda x: x.get("rerank_score", -9999), reverse=True)
    except Exception as rerank_err:
        print(f"Warning: Reranker failed: {rerank_err}. Skipping reranking.")
        
    return candidates[:final_k]

# =====================================================
# LOGGER
# =====================================================

def log_results(query, section_name, results, retrieval_time):
    logger.info("=" * 120)
    logger.info(f"QUERY: {query}")
    logger.info(f"SECTION: {section_name}")
    logger.info(f"RETRIEVAL TIME: {retrieval_time:.2f}s")
    logger.info(f"TOTAL RETRIEVED: {len(results)}")

    if results:
        avg_score = sum(r["score"] for r in results) / len(results)
        unique_sources = set(r["metadata"].get("source") for r in results if "metadata" in r)
        logger.info(f"AVERAGE FAISS/SIMILARITY SCORE: {avg_score:.4f}")
        logger.info(f"UNIQUE SOURCES: {len(unique_sources)}")
        logger.info(f"SOURCES: {list(unique_sources)}")

    for rank, item in enumerate(results, start=1):
        logger.info("-" * 80)
        logger.info(f"RANK: {rank}")
        logger.info(f"SIMILARITY SCORE: {item['score']:.4f}")
        if "rerank_score" in item:
            logger.info(f"RERANK SCORE: {item['rerank_score']:.4f}")
        meta = item.get("metadata", {})
        logger.info(f"SOURCE: {meta.get('source')}")
        logger.info(f"SECTION: {meta.get('section')}")
        logger.info(f"CHUNK ID: {meta.get('chunk_id')}")
        logger.info(item["content"][:1500])

# =====================================================
# KEYWORD RETRIEVAL FALLBACK (Low-RAM Mode)
# =====================================================

def retrieve_keyword_fallback(query, search_k=SEARCH_K, section_name=None):
    query_words = [w.lower() for w in query.replace("-", " ").replace(",", " ").split() if len(w) > 2]
    if not query_words:
        query_words = [query.lower()]

    candidates = []
    for idx, text in enumerate(texts):
        meta = metadata[idx] if idx < len(metadata) else {}
        
        # Apply section filter if section_name is specified
        if section_name:
            section = str(meta.get("section", "")).upper()
            if section_name.upper() not in section:
                continue

        text_lower = text.lower()
        overlap = sum(1 for word in query_words if word in text_lower)
        if overlap > 0:
            # Score matches between MIN_SCORE and 1.0 based on query word overlap
            score = MIN_SCORE + (1.0 - MIN_SCORE) * (overlap / len(query_words))
            candidates.append({
                "score": float(score),
                "content": text,
                "metadata": meta
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:search_k]

# =====================================================
# GENERAL RETRIEVAL
# =====================================================

def retrieve(query, top_k=TOP_K, search_k=SEARCH_K):
    start_time = time.time()

    if LOW_RAM_MODE or not embedding_model or not index:
        results = retrieve_keyword_fallback(query, search_k=search_k)
    else:
        try:
            query_embedding = embedding_model.encode([query], normalize_embeddings=True)
            query_embedding = np.array(query_embedding, dtype=np.float32)
            scores, indices = index.search(query_embedding, search_k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or score < MIN_SCORE:
                    continue
                results.append({
                    "score": float(score),
                    "content": texts[idx],
                    "metadata": metadata[idx] if idx < len(metadata) else {}
                })
        except Exception as search_err:
            print(f"Warning: Dense search failed: {search_err}. Falling back to keyword search.")
            results = retrieve_keyword_fallback(query, search_k=search_k)

    results = rerank_results(query, results, final_k=top_k)
    retrieval_time = time.time() - start_time
    log_results(query, "GENERAL", results, retrieval_time)
    
    return results

# =====================================================
# SECTION RETRIEVAL
# =====================================================

def retrieve_by_section(query, section_name, top_k=TOP_K, search_k=SEARCH_K):
    start_time = time.time()

    if LOW_RAM_MODE or not embedding_model or not index:
        results = retrieve_keyword_fallback(query, search_k=search_k, section_name=section_name)
    else:
        try:
            query_embedding = embedding_model.encode([query], normalize_embeddings=True)
            query_embedding = np.array(query_embedding, dtype=np.float32)
            scores, indices = index.search(query_embedding, search_k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or score < MIN_SCORE:
                    continue
                meta = metadata[idx] if idx < len(metadata) else {}
                section = str(meta.get("section", "")).upper()
                if section_name.upper() in section:
                    results.append({
                        "score": float(score),
                        "content": texts[idx],
                        "metadata": meta
                    })
        except Exception as search_err:
            print(f"Warning: Dense section search failed: {search_err}. Falling back to keyword search.")
            results = retrieve_keyword_fallback(query, search_k=search_k, section_name=section_name)

    results = rerank_results(query, results, final_k=top_k)
    retrieval_time = time.time() - start_time
    log_results(query, section_name, results, retrieval_time)

    return results

# =====================================================
# CONTEXT BUILDER
# =====================================================

def build_context(query, section_name=None, top_k=TOP_K):
    if section_name:
        results = retrieve_by_section(query, section_name, top_k)
    else:
        results = retrieve(query, top_k)

    context_parts = []
    for item in results:
        meta = item.get("metadata", {})
        context_parts.append(
            f"SOURCE: {meta.get('source')}\n"
            f"SECTION: {meta.get('section')}\n"
            f"PAGE: {meta.get('page')}\n\n"
            f"{item['content']}"
        )

    return "\n\n".join(context_parts)

# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    query = input("\nEnter Tender for Generation: ")
    section = input("\nSection (leave blank for general search): ")

    if section.strip():
        results = retrieve_by_section(query, section)
    else:
        results = retrieve(query)

    print(f"\nRetrieved {len(results)} chunks")
    if len(results) == 0:
        print("\nNo chunks passed the similarity threshold.")

    for i, item in enumerate(results, start=1):
        print("\n" + "=" * 80)
        meta = item.get("metadata", {})
        print(f"[{i}] {meta.get('source')}")
        print(f"Similarity Score: {item['score']:.4f}")
        if "rerank_score" in item:
            print(f"Rerank Score: {item['rerank_score']:.4f}")
        print(f"Section: {meta.get('section')}")
        print(f"Chunk ID: {meta.get('chunk_id')}")
        print(item["content"][:700])