import os
import faiss
import pickle
import numpy as np
import time

##os.environ["HF_HUB_OFFLINE"] = "1"
##os.environ["TRANSFORMERS_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer
from FlagEmbedding import FlagReranker

from logger import logger

# =====================================================
# PATHS
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

VECTOR_DB_DIR = os.path.join(
    BASE_DIR,
    "vectordb"
)

INDEX_FILE = os.path.join(
    VECTOR_DB_DIR,
    "faiss.index"
)

METADATA_FILE = os.path.join(
    VECTOR_DB_DIR,
    "metadata.pkl"
)

# =====================================================
# RETRIEVAL CONFIG
# =====================================================

TOP_K = 6

SEARCH_K = 30

MIN_SCORE = 0.35

RERANKER_MODEL = "BAAI/bge-reranker-base"
# =====================================================
# LOAD EMBEDDING MODEL
# =====================================================

EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"

print(f"\nLoading {EMBEDDING_MODEL_NAME}...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL_NAME,
    local_files_only=True
)

print("Embedding Model Loaded")
# =====================================================
# LOAD RERANKER
# =====================================================

print("Loading Reranker...")

reranker = FlagReranker(
    RERANKER_MODEL,
    use_fp16=False
)
print("Reranker Loaded")

# =====================================================
# LOAD FAISS
# =====================================================

print("Loading FAISS Index...")

index = faiss.read_index(
    INDEX_FILE
)

with open(
    METADATA_FILE,
    "rb"
) as f:

    db = pickle.load(f)

texts = db["texts"]
metadata = db["metadata"]

print(
    f"Loaded {len(texts):,} chunks"
)

# =====================================================
# RERANKER
# =====================================================

def rerank_results(
        query,
        candidates,
        final_k=TOP_K
):

    if len(candidates) == 0:
        return []

    pairs = []

    for item in candidates:

        pairs.append(
            (
                query,
                item["content"]
            )
        )

    rerank_scores = reranker.compute_score(
        pairs
    )

    for item, score in zip(
        candidates,
        rerank_scores
    ):

        item["rerank_score"] = float(
            score
        )

    candidates.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return candidates[:final_k]

# =====================================================
# LOGGER
# =====================================================

def log_results(
        query,
        section_name,
        results,
        retrieval_time
):

    logger.info("=" * 120)

    logger.info(
        f"QUERY: {query}"
    )

    logger.info(
        f"SECTION: {section_name}"
    )

    logger.info(
        f"RETRIEVAL TIME: {retrieval_time:.2f}s"
    )

    logger.info(
        f"TOTAL RETRIEVED: {len(results)}"
    )

    if results:

        avg_score = sum(
            r["score"]
            for r in results
        ) / len(results)

        unique_sources = set(
            r["metadata"].get("source")
            for r in results
        )

        logger.info(
            f"AVERAGE FAISS SCORE: {avg_score:.4f}"
        )

        logger.info(
            f"UNIQUE SOURCES: {len(unique_sources)}"
        )

        logger.info(
            f"SOURCES: {list(unique_sources)}"
        )

    for rank, item in enumerate(
        results,
        start=1
    ):

        logger.info("-" * 80)

        logger.info(
            f"RANK: {rank}"
        )

        logger.info(
            f"FAISS SCORE: {item['score']:.4f}"
        )

        if "rerank_score" in item:

            logger.info(
                f"RERANK SCORE: "
                f"{item['rerank_score']:.4f}"
            )

        logger.info(
            f"SOURCE: {item['metadata'].get('source')}"
        )

        logger.info(
            f"SECTION: {item['metadata'].get('section')}"
        )

        logger.info(
            f"CHUNK ID: {item['metadata'].get('chunk_id')}"
        )

        logger.info(
            item["content"][:1500]
        )

# =====================================================
# GENERAL RETRIEVAL
# =====================================================

def retrieve(
        query,
        top_k=TOP_K,
        search_k=SEARCH_K
):

    start_time = time.time()

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True
    )

    query_embedding = np.array(
        query_embedding,
        dtype=np.float32
    )

    scores, indices = index.search(
        query_embedding,
        search_k
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx < 0:
            continue

        if score < MIN_SCORE:
            continue

        results.append({

            "score": float(score),

            "content": texts[idx],

            "metadata": metadata[idx]
        })

    results = rerank_results(
        query,
        results,
        final_k=top_k
    )

    retrieval_time = (
        time.time() - start_time
    )

    log_results(
        query,
        "GENERAL",
        results,
        retrieval_time
    )

    return results

# =====================================================
# SECTION RETRIEVAL
# =====================================================

def retrieve_by_section(
        query,
        section_name,
        top_k=TOP_K,
        search_k=SEARCH_K
):

    start_time = time.time()

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True
    )

    query_embedding = np.array(
        query_embedding,
        dtype=np.float32
    )

    scores, indices = index.search(
        query_embedding,
        search_k
    )

    results = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx < 0:
            continue

        if score < MIN_SCORE:
            continue

        meta = metadata[idx]

        section = str(
            meta.get(
                "section",
                ""
            )
        ).upper()

        if section_name.upper() in section:

            results.append({

                "score": float(score),

                "content": texts[idx],

                "metadata": meta
            })

    results = rerank_results(
        query,
        results,
        final_k=top_k
    )

    retrieval_time = (
        time.time() - start_time
    )

    log_results(
        query,
        section_name,
        results,
        retrieval_time
    )

    return results

# =====================================================
# CONTEXT BUILDER
# =====================================================

def build_context(
        query,
        section_name=None,
        top_k=TOP_K
):

    if section_name:

        results = retrieve_by_section(
            query,
            section_name,
            top_k
        )

    else:

        results = retrieve(
            query,
            top_k
        )

    context_parts = []

    for item in results:

        meta = item["metadata"]

        context_parts.append(
            f"""
SOURCE: {meta.get('source')}
SECTION: {meta.get('section')}
PAGE: {meta.get('page')}

{item['content']}
"""
        )

    return "\n\n".join(context_parts)
# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":

    query = input(
        "\nEnter Tender for Generation: "
    )

    section = input(
        "\nSection (leave blank for general search): "
    )

    if section.strip():

        results = retrieve_by_section(
            query,
            section
        )

    else:

        results = retrieve(
            query
        )

    print(
        f"\nRetrieved {len(results)} chunks"
    )

    if len(results) == 0:

        print(
            "\nNo chunks passed the similarity threshold."
        )

    for i, item in enumerate(
        results,
        start=1
    ):

        print("\n" + "=" * 80)

        print(
            f"[{i}] {item['metadata'].get('source')}"
        )

        print(
            f"FAISS Score: {item['score']:.4f}"
        )

        if "rerank_score" in item:

            print(
                f"Rerank Score: "
                f"{item['rerank_score']:.4f}"
            )

        print(
            f"Section: "
            f"{item['metadata'].get('section')}"
        )

        print(
            f"Chunk ID: "
            f"{item['metadata'].get('chunk_id')}"
        )

        print(
            item["content"][:700]
        )