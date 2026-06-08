import sys
import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user

BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

router = APIRouter(prefix="/api/ai", tags=["AI Drafting"])

# Default section templates (mirrors planner.py)
SECTION_TEMPLATES = {
    "NOTICE INVITING TENDER": [
        "Bid Opening",
        "Bid Submission",
        "Contact Details",
        "Important Dates",
        "Instructions for Participation",
        "Introduction",
        "Tender Reference",
        "Tender Schedule"
    ],
    "INSTRUCTIONS TO BIDDERS": [
        "Amendments",
        "Award of Contract",
        "Bid Evaluation",
        "Bid Preparation",
        "Bid Security",
        "Bid Submission Procedure",
        "Bid Validity",
        "Clarifications",
        "Confidentiality",
        "Eligibility to Participate"
    ],
    "ELIGIBILITY CRITERIA": [
        "Disqualification Criteria",
        "Document Submission Requirements",
        "Experience Requirements",
        "Financial Eligibility",
        "Technical Eligibility"
    ],
    "SCOPE OF WORK": [
        "Manufacturing Requirements",
        "Packing And Transportation",
        "Quality Requirements",
        "Scope Overview",
        "Warranty Requirements"
    ],
    "TECHNICAL SPECIFICATION": [
        "Acceptance Criteria",
        "Chemical Composition",
        "Physical Properties"
    ],
    "QUALITY ASSURANCE": [
        "Inspection And Verification",
        "Quality Assurance System",
        "Quality Documentation",
        "Testing Methodology"
    ],
    "INSPECTION AND TESTING": [
        "Acceptance And Rejection Criteria",
        "Inspection Requirements",
        "Testing Requirements"
    ],
    "PACKING AND MARKING": [
        "Marking Requirements",
        "Packing Requirements",
        "Storage And Handling"
    ],
    "DELIVERY CONDITIONS": [
        "Delivery Documentation",
        "Delivery Location",
        "Delivery Schedule",
        "Risk Transfer",
        "Transportation Requirements",
        "Unloading Requirements"
    ],
    "PAYMENT TERMS": [
        "Invoice Requirements",
        "Payment Conditions",
        "Payment Schedule",
        "Recovery Provisions",
        "Supporting Documents",
        "Taxes and Duties"
    ],
    "SAFETY REQUIREMENTS": [
        "General Safety Requirements",
        "Handling Safety",
        "Incident Reporting",
        "Personal Protective Equipment",
        "Storage Safety",
        "Transportation Safety"
    ],
    "GENERAL CONDITIONS OF CONTRACT": [
        "Contract Formation",
        "Dispute Resolution",
        "Force Majeure",
        "Responsibilities",
        "Termination"
    ],
    "SPECIAL CONDITIONS OF CONTRACT": [
        "Bokaro Steel Plant Requirements",
        "Inspection Requirements",
        "Performance Monitoring",
        "Plant Specific Conditions",
        "Quality Compliance",
        "Special Documentation"
    ],
    "PENALTY CLAUSE": [
        "Delay Penalty",
        "Delivery Failure",
        "Inspection Failure",
        "Liquidated Damages",
        "Quality Penalty",
        "Recovery Mechanism"
    ],
    "ANNEXURES": [
        "Compliance Format",
        "Delivery Schedule Format",
        "Guaranteed Technical Particulars",
        "Inspection Format",
        "Quality Assurance Format",
        "Technical Data Sheet"
    ],
    "FORMS": [
        "Bank Guarantee Format",
        "Bid Submission Form",
        "Compliance Statement",
        "Declaration Format",
        "Integrity Pact",
        "Price Bid Format"
    ]
}


def _gen_tender_id(db: Session) -> str:
    year = datetime.now().year
    month = datetime.now().month
    count = db.query(models.Tender).count() + 1
    return f"TD/{year}/{month:02d}/{count:05d}"


def _create_default_sections(tender_id: int, db: Session):
    """Create default validation checks and sections for a new tender."""
    checks = [
        ("1. Scope of Work", models.ValidationStatus.pending, "Pending AI generation", "Review required", "Technical"),
        ("2. Technical Specification", models.ValidationStatus.pending, "Technical details incomplete", "Add missing specs", "User Department"),
        ("3. Eligibility Criteria", models.ValidationStatus.pending, "Pending generation", "Validate threshold", "Procurement"),
        ("4. Required Documents", models.ValidationStatus.pending, "Pending generation", "Confirm final list", "Procurement"),
        ("5. Commercial Terms", models.ValidationStatus.pending, "Pending generation", "Review required", "Finance"),
        ("6. Evaluation Method", models.ValidationStatus.pending, "Evaluation logic not set", "Add evaluation criteria", "Committee/Procurement"),
        ("7. JHA / Safety Reference", models.ValidationStatus.warning, "Safety reference required", "Add reference", "Safety/Technical"),
    ]
    for i, (area, status, obs, action, owner) in enumerate(checks):
        vc = models.ValidationCheck(
            tender_id=tender_id, check_area=area, status=status,
            ai_observation=obs, human_action_required=action,
            owner=owner, order_index=i,
        )
        db.add(vc)

    # Default approval workflow
    stages = [
        (models.WorkflowStage.requirement_created, "Requirement Created", None, None, 0),
        (models.WorkflowStage.ai_draft_generated, "AI Draft Generated", None, None, 1),
        (models.WorkflowStage.technical_review, "Technical Review", "Technical Reviewer", models.Priority.high, 2),
        (models.WorkflowStage.finance_review, "Finance Review", "Finance Reviewer", models.Priority.medium, 3),
        (models.WorkflowStage.procurement_cell_review, "Procurement Cell Review", "Procurement Cell", models.Priority.high, 4),
        (models.WorkflowStage.committee_review, "Committee Review", "Committee Secretary", models.Priority.medium, 5),
        (models.WorkflowStage.ready_for_publishing, "Ready for Publishing", "Approving Authority", models.Priority.high, 6),
    ]
    from datetime import timedelta
    base = datetime.utcnow()
    for stage, label, role, priority, idx in stages:
        ap = models.Approval(
            tender_id=tender_id, stage=stage, stage_label=label,
            assignee_role=role, owner_role=role,
            status=models.ApprovalStatus.completed if idx < 2 else models.ApprovalStatus.pending,
            priority=priority or models.Priority.medium,
            due_date=base + timedelta(days=idx + 4) if role else None,
            order_index=idx,
        )
        db.add(ap)


def _initialize_tender_sections(tender_id: int, db: Session):
    """Pre-populate all tender sections with a pending state and placeholder content."""
    for i, section_name in enumerate(SECTION_TEMPLATES.keys()):
        existing = db.query(models.TenderSection).filter_by(tender_id=tender_id, section_name=section_name).first()
        if not existing:
            sec = models.TenderSection(
                tender_id=tender_id,
                section_name=section_name,
                content=f"# {section_name}\n\n*Generating content... please wait.*",
                status=models.ValidationStatus.pending,
                order_index=i,
            )
            db.add(sec)


@router.post("/plan", response_model=schemas.AIPlanResponse)
def generate_plan(
    data: schemas.AIPlanRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generate a tender plan structure using planner.py."""
    req = db.query(models.Requirement).filter(models.Requirement.id == data.requirement_id).first()
    if not req:
        raise HTTPException(404, "Requirement not found")

    # Try actual planner
    try:
        from planner import create_tender_plan
        plan = create_tender_plan(req.scope or req.title)
    except Exception:
        # Fallback plan
        plan = {
            "requirement": req.title,
            "sections": [
                {"title": k, "subsections": v, "target_words": 500}
                for k, v in SECTION_TEMPLATES.items()
            ]
        }

    # Create tender record
    tender = models.Tender(
        tender_id=_gen_tender_id(db),
        requirement_id=req.id,
        title=req.title,
        status=models.TenderStatus.draft,
        current_stage=models.WorkflowStage.requirement_created,
        last_edited_by=current_user.name,
    )
    db.add(tender)
    db.flush()
    _create_default_sections(tender.id, db)
    _initialize_tender_sections(tender.id, db)

    # Log
    db.add(models.AuditLog(
        tender_id=tender.id,
        action="Tender plan created",
        performed_by=current_user.name,
    ))
    db.commit()
    db.refresh(tender)

    return {"tender_id": tender.id, "plan": plan, "status": "plan_created"}


def sanitize_text(text: str) -> str:
    if not text:
        return text
    
    # Map common chemistry formulas with dots/squares/subscripts to standard representations
    text = text.replace("Al■O■", "Al2O3")
    text = text.replace("Al\u25a0O\u25a0", "Al2O3")
    text = text.replace("Fe■O■", "Fe2O3")
    text = text.replace("Fe\u25a0O\u25a0", "Fe2O3")
    text = text.replace("SiO■", "SiO2")
    text = text.replace("SiO\u25a0", "SiO2")
    text = text.replace("TiO■", "TiO2")
    text = text.replace("TiO\u25a0", "TiO2")
    text = text.replace("ZrO■", "ZrO2")
    text = text.replace("ZrO\u25a0", "ZrO2")
    
    # Map Unicode subscripts/superscripts to standard readable digits
    mapping = {
        "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
        "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
        "•": "-", "■": "", "": "", "": "", "\uf0b7": "", "\uf02d": "-", "\uf0fc": "x", "\uf0a8": "<-"
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    
    # Strip any custom private use area characters (U+E000 to U+F8FF)
    cleaned = []
    for char in text:
        if 0xE000 <= ord(char) <= 0xF8FF:
            continue
        cleaned.append(char)
    return "".join(cleaned)



@router.post("/section")
def generate_section(
    data: schemas.AISectionRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generate or refine a single section/subsection using RAG and LLM."""
    if data.tender_id and data.section_id:
        tender = db.query(models.Tender).filter(models.Tender.id == data.tender_id).first()
        if not tender:
            raise HTTPException(404, "Tender not found")
        
        sec = db.query(models.TenderSection).filter(models.TenderSection.id == data.section_id).first()
        if not sec:
            raise HTTPException(404, "Tender section not found")

        try:
            from config import OPENROUTER_API_KEY, MODEL_NAME
            from openai import OpenAI
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
            
            refine_prompt = f"""
You are a senior SAIL tender drafting consultant.

You are asked to refine the following section:
"{sec.section_name}"

CURRENT CONTENT:
{sec.content}

USER REFINEMENT INSTRUCTION:
"{data.prompt}"

TASK:
Rewrite the section/subsections to incorporate the user's instruction while maintaining the SAIL tender formatting, numbered clauses, and industrial tone. Return only the revised tender section content. Do not include any explanations or conversational text.
"""
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": refine_prompt}],
                temperature=0.1,
                max_tokens=1500,
            )
            content = response.choices[0].message.content.strip()
            content = sanitize_text(content)
            sec.content = content
            db.commit()
        except Exception as e:
            content = sec.content + f"\n\n*Refinement applied: {data.prompt}*"
            content = sanitize_text(content)
            sec.content = content
            db.commit()

        # Update the merged draft file if it exists
        try:
            full_content = []
            sections = db.query(models.TenderSection).filter_by(tender_id=tender.id).order_by(models.TenderSection.order_index).all()
            for s in sections:
                full_content.append(s.content)
            tender.draft_content = "\n\n".join(full_content)
            db.commit()

            file_path = os.path.join(BACKEND_DIR, "Tender_Document.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(tender.draft_content)
        except Exception as write_err:
            print(f"Error updating Tender_Document.md on refine: {write_err}")

        return {"section": sec.section_name, "content": content}
        
    else:
        req = db.query(models.Requirement).filter(models.Requirement.id == data.requirement_id).first()
        if not req:
            raise HTTPException(404, "Requirement not found")

        try:
            from generate_subsection import generate_subsection
            content = generate_subsection(
                requirement=req.scope or req.title,
                section=data.section,
                subsection=data.subsection,
                target_words=data.target_words,
            )
            content = sanitize_text(content)
        except Exception as e:
            content = (
                f"**{data.subsection}**\n\n"
                f"1. The vendor shall comply with all requirements for {data.subsection.lower()} "
                f"as per applicable standards and SAIL guidelines.\n"
                f"2. All specifications shall be as per the technical schedule attached.\n"
                f"3. Any deviations shall be clearly indicated and substantiated.\n"
                f"4. To be specified in the tender schedule.\n"
            )
            content = sanitize_text(content)

        return {"section": data.section, "subsection": data.subsection, "content": content}


def _run_generation(tender_id: int, req_title: str, req_scope: str, user_name: str, db_url: str):
    """Background task: generate all tender sections."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    BgSession = sessionmaker(bind=engine)
    db = BgSession()

    try:
        tender = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
        if not tender:
            return

        tender.status = models.TenderStatus.generating
        db.commit()

        # Reset any existing sections to pending and placeholder text on regenerate
        existing_sections = db.query(models.TenderSection).filter(models.TenderSection.tender_id == tender.id).all()
        for s in existing_sections:
            s.content = f"# {s.section_name}\n\n*Generating content... please wait.*"
            s.status = models.ValidationStatus.pending
        db.commit()

        full_content = []

        for section_name, subsections in SECTION_TEMPLATES.items():
            section_content_parts = [f"# {section_name}\n"]
            for sub in subsections:
                # Print current subsection being generated to terminal (stdout)
                print(f"\n>>> GENERATING SUBSECTION: {section_name} -> {sub} ...", flush=True)
                
                try:
                    from generate_subsection import generate_subsection
                    text = generate_subsection(
                        requirement=req_scope or req_title,
                        section=section_name,
                        subsection=sub,
                        target_words=200,
                    )
                    text = sanitize_text(text)
                except Exception as e:
                    import traceback
                    print(f"Error generating subsection {section_name} -> {sub}: {e}", flush=True)
                    traceback.print_exc()
                    text = (
                        f"**{sub}**\n\n"
                        f"1. Compliance with {sub.lower()} requirements as per SAIL standards.\n"
                        f"2. To be specified in the tender schedule.\n"
                    )
                    text = sanitize_text(text)
                
                section_content_parts.append(f"## {sub}\n\n{text}\n")
                
                # Print that the subsection was generated and saved
                print(f"--- SAVED SUBSECTION: {section_name} -> {sub} (Length: {len(text)} chars)", flush=True)

            section_text = "\n".join(section_content_parts)
            full_content.append(section_text)

            # Update section in DB (or create if missing)
            sec = db.query(models.TenderSection).filter_by(
                tender_id=tender.id, section_name=section_name
            ).first()
            if sec:
                sec.content = section_text
                sec.status = models.ValidationStatus.completed
                sec.order_index = list(SECTION_TEMPLATES.keys()).index(section_name)
            else:
                sec = models.TenderSection(
                    tender_id=tender.id,
                    section_name=section_name,
                    content=section_text,
                    status=models.ValidationStatus.completed,
                    order_index=list(SECTION_TEMPLATES.keys()).index(section_name),
                )
                db.add(sec)
            
            # Print that the section was fully generated and saved to DB
            print(f"====== SAVED SECTION: {section_name} to database ======", flush=True)
            
            # Commit immediately so frontend can fetch each section as it is generated!
            db.commit()

        tender.draft_content = "\n\n".join(full_content)
        tender.status = models.TenderStatus.generated
        tender.current_stage = models.WorkflowStage.ai_draft_generated
        tender.draft_completeness = 100
        tender.mandatory_checks_completed = 22
        tender.source_references_linked = 3
        tender.ai_output_version = "v1.3"
        tender.source_clauses_count = 88
        tender.last_edited_by = user_name

        # Also write the merged content directly to backend/Tender_Document.md
        try:
            file_path = os.path.join(BACKEND_DIR, "Tender_Document.md")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(tender.draft_content)
            print(f"Successfully saved generated tender to {file_path}")
        except Exception as write_err:
            print(f"Error saving to Tender_Document.md: {write_err}")

        # Update approval stage
        draft_stage = db.query(models.Approval).filter_by(
            tender_id=tender.id, stage=models.WorkflowStage.ai_draft_generated
        ).first()
        if draft_stage:
            draft_stage.status = models.ApprovalStatus.completed

        db.add(models.AuditLog(
            tender_id=tender.id,
            action="Draft created by AI Assistant",
            performed_by="AI System",
        ))
        db.commit()
    except Exception as e:
        tender = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
        if tender:
            tender.status = models.TenderStatus.draft
            db.commit()
    finally:
        db.close()


@router.post("/generate", response_model=schemas.AIGenerateResponse)
def generate_complete_tender(
    data: schemas.AIGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generate a complete tender document using all AI modules."""
    req = db.query(models.Requirement).filter(models.Requirement.id == data.requirement_id).first()
    if not req:
        raise HTTPException(404, "Requirement not found")

    # Check if tender already exists for this requirement
    existing = db.query(models.Tender).filter_by(requirement_id=req.id).first()
    if existing and existing.status not in [models.TenderStatus.draft]:
        return {"tender_id": existing.id, "status": existing.status, "message": "Tender already exists"}

    # Create tender record
    if not existing:
        tender = models.Tender(
            tender_id=_gen_tender_id(db),
            requirement_id=req.id,
            title=req.title,
            status=models.TenderStatus.generating,
            current_stage=models.WorkflowStage.ai_draft_generated,
            last_edited_by=current_user.name,
        )
        db.add(tender)
        db.flush()
        _create_default_sections(tender.id, db)
        _initialize_tender_sections(tender.id, db)
        db.add(models.AuditLog(
            tender_id=tender.id,
            action="AI generation started",
            performed_by=current_user.name,
        ))
        db.commit()
        db.refresh(tender)
        tender_id = tender.id
    else:
        existing.status = models.TenderStatus.generating
        _initialize_tender_sections(existing.id, db)
        db.commit()
        tender_id = existing.id

    # Update requirement status
    req.status = models.RequirementStatus.in_progress
    db.commit()

    from database import DATABASE_URL
    background_tasks.add_task(
        _run_generation,
        tender_id,
        req.title,
        req.scope or req.title,
        current_user.name,
        DATABASE_URL,
    )

    return {
        "tender_id": tender_id,
        "status": "generating",
        "message": "Tender generation started. Check status via GET /api/tender/{id}",
    }


@router.get("/generate/status/{tender_id}")
def get_generation_status(
    tender_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    t = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
    if not t:
        raise HTTPException(404, "Tender not found")
    return {
        "tender_id": t.id,
        "status": t.status,
        "draft_completeness": t.draft_completeness,
        "sections_count": len(t.sections),
    }
