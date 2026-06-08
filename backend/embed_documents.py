import os
import json
import pickle
import logging

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
BATCH_SIZE = 128

# =====================================================
# LOAD MODEL
# =====================================================

print("\nLoading Embedding Model...")

model = SentenceTransformer(
    MODEL_NAME
)

print("Model Loaded Successfully")

# =====================================================
# LOAD CHUNKS
# =====================================================

with open(
    CHUNKS_FILE,
    "r",
    encoding="utf-8"
) as f:

    chunks = json.load(f)

print(
    f"\nLoaded {len(chunks):,} chunks"
)

texts = [
    chunk["content"]
    for chunk in chunks
]

metadata = [
    chunk["metadata"]
    for chunk in chunks
]

# =====================================================
# GENERATE EMBEDDINGS
# =====================================================

all_embeddings = []

print("\nGenerating Embeddings...\n")

for i in tqdm(
    range(
        0,
        len(texts),
        BATCH_SIZE
    )
):

    batch = texts[
        i:i + BATCH_SIZE
    ]

    embeddings = model.encode(
        batch,
        batch_size=BATCH_SIZE,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    all_embeddings.extend(
        embeddings
    )

    print(
        f"Processed {min(i + BATCH_SIZE, len(texts))}/{len(texts)} chunks"
    )

# =====================================================
# CONVERT TO NUMPY
# =====================================================

embeddings_array = np.array(
    all_embeddings,
    dtype=np.float32
)

print(
    f"\nEmbeddings Shape: {embeddings_array.shape}"
)

# =====================================================
# CREATE FAISS INDEX
# =====================================================

dimension = embeddings_array.shape[1]

print(
    f"Vector Dimension: {dimension}"
)

faiss.normalize_L2(
    embeddings_array
)

index = faiss.IndexFlatIP(
    dimension
)

index.add(
    embeddings_array
)

print(
    f"Vectors Indexed: {index.ntotal:,}"
)

# =====================================================
# SAVE INDEX
# =====================================================

faiss.write_index(
    index,
    INDEX_FILE
)

with open(
    METADATA_FILE,
    "wb"
) as f:

    pickle.dump(
        {
            "texts": texts,
            "metadata": metadata
        },
        f
    )

# =====================================================
# SUMMARY
# =====================================================

print("\n" + "=" * 60)

print(
    f"Total Chunks      : {len(texts):,}"
)

print(
    f"Embedding Model   : {MODEL_NAME}"
)

print(
    f"FAISS Vectors     : {index.ntotal:,}"
)

print(
    f"Index Saved       : {INDEX_FILE}"
)

print(
    f"Metadata Saved    : {METADATA_FILE}"
)

print("=" * 60)