import os
import pickle
import time
import numpy as np
import json

try:
    from dotenv import load_dotenv
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(backend_dir)
    load_dotenv(os.path.join(backend_dir, ".env"))
    load_dotenv(os.path.join(root_dir, ".env"))
except ImportError:
    pass

# Configure offline environments
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from logger import logger

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vectordb")
INDEX_FILE = os.path.join(VECTOR_DB_DIR, "faiss.index")
METADATA_FILE = os.path.join(VECTOR_DB_DIR, "metadata.pkl")
COMPANY_INDEX_FILE = os.path.join(
    VECTOR_DB_DIR,
    "company_index.json"
)

company_index = {}


try:

    with open(
        COMPANY_INDEX_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        company_index = json.load(f)

    print(
        f"Loaded company index for "
        f"{len(company_index)} companies."
    )

except Exception as e:

    print(
        f"Failed to load company index: {e}"
    )

# Retrieval Config
TOP_K = 20
SEARCH_K = 300
MIN_SCORE = 0.05
RERANKER_MODEL = os.path.join(
    BASE_DIR,
    "backend",
    "models",
    "bge-reranker-v2-m3"
)
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
        data = pickle.load(f)

    texts = data["texts"]
    metadata = data["metadata"]

    print(f"Loaded {len(metadata):,} chunks from metadata cache.")

except Exception as cache_err:
    print(f"Warning: Failed to load metadata cache: {cache_err}")

# Load heavy libraries and models dynamically only if not in LOW_RAM_MODE
# Load heavy libraries and models dynamically only if not in LOW_RAM_MODE
if LOW_RAM_MODE:
    print("INFO: LOW_RAM_MODE is active. Skipping heavy ML models.")
else:
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
        from FlagEmbedding import FlagReranker
        import torch

        # Restrict PyTorch thread count
        torch.set_num_threads(1)

        # ==========================================
        # EMBEDDING MODEL
        # ==========================================

        print(f"\nLoading {EMBEDDING_MODEL_NAME} embedding model...")

        embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME,
            local_files_only=True
        )

        print("Embedding Model Loaded.")

        # ==========================================
        # RERANKER
        # ==========================================

        print("Loading reranker model...")

        reranker = FlagReranker(
            RERANKER_MODEL,
            use_fp16=False
        )

        print("Reranker Loaded.")

        # ==========================================
        # FAISS INDEX
        # ==========================================

        print("Loading FAISS Index...")

        index = faiss.read_index(
            INDEX_FILE
        )

        print(
            f"FAISS Index Loaded successfully "
            f"with {index.ntotal:,} items."
        )

    except Exception as ml_err:

        print(
            f"ERROR: Failed to initialize "
            f"heavy ML models: {ml_err}"
        )

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
# SECTION KEY MAPPING / NORMALIZATION
# =====================================================
def normalize_section_name(name):
    if not name:
        return "GENERAL"
    
    name_upper = name.strip().upper()
    
    # Mapping of human readable section names to DB section keys
    mapping = {
        "NOTICE INVITING TENDER": "NOTICE_INVITING_TENDER",
        "INSTRUCTIONS TO BIDDERS": "BID_SUBMISSION",
        "ELIGIBILITY CRITERIA": "ELIGIBILITY",
        "SCOPE OF WORK": "SCOPE_OF_WORK",
        "TECHNICAL SPECIFICATION": "TECHNICAL",
        "QUALITY ASSURANCE": "QUALITY",
        "INSPECTION AND TESTING": "GENERAL",
        "PACKING AND MARKING": "GENERAL",
        "DELIVERY CONDITIONS": "DELIVERY",
        "PAYMENT TERMS": "COMMERCIAL",
        "SAFETY REQUIREMENTS": "SAFETY",
        "GENERAL CONDITIONS OF CONTRACT": "GCC",
        "SPECIAL CONDITIONS OF CONTRACT": "SCC",
        "PENALTY CLAUSE": "PENALTY",
        "ANNEXURES": "ANNEXURE",
        "FORMS": "GENERAL"
    }
    
    # First check mapping
    if name_upper in mapping:
        return mapping[name_upper]
        
    # Also check if it's already a valid DB key (with underscores instead of spaces)
    normalized = name_upper.replace(" ", "_")
    valid_db_keys = {
        "NOTICE_INVITING_TENDER", "SCOPE_OF_WORK", "ELIGIBILITY", "TECHNICAL", 
        "COMMERCIAL", "BID_SUBMISSION", "EVALUATION", "GCC", "SCC", 
        "SAFETY", "QUALITY", "DELIVERY", "PENALTY", "BOQ", "ANNEXURE", "GENERAL"
    }
    
    if normalized in valid_db_keys:
        return normalized
        
    # Check substring matches
    for key in valid_db_keys:
        if key in normalized or normalized in key:
            return key
            
    return "GENERAL"

# =====================================================
# KEYWORD RETRIEVAL FALLBACK (Low-RAM Mode)
# =====================================================
def retrieve_keyword_fallback(
    query,
    company=None,
    tender_type=None,
    search_k=SEARCH_K,
    section_name=None
):

    query_words = [
        w.lower()
        for w in query.replace("-", " ")
                      .replace(",", " ")
                      .split()
        if len(w) > 2
    ]

    if not query_words:
        query_words = [query.lower()]

    candidates = []

    for idx, text in enumerate(texts):

        meta = metadata[idx] if idx < len(metadata) else {}

        # Company Filter
        if company:

            chunk_company = meta.get(
                "company_folder",
                ""
            )

            if (
                chunk_company.upper()
                != company.upper()
            ):
                continue

        # Tender Type Filter
        if tender_type:

            chunk_type = meta.get(
                "tender_type",
                ""
            )

            if (
                tender_type.upper()
                not in chunk_type.upper()
            ):
                continue

        # Section Filter
        if section_name:

            section = str(
                meta.get(
                    "section",
                    ""
                )
            ).upper()

            db_section_name = normalize_section_name(section_name)
            if db_section_name != section:
                continue

        text_lower = text.lower()

        overlap = sum(
            1
            for word in query_words
            if word in text_lower
        )

        if overlap > 0:

            score = (
                MIN_SCORE
                + (1.0 - MIN_SCORE)
                * (overlap / len(query_words))
            )

            candidates.append({

                "score": float(score),

                "content": text,

                "metadata": meta
            })

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return candidates[:search_k]
# =====================================================
# GENERAL RETRIEVAL
# =====================================================
def retrieve(
    query,
    company=None,
    tender_type=None,
    top_k=TOP_K,
    search_k=SEARCH_K
):

    start_time = time.time()

    # Fallback to keyword search in Low-RAM Mode or if models failed to load
    if LOW_RAM_MODE or not embedding_model or not index:
        return retrieve_keyword_fallback(
            query=query,
            company=company,
            tender_type=tender_type,
            search_k=search_k,
            section_name=None
        )

    try:

        query_embedding = embedding_model.encode(
            [query],
            normalize_embeddings=True
        )

        query_embedding = np.array(
            query_embedding,
            dtype=np.float32
        )

        # Look up matching company key case-insensitively in company_index
        matched_company_key = None
        if company and company_index:
            company_lookup = {k.upper(): k for k in company_index.keys()}
            matched_company_key = company_lookup.get(company.upper())

        results = []

        if matched_company_key:
            # We have the exact list of chunk IDs for this company.
            # This avoids missing matches due to approximate IVF search cluster pruning.
            company_chunk_ids = company_index[matched_company_key]
            
            # Filter candidate chunk IDs by other metadata criteria (tender_type) first
            candidates = []
            for idx in company_chunk_ids:
                if idx < 0 or idx >= len(metadata):
                    continue
                meta = metadata[idx]
                
                if tender_type:
                    chunk_type = str(meta.get("tender_type", "")).strip().upper()
                    if tender_type.upper() not in chunk_type:
                        continue
                        
                candidates.append(idx)

            if candidates:
                if hasattr(index, "make_direct_map"):
                    index.make_direct_map()
                
                # Reconstruct vectors for candidates and compute exact cosine similarity
                candidate_vectors = np.vstack([index.reconstruct(int(idx)) for idx in candidates])
                scores = np.dot(candidate_vectors, query_embedding[0])
                
                for idx, score in zip(candidates, scores):
                    if score < MIN_SCORE:
                        continue
                    results.append({
                        "score": float(score),
                        "content": texts[idx],
                        "metadata": metadata[idx]
                    })
                
                # Sort by score descending
                results.sort(key=lambda x: x["score"], reverse=True)
        else:
            # Fallback/Global Search
            if hasattr(index, "nprobe"):
                # Increase nprobe to improve approximate search recall
                index.nprobe = min(64, getattr(index, "nlist", 64))

            search_k = min(
                3000,
                index.ntotal
            )

            scores, indices = index.search(
                query_embedding,
                search_k
            )

            for score, idx in zip(
                scores[0],
                indices[0]
            ):

                if idx < 0:
                    continue

                meta = metadata[idx]

                if company:

                    chunk_company = str(
                        meta.get(
                            "company_folder",
                            ""
                        )
                    ).strip().upper()

                    if chunk_company != company.upper():
                        continue

                if score < MIN_SCORE:
                    continue

                if tender_type:

                    chunk_type = str(
                        meta.get(
                            "tender_type",
                            ""
                        )
                    )

                    if (
                        tender_type.upper()
                        not in chunk_type.upper()
                    ):
                        continue

                results.append({
                    "score": float(score),
                    "content": texts[idx],
                    "metadata": meta
                })

    except Exception as e:

        print(
            f"Search failed: {e}"
        )

        results = []

    results = rerank_results(
        query,
        results,
        final_k=min(
            top_k,
            len(results)
        )
    )

    return results
# =====================================================
# SECTION RETRIEVAL
# =====================================================
def retrieve_by_section(
    query,
    section_name,
    company=None,
    tender_type=None,
    top_k=TOP_K,
    search_k=SEARCH_K
):

    start_time = time.time()

    # Fallback to keyword search in Low-RAM Mode or if models failed to load
    if LOW_RAM_MODE or not embedding_model or not index:
        return retrieve_keyword_fallback(
            query=query,
            company=company,
            tender_type=tender_type,
            search_k=search_k,
            section_name=section_name
        )

    try:

        query_embedding = embedding_model.encode(
            [query],
            normalize_embeddings=True
        )

        query_embedding = np.array(
            query_embedding,
            dtype=np.float32
        )

        # Look up matching company key case-insensitively in company_index
        matched_company_key = None
        if company and company_index:
            company_lookup = {k.upper(): k for k in company_index.keys()}
            matched_company_key = company_lookup.get(company.upper())

        results = []

        if matched_company_key:
            # We have the exact list of chunk IDs for this company.
            # This avoids missing matches due to approximate IVF search cluster pruning.
            company_chunk_ids = company_index[matched_company_key]
            
            # Filter candidate chunk IDs by other metadata criteria (tender_type, section_name) first
            candidates = []
            for idx in company_chunk_ids:
                if idx < 0 or idx >= len(metadata):
                    continue
                meta = metadata[idx]
                
                if tender_type:
                    chunk_type = str(meta.get("tender_type", "")).strip().upper()
                    if tender_type.upper() not in chunk_type:
                        continue
                        
                if section_name:
                    section = str(meta.get("section", "")).strip().upper()
                    db_section_name = normalize_section_name(section_name)
                    if db_section_name != section:
                        continue
                        
                candidates.append(idx)

            if candidates:
                if hasattr(index, "make_direct_map"):
                    index.make_direct_map()
                
                # Reconstruct vectors for candidates and compute exact cosine similarity
                candidate_vectors = np.vstack([index.reconstruct(int(idx)) for idx in candidates])
                scores = np.dot(candidate_vectors, query_embedding[0])
                
                for idx, score in zip(candidates, scores):
                    if score < MIN_SCORE:
                        continue
                    results.append({
                        "score": float(score),
                        "content": texts[idx],
                        "metadata": metadata[idx]
                    })
                
                # Sort by score descending
                results.sort(key=lambda x: x["score"], reverse=True)
        else:
            # Fallback/Global Search
            if hasattr(index, "nprobe"):
                # Increase nprobe to improve approximate search recall
                index.nprobe = min(64, getattr(index, "nlist", 64))

            search_k = min(
                5000,
                index.ntotal
            )

            scores, indices = index.search(
                query_embedding,
                search_k
            )

            for score, idx in zip(
                scores[0],
                indices[0]
            ):

                if idx < 0:
                    continue

                if idx >= len(metadata):
                    continue

                meta = metadata[idx]

                # =====================================
                # COMPANY FILTER
                # =====================================

                if company:

                    chunk_company = str(
                        meta.get(
                            "company_folder",
                            ""
                        )
                    ).strip().upper()

                    if chunk_company != company.upper():
                        continue

                # =====================================
                # SCORE FILTER
                # =====================================

                if score < MIN_SCORE:
                    continue

                # =====================================
                # TENDER TYPE FILTER
                # =====================================

                if tender_type:

                    chunk_type = str(
                        meta.get(
                            "tender_type",
                            ""
                        )
                    )

                    if (
                        tender_type.upper()
                        not in chunk_type.upper()
                    ):
                        continue

                # =====================================
                # SECTION FILTER
                # =====================================

                section = str(
                    meta.get(
                        "section",
                        ""
                    )
                ).upper()

                db_section_name = normalize_section_name(section_name)
                if db_section_name != section:
                    continue

                results.append({

                    "score": float(score),

                    "content": texts[idx],

                    "metadata": meta
                })

        print(
            f"\nSection Results Found: "
            f"{len(results)}"
        )

    except Exception as e:

        print(
            f"Section search failed: {e}"
        )

        results = []

    results = rerank_results(
        query,
        results,
        final_k=min(
            top_k,
            len(results)
        )
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
    company=None,
    tender_type=None,
    section_name=None,
    top_k=TOP_K
):

    if section_name:

        results = retrieve_by_section(
            query=query,
            company=company,
            tender_type=tender_type,
            section_name=section_name,
            top_k=top_k
        )

    else:

        results = retrieve(
            query=query,
            company=company,
            tender_type=tender_type,
            top_k=top_k
        )

    context_parts = []

    for item in results:

        meta = item.get(
            "metadata",
            {}
        )

        context_parts.append(

            f"COMPANY: "
            f"{meta.get('company_folder', '')}\n"

            f"ORGANIZATION: "
            f"{meta.get('organization', '')}\n"

            f"SOURCE: "
            f"{meta.get('source', '')}\n"

            f"TENDER TYPE: "
            f"{meta.get('tender_type', '')}\n"

            f"SECTION: "
            f"{meta.get('section', '')}\n"

            f"TENDER NUMBER: "
            f"{meta.get('tender_number', '')}\n"

            f"ESTIMATED VALUE: "
            f"{meta.get('estimated_value', '')}\n"

            f"EMD: "
            f"{meta.get('emd', '')}\n"

            f"TURNOVER: "
            f"{meta.get('turnover', '')}\n"

            f"EXPERIENCE: "
            f"{meta.get('experience', '')}\n"

            f"COMPLETION PERIOD: "
            f"{meta.get('completion_period', '')}\n"

            f"SIMILARITY SCORE: "
            f"{item.get('score', 0):.4f}\n\n"

            f"{item['content']}"
        )

    return "\n\n" + ("\n" + "=" * 100 + "\n\n").join(
        context_parts
    )
def build_tender_context(
    query,
    company,
    tender_type=None
):

    return {

        "eligibility": retrieve_by_section(
            query=query,
            section_name="ELIGIBILITY",
            company=company,
            tender_type=tender_type,
            top_k=15
        ),

        "technical": retrieve_by_section(
            query=query,
            section_name="TECHNICAL",
            company=company,
            tender_type=tender_type,
            top_k=20
        ),

        "commercial": retrieve_by_section(
            query=query,
            section_name="COMMERCIAL",
            company=company,
            tender_type=tender_type,
            top_k=15
        ),

        "boq": retrieve_by_section(
            query=query,
            section_name="BOQ",
            company=company,
            tender_type=tender_type,
            top_k=10
        ),

        "scc": retrieve_by_section(
            query=query,
            section_name="SCC",
            company=company,
            tender_type=tender_type,
            top_k=10
        ),

        "gcc": retrieve_by_section(
            query=query,
            section_name="GCC",
            company=company,
            tender_type=tender_type,
            top_k=15
        ),

        "nit": retrieve_by_section(
            query=query,
            section_name="NOTICE_INVITING_TENDER",
            company=company,
            tender_type=tender_type,
            top_k=10
        )
    }
# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":

    query = input(
        "\nEnter Tender Query: "
    ).strip()

    company = input(
        "\nCompany (SAIL/NTPC/BHEL etc, leave blank for all): "
    ).strip()

    section = input(
        "\nSection (leave blank for general search): "
    ).strip()

    company = (
        company
        if company
        else None
    )

    if section:

        results = retrieve_by_section(
            query=query,
            section_name=section,
            company=company
        )

    else:

        results = retrieve(
            query=query,
            company=company
        )

    print(
        f"\nRetrieved "
        f"{len(results)} chunks"
    )

    if len(results) == 0:

        print(
            "\nNo chunks passed "
            "the similarity threshold."
        )

    for i, item in enumerate(
        results,
        start=1
    ):

        print(
            "\n" + "=" * 80
        )

        meta = item.get(
            "metadata",
            {}
        )

        print(
            f"[{i}] "
            f"{meta.get('source')}"
        )

        print(
            f"Similarity Score: "
            f"{item['score']:.4f}"
        )

        if "rerank_score" in item:

            print(
                f"Rerank Score: "
                f"{item['rerank_score']:.4f}"
            )

        print(
            f"Company: "
            f"{meta.get('company_folder')}"
        )

        print(
            f"Organization: "
            f"{meta.get('organization')}"
        )

        print(
            f"Section: "
            f"{meta.get('section')}"
        )

        print(
            f"Estimated Value: "
            f"{meta.get('estimated_value')}"
        )

        print(
            f"Chunk ID: "
            f"{meta.get('chunk_id')}"
        )

        print(
            item["content"][:700]
        )