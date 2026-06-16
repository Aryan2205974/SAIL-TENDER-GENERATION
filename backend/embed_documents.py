import os
import json
import pickle
import logging
import time
import faiss
import numpy as np

from tqdm import tqdm
from sentence_transformers import SentenceTransformer

# =====================================================
# PATHS
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

CHUNKS_FILE = os.path.join(
    BASE_DIR,
    "chunks",
    "chunks.json"
)

VECTOR_DB_DIR = os.path.join(
    BASE_DIR,
    "vectordb"
)

os.makedirs(
    VECTOR_DB_DIR,
    exist_ok=True
)

INDEX_FILE = os.path.join(
    VECTOR_DB_DIR,
    "faiss.index"
)

METADATA_FILE = os.path.join(
    VECTOR_DB_DIR,
    "metadata.pkl"
)
METADATA_JSON = os.path.join(
    VECTOR_DB_DIR,
    "metadata.json"
)

INTELLIGENCE_FILE = os.path.join(
    VECTOR_DB_DIR,
    "tender_intelligence.json"
)
SIMILAR_FILE = os.path.join(
    VECTOR_DB_DIR,
    "similar_tenders.json"
)
COMPANY_RETRIEVAL_FILE = os.path.join(
    VECTOR_DB_DIR,
    "company_retrieval_index.json"
)

# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =====================================================
# CONFIG
# =====================================================

MODEL_NAME = "BAAI/bge-base-en-v1.5"
BATCH_SIZE = 64

# =====================================================
# SECTION PRIORITY CONFIG
# =====================================================

SECTION_PRIORITY = {
    "ELIGIBILITY": 10,
    "TECHNICAL": 9,
    "COMMERCIAL": 8,
    "BOQ": 7,
    "SCC": 6,
    "GCC": 5,
    "EVALUATION": 5,
    "NOTICE_INVITING_TENDER": 4,
    "ANNEXURE": 3,
    "GENERAL": 1
}

# =====================================================
# ESTIMATED VALUE ENGINE
# =====================================================

def derive_estimated_value(meta):
    emd = meta.get("emd")
    if emd:
        try:
            emd = float(str(emd).replace(",", ""))
            return int(emd * 75)
        except:
            pass

    turnover = meta.get("turnover")
    if turnover:
        try:
            turnover = float(str(turnover).replace(",", ""))
            return int(turnover * 10000000)
        except:
            pass

    return None


# =====================================================
# MAIN EMBED FUNCTION (callable from API)
# =====================================================

def embed_all() -> int:
    """
    Load chunks.json, generate FAISS embeddings, extract numerical intelligence
    (EMD, turnover, experience, completion period, estimated value), and save all
    indexes. Returns the number of vectors indexed.
    """
    overall_start = time.time()
    LOW_RAM_MODE = (
        os.getenv("LOW_RAM_MODE", "false").lower() == "true"
        or os.getenv("RENDER", "false").lower() == "true"
    )

    model = None
    if not LOW_RAM_MODE:
        print("\nLoading Embedding Model...")
        model = SentenceTransformer(MODEL_NAME)
        print("Model Loaded Successfully")
    else:
        print("INFO: LOW_RAM_MODE is active. Skipping SentenceTransformer loading.")

    # Load chunks
    if not os.path.exists(CHUNKS_FILE):
        print(f"[embed_all] No chunks file found at {CHUNKS_FILE}. Run chunking first.")
        return 0

    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"\nLoaded {len(chunks):,} chunks")

    if not chunks:
        print("[embed_all] No chunks to embed.")
        return 0

    texts = []
    metadata = []
    tender_intelligence = []
    section_counter = {}
    similar_tenders = {}
    company_retrieval_index = {}
    company_index = {}

    for chunk in chunks:
        meta = chunk["metadata"]
        section = meta.get("section", "GENERAL")
        section_counter[section] = section_counter.get(section, 0) + 1

        estimated_value = derive_estimated_value(meta)
        meta["estimated_value"] = estimated_value
        meta["section_priority"] = SECTION_PRIORITY.get(section, 1)
        meta["has_emd"] = bool(meta.get("emd"))
        meta["has_turnover"] = bool(meta.get("turnover"))
        meta["has_experience"] = bool(meta.get("experience"))
        meta["has_completion_period"] = bool(meta.get("completion_period"))
        meta["content_preview"] = chunk["content"][:500]

        metadata.append(meta)

        company_name = meta.get("company_folder", "UNKNOWN")
        if company_name not in company_index:
            company_index[company_name] = []
        company_index[company_name].append(len(metadata) - 1)

        tender_intelligence.append({
            "company_folder": meta.get("company_folder"),
            "source": meta.get("source"),
            "organization": meta.get("organization"),
            "tender_type": meta.get("tender_type"),
            "section": meta.get("section"),
            "estimated_value": estimated_value,
            "emd": meta.get("emd"),
            "turnover": meta.get("turnover"),
            "experience": meta.get("experience"),
            "completion_period": meta.get("completion_period")
        })

        enriched_text = f"""
COMPANY:
{meta.get('company_folder','')}   

ORGANIZATION:
{meta.get('organization','')}

SOURCE:
{meta.get('source','')}

TENDER TYPE:
{meta.get('tender_type','')}

SECTION:
{meta.get('section','')}

TENDER NUMBER:
{meta.get('tender_number','')}

EMD:
{meta.get('emd','')}

TURNOVER:
{meta.get('turnover','')}

EXPERIENCE:
{meta.get('experience','')}

COMPLETION PERIOD:
{meta.get('completion_period','')}

ESTIMATED VALUE:
{estimated_value}

SECTION PRIORITY:
{meta.get('section_priority')}

KEYWORDS:
{' '.join(meta.get('keywords', []))}

CONTENT:
{chunk['content']}
"""
        texts.append(enriched_text)

    print(f"\nPrepared {len(texts):,} embedding documents")
    print("\nSection Distribution:")
    for section, count in sorted(section_counter.items(), key=lambda x: x[1], reverse=True):
        print(f"{section:<30} {count:,}")

    # Generate embeddings if not in LOW_RAM_MODE
    if not LOW_RAM_MODE and model:
        all_embeddings = []
        embedding_start = time.time()
        print("\nGenerating Embeddings...\n")

        for i in tqdm(range(0, len(texts), BATCH_SIZE)):
            batch = texts[i:i + BATCH_SIZE]
            embeddings = model.encode(
                batch,
                batch_size=BATCH_SIZE,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True
            )
            all_embeddings.extend(embeddings)
            print(f"Processed {min(i+BATCH_SIZE,len(texts)):,}/{len(texts):,}")

        embeddings_array = np.array(all_embeddings, dtype=np.float32)
        print(f"\nEmbedding Time: {time.time()-embedding_start:.2f}s")
        print(f"\nEmbedding Shape: {embeddings_array.shape}")

        # Normalize and build FAISS index
        faiss.normalize_L2(embeddings_array)
        dimension = embeddings_array.shape[1]
        print(f"Vector Dimension: {dimension}")

        if len(embeddings_array) > 5000:
            nlist = min(1024, max(50, len(embeddings_array) // 40))
            print(f"\nCreating IVF Index")
            print(f"Clusters: {nlist}")
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_INNER_PRODUCT)
            print("\nTraining Index...")
            index.train(embeddings_array)
        else:
            print("\nCreating Flat Index")
            index = faiss.IndexFlatIP(dimension)

        index.add(embeddings_array)
        print(f"\nIndexed {index.ntotal:,} vectors")

        # Save FAISS index
        faiss.write_index(index, INDEX_FILE)
    else:
        print("\nINFO: LOW_RAM_MODE is active. Skipping embedding generation and FAISS indexing.")

    # Save metadata PKL
    with open(METADATA_FILE, "wb") as f:
        pickle.dump({"texts": texts, "metadata": metadata}, f)

    # Save metadata JSON
    with open(METADATA_JSON, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # Save tender intelligence
    with open(INTELLIGENCE_FILE, "w", encoding="utf-8") as f:
        json.dump(tender_intelligence, f, indent=2, ensure_ascii=False)

    # Build and save similar tenders
    for meta in metadata:
        tender_type = meta.get("tender_type", "GENERAL")
        source = meta.get("source", "UNKNOWN")
        company = meta.get("company_folder", "UNKNOWN")

        similar_tenders.setdefault(tender_type, [])
        company_retrieval_index.setdefault(company, [])

        source = meta.get("source")
        if source not in company_retrieval_index[company]:
            company_retrieval_index[company].append(source)
        if source not in similar_tenders[tender_type]:
            similar_tenders[tender_type].append(source)

    with open(SIMILAR_FILE, "w", encoding="utf-8") as f:
        json.dump(similar_tenders, f, indent=2, ensure_ascii=False)
    print(f"Similar Tenders Saved : {SIMILAR_FILE}")

    with open(COMPANY_RETRIEVAL_FILE, "w", encoding="utf-8") as f:
        json.dump(company_retrieval_index, f, indent=2, ensure_ascii=False)
    print(f"Company Retrieval Index Saved : {COMPANY_RETRIEVAL_FILE}")

    COMPANY_INDEX_FILE = os.path.join(VECTOR_DB_DIR, "company_index.json")
    with open(COMPANY_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(company_index, f, indent=2)
    print(f"Company Index Saved : {COMPANY_INDEX_FILE}")

    print("\n" + "=" * 80)
    print(f"Total Chunks           : {len(texts):,}")
    print(f"Metadata Records       : {len(metadata):,}")
    print(f"Embedding Model        : {MODEL_NAME}")
    print(f"FAISS Vectors          : {index.ntotal if index else 0}")
    print(f"Index Saved            : {INDEX_FILE}")
    print(f"Metadata PKL Saved     : {METADATA_FILE}")
    print(f"Metadata JSON Saved    : {METADATA_JSON}")
    print(f"Tender Intelligence    : {INTELLIGENCE_FILE}")
    print(f"Total Runtime         : {time.time()-overall_start:.2f}s")
    print("=" * 80)

    return index.ntotal if index else len(texts)


if __name__ == "__main__":
    embed_all()