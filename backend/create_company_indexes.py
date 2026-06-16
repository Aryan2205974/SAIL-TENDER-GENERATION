import os
import json
import pickle
import numpy as np
import faiss

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
print(BASE_DIR)
print(VECTOR_DB_DIR)

VECTOR_DB_DIR = os.path.join(
    BASE_DIR,
    "vectordb"
)

FAISS_INDEX_FILE = os.path.join(
    VECTOR_DB_DIR,
    "faiss.index"
)

METADATA_FILE = os.path.join(
    VECTOR_DB_DIR,
    "metadata.pkl"
)

COMPANY_INDEX_FILE = os.path.join(
    VECTOR_DB_DIR,
    "company_index.json"
)

# =====================================================
# LOAD DATA
# =====================================================

print("\nLoading metadata...")

with open(
    METADATA_FILE,
    "rb"
) as f:

    data = pickle.load(f)

texts = data["texts"]
metadata = data["metadata"]

print(
    f"Loaded {len(metadata):,} chunks"
)

print("\nLoading company index...")

with open(
    COMPANY_INDEX_FILE,
    "r",
    encoding="utf-8"
) as f:

    company_index = json.load(f)

print(
    f"Loaded {len(company_index)} companies"
)

print("\nLoading FAISS index...")

global_index = faiss.read_index(
    FAISS_INDEX_FILE
)

print(
    f"Global FAISS size: "
    f"{global_index.ntotal:,}"
)

# =====================================================
# CREATE COMPANY INDEXES
# =====================================================

created = 0

for company, chunk_ids in company_index.items():

    try:

        print(
            f"\n{'=' * 80}"
        )

        print(
            f"Processing: {company}"
        )

        if len(chunk_ids) == 0:

            print(
                "No chunks found."
            )

            continue

        company_vectors = []
        company_texts = []
        company_metadata = []

        for idx in chunk_ids:

            idx = int(idx)

            if idx >= global_index.ntotal:
                continue

            vector = global_index.reconstruct(
                idx
            )

            company_vectors.append(
                vector
            )

            company_texts.append(
                texts[idx]
            )

            company_metadata.append(
                metadata[idx]
            )

        if len(company_vectors) == 0:

            print(
                "No valid vectors found."
            )

            continue

        company_vectors = np.array(
            company_vectors,
            dtype=np.float32
        )

        dimension = (
            company_vectors.shape[1]
        )

        company_faiss = faiss.IndexFlatIP(
            dimension
        )

        company_faiss.add(
            company_vectors
        )

        # =================================
        # SAVE FAISS
        # =================================

        company_faiss_file = os.path.join(
            VECTOR_DB_DIR,
            f"faiss_{company.lower()}.index"
        )

        faiss.write_index(
            company_faiss,
            company_faiss_file
        )

        # =================================
        # SAVE METADATA
        # =================================

        company_metadata_file = os.path.join(
            VECTOR_DB_DIR,
            f"metadata_{company.lower()}.pkl"
        )

        with open(
            company_metadata_file,
            "wb"
        ) as f:

            pickle.dump(
                {
                    "texts": company_texts,
                    "metadata": company_metadata
                },
                f
            )

        print(
            f"Created:"
        )

        print(
            f"  faiss_{company.lower()}.index"
        )

        print(
            f"  metadata_{company.lower()}.pkl"
        )

        print(
            f"  Chunks: "
            f"{len(company_texts):,}"
        )

        created += 1

    except Exception as e:

        print(
            f"Failed for "
            f"{company}: {e}"
        )

# =====================================================
# DONE
# =====================================================

print(
    f"\n{'=' * 80}"
)

print(
    f"Successfully created "
    f"{created} company indexes"
)

print(
    "\nFinished."
)
