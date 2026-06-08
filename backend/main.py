from fastapi import FastAPI
from fastapi.responses import FileResponse
import uuid
import os

from planner import create_tender_plan, save_plan
from generate_subsection import generate_from_plan
from merge_to_pdf import merge_markdown, markdown_to_pdf

app = FastAPI(title="SAIL AI Tender Generator (Legacy Backend)", version="1.0.0")

PLAN_FILE = "tender_plan.json"

@app.post("/generate")
def generate_tender(data: dict):

    requirement = data.get("requirement", "")
    run_id = str(uuid.uuid4())[:8]

    # Step 1: Create structured tender plan and save to JSON
    plan = create_tender_plan(requirement)
    save_plan(plan, output_file=PLAN_FILE)

    # Step 2: Generate all subsections reading from the saved plan file
    generate_from_plan(plan_file=PLAN_FILE)

    # Step 3: Merge subsection markdown files into one document
    merged_text = merge_markdown()

    # Step 4: Convert merged markdown to PDF
    pdf_path = markdown_to_pdf(merged_text)

    return {
        "run_id": run_id,
        "pdf": pdf_path,
        "sections": len(plan.get("sections", []))
    }


@app.get("/download/{filename}")
def download_file(filename: str):
    return FileResponse(
        filename,
        media_type="application/pdf",
        filename=os.path.basename(filename)
    )
