import os
import re
import json
import fitz

from ocr_utils import ocr_page

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

# =====================================================
# PATHS
# =====================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PDF_FOLDER = os.path.join(
    BASE_DIR,
    "data"
)

OUTPUT_FOLDER = os.path.join(
    BASE_DIR,
    "chunks"
)

os.makedirs(
    OUTPUT_FOLDER,
    exist_ok=True
)

OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "chunks.json"
)

# =====================================================
# CONFIG
# =====================================================

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

# =====================================================
# SECTION PATTERNS
# =====================================================

SECTION_PATTERNS = [

    r"NOTICE INVITING TENDER",
    r"\bNIT\b",

    r"SCOPE OF WORK",

    r"ELIGIBILITY CRITERIA",
    r"ELIGIBILITY",

    r"PRE[- ]?QUALIFICATION",
    r"PRE[- ]?QUALIFICATION CRITERIA",
    r"PRE[- ]?QUALIFICATION REQUIREMENT",

    r"QUALIFYING REQUIREMENT",
    r"QUALIFYING REQUIREMENTS",

    r"PQ CRITERIA",

    r"BIDDER ELIGIBILITY",

    r"TECHNO COMMERCIAL ELIGIBILITY",

    r"TECHNICAL SPECIFICATION",
    r"TECHNICAL REQUIREMENTS",

    r"COMMERCIAL TERMS",

    r"PAYMENT TERMS",

    r"BID SUBMISSION",

    r"INSTRUCTIONS TO BIDDERS",

    r"EVALUATION CRITERIA",

    r"GENERAL CONDITIONS OF CONTRACT",
    r"\bGCC\b",

    r"SPECIAL CONDITIONS OF CONTRACT",
    r"\bSCC\b",

    r"SAFETY REQUIREMENTS",

    r"QUALITY ASSURANCE",

    r"DELIVERY SCHEDULE",

    r"LIQUIDATED DAMAGES",

    r"PENALTY CLAUSE",

    r"PRICE BID",

    r"BOQ",
    r"BILL OF QUANTITY",

    r"ANNEXURE",
    r"ANNEX",

    r"FORMS"
]

# =====================================================
# CLEAN TEXT
# =====================================================

def clean_text(text):

    text = text.replace(
        "\x00",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()

# =====================================================
# NOISE CHECK
# =====================================================

def is_noisy(text):

    special_chars = len(
        re.findall(
            r'[^A-Za-z0-9\s.,()\-:/%]',
            text
        )
    )

    ratio = special_chars / max(
        len(text),
        1
    )

    return ratio > 0.25

# =====================================================
# SECTION DETECTION
# =====================================================

def detect_section(text):

    text_upper = text.upper()

    for pattern in SECTION_PATTERNS:

        if re.search(
            pattern,
            text_upper
        ):
            return pattern

    return "GENERAL"

# =====================================================
# TENDER TYPE DETECTION
# =====================================================

def detect_tender_type(text):

    text = text.upper()

    if any(
        keyword in text
        for keyword in [
            "REFRACTORY",
            "BRICK",
            "ALUMINA",
            "MAGNESIA",
            "LADLE",
            "SMS"
        ]
    ):
        return "REFRACTORY"

    elif any(
        keyword in text
        for keyword in [
            "TRANSFORMER",
            "MOTOR",
            "CABLE",
            "SWITCHGEAR"
        ]
    ):
        return "ELECTRICAL"

    elif any(
        keyword in text
        for keyword in [
            "AMC",
            "REPAIR",
            "MAINTENANCE",
            "OVERHAULING"
        ]
    ):
        return "MAINTENANCE"

    elif any(
        keyword in text
        for keyword in [
            "CIVIL",
            "BUILDING",
            "ROAD",
            "STRUCTURE"
        ]
    ):
        return "CIVIL"

    return "GENERAL"

# =====================================================
# PDF EXTRACTION
# =====================================================

def extract_pdf_text(pdf_path):

    document = fitz.open(pdf_path)

    full_text = ""

    ocr_pages = 0

    for page_num in range(len(document)):

        page = document.load_page(page_num)

        page_text = page.get_text("text")

        if len(page_text.strip()) < 100:

            print(
                f"   OCR Page {page_num + 1}"
            )

            page_text = ocr_page(page)

            ocr_pages += 1

        full_text += (
            f"\n\nPAGE_NUMBER:{page_num+1}\n\n"
        )

        full_text += page_text

    document.close()

    print(
        f"   OCR Pages Used: {ocr_pages}"
    )

    return clean_text(full_text)

# =====================================================
# TEXT SPLITTER
# =====================================================

splitter = RecursiveCharacterTextSplitter(

    chunk_size=CHUNK_SIZE,

    chunk_overlap=CHUNK_OVERLAP,

    separators=[
        "\n\n",
        "\n",
        ". ",
        " ",
        ""
    ]
)

# =====================================================
# CHUNK CLEANING
# =====================================================

def clean_chunk(chunk):

    chunk = re.sub(
        r"PAGE_NUMBER:\d+",
        " ",
        chunk
    )

    chunk = re.sub(
        r"Page\s+\d+\s+of\s+\d+",
        " ",
        chunk,
        flags=re.IGNORECASE
    )

    chunk = re.sub(
        r"\bPage\s+\d+\b",
        " ",
        chunk,
        flags=re.IGNORECASE
    )

    chunk = re.sub(
        r"\S+@\S+",
        " ",
        chunk
    )

    chunk = re.sub(
        r"\+?\d[\d\-\s]{8,}",
        " ",
        chunk
    )

    chunk = re.sub(
        r"\s+",
        " ",
        chunk
    )

    return chunk.strip()

# =====================================================
# PROCESS ALL PDFs
# =====================================================

def process_all_pdfs():

    pdf_files = sorted([
        f
        for f in os.listdir(
            PDF_FOLDER
        )
        if f.lower().endswith(".pdf")
    ])

    if not pdf_files:

        print(
            f"\n❌ No PDFs found in:\n{PDF_FOLDER}"
        )

        return

    print(
        f"\n📄 Found {len(pdf_files)} PDFs\n"
    )

    all_chunks = []

    for pdf_file in pdf_files:

        try:

            pdf_path = os.path.join(
                PDF_FOLDER,
                pdf_file
            )

            print(
                f"🔄 Processing: {pdf_file}"
            )

            document_text = extract_pdf_text(
                pdf_path
            )

            document_section = detect_section(
                document_text
            )

            tender_type = detect_tender_type(
                document_text
            )

            chunks = splitter.split_text(
                document_text
            )

            print(
                f"   Text Length : {len(document_text):,}"
            )

            print(
                f"   Chunks      : {len(chunks)}"
            )

            for idx, chunk in enumerate(chunks):

                page_match = re.search(
                    r"PAGE_NUMBER:(\d+)",
                    chunk
                )

                page_no = (
                    int(page_match.group(1))
                    if page_match
                    else 0
                )

                chunk = clean_chunk(chunk)

                if len(chunk) < 100:
                    continue

                if is_noisy(chunk):
                    continue

                section = detect_section(chunk)

                if section == "GENERAL":
                    section = document_section

                all_chunks.append({

                    "content": chunk,

                    "metadata": {

                        "source": pdf_file,

                        "section": section,

                        "tender_type": tender_type,

                        "page": page_no,

                        "chunk_id": idx,

                        "length": len(chunk)

                    }
                })

        except Exception as e:

            print(
                f"\n❌ Error in {pdf_file}"
            )

            print(str(e))

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_chunks,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        "\n" + "=" * 60
    )

    print(
        f"✅ Total Chunks : {len(all_chunks):,}"
    )

    print(
        f"✅ Saved To     : {OUTPUT_FILE}"
    )

    print(
        "=" * 60
    )

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    print(
        f"\nPDF Folder: {PDF_FOLDER}\n"
    )

    process_all_pdfs()