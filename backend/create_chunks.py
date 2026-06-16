"""
Production-ready Tender RAG Chunking Pipeline
Features:
- Recursive PDF discovery
- OCR fallback
- Section-aware chunking
- Tender intelligence extraction
- Clause extraction
- Table detection
- Keyword extraction
- Cross-tender metadata
- Outputs:
    chunks.json
    clauses.json
    tender_metadata.json
"""
import time
import os
import re
import json
import fitz
from datetime import datetime
from collections import Counter

from ocr_utils import ocr_page
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_FOLDER = os.path.join(BASE_DIR, "data")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "chunks")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

CHUNKS_FILE = os.path.join(OUTPUT_FOLDER, "chunks.json")
CLAUSES_FILE = os.path.join(OUTPUT_FOLDER, "clauses.json")
META_FILE = os.path.join(OUTPUT_FOLDER, "tender_metadata.json")
ORG_MAP_FILE = os.path.join(
    OUTPUT_FOLDER,
    "organization_map.json"
)

COMPANY_INDEX_FILE = os.path.join(
    OUTPUT_FOLDER,
    "company_index.json"
)

CHUNK_SIZE = 1800
CHUNK_OVERLAP = 300
MIN_CHUNK_LENGTH = 100

SECTION_PATTERNS = {
    "NOTICE_INVITING_TENDER":[r"NOTICE INVITING TENDER",r"\bNIT\b"],
    "SCOPE_OF_WORK":[r"SCOPE OF WORK",r"WORK DESCRIPTION"],
    "ELIGIBILITY":[r"ELIGIBILITY CRITERIA",r"PRE[- ]?QUALIFICATION",r"PQ CRITERIA"],
    "TECHNICAL":[r"TECHNICAL SPECIFICATION",r"TECHNICAL REQUIREMENTS"],
    "COMMERCIAL":[r"COMMERCIAL TERMS",r"PAYMENT TERMS"],
    "BID_SUBMISSION":[r"BID SUBMISSION",r"INSTRUCTIONS TO BIDDERS"],
    "EVALUATION":[r"EVALUATION CRITERIA"],
    "GCC":[r"GENERAL CONDITIONS OF CONTRACT",r"\bGCC\b"],
    "SCC":[r"SPECIAL CONDITIONS OF CONTRACT",r"\bSCC\b"],
    "SAFETY":[r"SAFETY REQUIREMENTS"],
    "QUALITY":[r"QUALITY ASSURANCE"],
    "DELIVERY":[r"DELIVERY SCHEDULE"],
    "PENALTY":[r"LIQUIDATED DAMAGES",r"PENALTY CLAUSE"],
    "BOQ":[r"BOQ",r"BILL OF QUANTITY"],
    "ANNEXURE":[r"ANNEXURE",r"ANNEX"]
}

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n","\n",". "," ",""]
)

def clean_text(text):
    text = text.replace("\x00"," ")
    text = re.sub(r"\s+"," ",text)
    return text.strip()

def detect_section(text):
    txt = text.upper()
    for sec, patterns in SECTION_PATTERNS.items():
        for p in patterns:
            if re.search(p, txt):
                return sec
    return "GENERAL"

def detect_tender_type(text):

    text = text.lower()

    categories = {

        "REFRACTORY": [
            "refractory",
            "ladle",
            "tundish",
            "castable",
            "alumina",
            "magnesia",
            "spinel",
            "brick",
            "bricks",
            "ramming mass",
            "slide gate",
            "purging plug"
        ],

        "IT": [
            "sap",
            "vpn",
            "consultant",
            "software",
            "server",
            "database",
            "application",
            "business solution",
            "support maintenance",
            "implementation",
            "helpdesk"
        ],

        "ELECTRICAL": [
            "electrical",
            "transformer",
            "switchgear",
            "cable",
            "motor",
            "substation",
            "relay",
            "lt panel",
            "ht panel"
        ],

        "MECHANICAL": [
            "pump",
            "compressor",
            "bearing",
            "gearbox",
            "conveyor",
            "blower",
            "valve",
            "mechanical"
        ],

        "CIVIL": [
            "civil",
            "concrete",
            "road",
            "drain",
            "building",
            "foundation",
            "structural"
        ]
    }

    scores = {}

    for category, keywords in categories.items():

        score = 0

        for keyword in keywords:

            score += text.count(keyword)

        scores[category] = score

    best_type = max(
        scores,
        key=scores.get
    )

    if scores[best_type] == 0:
        return "GENERAL"

    return best_type

def detect_organization(text, folder):
    known = ["SAIL","NTPC","ONGC","IOCL","ECIL","NMDC","INDIA POST","BANK OF BARODA"]
    txt = text.upper()
    for k in known:
        if k in txt:
            return k
    return folder

def extract_tender_number(text):
    patterns = [
        r"TENDER\s*NO\.?\s*[:\-]?\s*([A-Z0-9/_\-]+)",
        r"NIT\s*NO\.?\s*[:\-]?\s*([A-Z0-9/_\-]+)",
        r"BID\s*NO\.?\s*[:\-]?\s*([A-Z0-9/_\-]+)"
    ]
    for p in patterns:
        m = re.search(p,text,re.I)
        if m:
            return m.group(1)
    return ""

def extract_emd(text):
    pats=[r"EMD.*?Rs\.?\s*([\d,]+)",r"EARNEST MONEY.*?([\d,]+)"]
    for p in pats:
        m=re.search(p,text,re.I|re.S)
        if m:return m.group(1)
    return ""

def extract_turnover(text):
    m=re.search(r"TURNOVER.*?([\d,.]+)\s*(CR|CRORE)",text,re.I|re.S)
    return m.group(1) if m else ""

def extract_experience(text):
    m=re.search(r"(\d+)\s+YEARS?.*?EXPERIENCE",text,re.I|re.S)
    return m.group(1) if m else ""

def extract_completion_period(text):
    m=re.search(r"(\d+)\s+DAYS",text,re.I)
    return m.group(1) if m else ""

def extract_keywords(text):
    words=re.findall(r"\b[A-Z]{3,}\b",text.upper())
    return list(dict.fromkeys(words))[:50]

def detect_table(text):
    score=0
    if "|" in text: score+=1
    if len(re.findall(r"\s{3,}",text))>5: score+=1
    if len(re.findall(r"\d+\.\d+",text))>5: score+=1
    return score>=2

def extract_clauses(text):
    return re.findall(r"(\d+\.\d+.*?)(?=\d+\.\d+|\Z)",text,re.S)

def extract_pdf_text(pdf_path):

    start_pdf = time.time()

    doc = fitz.open(pdf_path)

    total_pages = len(doc)

    print(f"\n📄 Pages Found: {total_pages}")

    full = ""

    ocr_count = 0

    for i in range(total_pages):

        page_start = time.time()

        print(
            f"   Page {i+1}/{total_pages}",
            end=""
        )

        page = doc.load_page(i)

        txt = page.get_text("text")

        if len(txt.strip()) < 100:

            print(" | OCR", end="")

            ocr_start = time.time()

            txt = ocr_page(page)

            ocr_count += 1

            print(
                f" | OCR Time: {time.time()-ocr_start:.2f}s",
                end=""
            )

        full += f"\nPAGE_NUMBER:{i+1}\n{txt}\n"

        print(
            f" | Page Time: {time.time()-page_start:.2f}s"
        )

    doc.close()

    print(
        f"\n✅ PDF Extraction Complete"
    )

    print(
        f"   OCR Pages Used : {ocr_count}"
    )

    print(
        f"   Total Time     : {time.time()-start_pdf:.2f}s\n"
    )

    return clean_text(full)

def process():
    chunks = []
    clauses = []
    metadata = []
    organization_map = {}
    company_index = {}

    for root,_,files in os.walk(PDF_FOLDER):
        for file in files:
            if not file.lower().endswith(".pdf"):
                continue

            path=os.path.join(root,file)
            rel=os.path.relpath(path,PDF_FOLDER).replace("\\","/")
            folder=os.path.dirname(rel)

            print(f"Processing {rel}")

            try:
                text=extract_pdf_text(path)

                organization=detect_organization(text, folder.split("/")[0] if folder else "UNKNOWN")
                tender_no=extract_tender_number(text)
                tender_type=detect_tender_type(text)

                emd=extract_emd(text)
                turnover=extract_turnover(text)
                experience=extract_experience(text)
                completion=extract_completion_period(text)

                metadata.append({
                    "source":file,
                    "organization":organization,
                    "tender_number":tender_no,
                    "tender_type":tender_type,
                    "emd":emd,
                    "turnover":turnover,
                    "experience":experience,
                    "completion_period":completion
                })

                doc_clauses=extract_clauses(text)

                for cidx, clause in enumerate(doc_clauses):
                    clauses.append({
                        "source":file,
                        "clause_id":cidx,
                        "content":clause[:10000]
                    })

                split_chunks=splitter.split_text(text)

                for idx, chunk in enumerate(split_chunks):

                    chunk = clean_text(chunk)

                    if len(chunk) < MIN_CHUNK_LENGTH:
                        continue

                    chunk_record = {

                        "content": chunk,

                        "metadata": {

                            "source": file,

                            "relative_path": rel,

                            "folder": folder,

                            "company_folder": (
                                folder.split("/")[0]
                                if folder
                                else "UNKNOWN"
                            ),

                            "organization": organization,

                            "tender_number": tender_no,

                            "tender_type": tender_type,

                            "section": detect_section(chunk),

                            "emd": emd,

                            "turnover": turnover,

                            "experience": experience,

                            "completion_period": completion,

                            "keywords": extract_keywords(chunk),

                            "is_table": detect_table(chunk),

                            "chunk_id": idx,

                            "length": len(chunk),

                            "created_at":
                                datetime.now().isoformat()
                        }
                    }

                    # ---------------------------------
                    # SAVE CHUNK
                    # ---------------------------------

                    chunks.append(
                        chunk_record
                    )

                    global_chunk_id = (
                        len(chunks) - 1
                    )

                    # ---------------------------------
                    # ORGANIZATION MAP
                    # ---------------------------------

                    organization_map.setdefault(

                        organization,

                        {
                            "chunk_ids": [],
                            "files": []
                        }
                    )

                    organization_map[
                        organization
                    ]["chunk_ids"].append(
                        global_chunk_id
                    )

                    if file not in organization_map[
                        organization
                    ]["files"]:

                        organization_map[
                            organization
                        ]["files"].append(
                            file
                        )

                    # ---------------------------------
                    # COMPANY INDEX
                    # ---------------------------------

                    company_index.setdefault(

                        organization,

                        {
                            "chunk_ids": [],
                            "tenders": {}
                        }
                    )

                    company_index[
                        organization
                    ]["chunk_ids"].append(
                        global_chunk_id
                    )

                    company_index[
                        organization
                    ]["tenders"].setdefault(

                        file,

                        []
                    )

                    company_index[
                        organization
                    ]["tenders"][
                        file
                    ].append(
                        global_chunk_id
                    )

            except Exception as e:
                print(f"Error: {rel} -> {e}")

    with open(CHUNKS_FILE,"w",encoding="utf-8") as f:
        json.dump(chunks,f,ensure_ascii=False,indent=2)

    with open(CLAUSES_FILE,"w",encoding="utf-8") as f:
        json.dump(clauses,f,ensure_ascii=False,indent=2)

    with open(META_FILE,"w",encoding="utf-8") as f:
        json.dump(metadata,f,ensure_ascii=False,indent=2)
    with open(

    ORG_MAP_FILE,

    "w",

    encoding="utf-8"

    ) as f:

        json.dump(

        organization_map,

        f,

        ensure_ascii=False,

        indent=2
    ) 
    with open(

    COMPANY_INDEX_FILE,

    "w",

    encoding="utf-8"

    ) as f:

        json.dump(

        company_index,

        f,

        ensure_ascii=False,

        indent=2
    )   

    print(
        f"\nChunks: {len(chunks):,}"
    )

    print(
        f"Clauses: {len(clauses):,}"
    )

    print(
        f"Organizations: "
        f"{len(organization_map):,}"
    )

    print(
        f"Organization Map: "
        f"{ORG_MAP_FILE}"
    )

    print(
        f"Company Index: "
        f"{COMPANY_INDEX_FILE}"
    )

if __name__ == "__main__":
    process()
