import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/api/reference", tags=["Reference Library"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=schemas.ReferenceDocOut, status_code=201)
async def upload_reference(
    file: UploadFile = File(...),
    doc_type: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    procurement_type: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Save file
    safe_name = f"{db.query(models.ReferenceDocument).count() + 1}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = os.path.getsize(file_path)

    doc = models.ReferenceDocument(
        filename=safe_name,
        original_name=file.filename,
        file_path=file_path,
        doc_type=doc_type,
        department=department,
        procurement_type=procurement_type,
        year=year,
        category=category,
        file_size=file_size,
        tags=[],
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("", response_model=List[schemas.ReferenceDocOut])
def list_references(
    department: Optional[str] = None,
    doc_type: Optional[str] = None,
    year: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.ReferenceDocument)
    if department:
        q = q.filter(models.ReferenceDocument.department == department)
    if doc_type:
        q = q.filter(models.ReferenceDocument.doc_type == doc_type)
    if year:
        q = q.filter(models.ReferenceDocument.year == year)
    return q.order_by(models.ReferenceDocument.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{doc_id}", response_model=schemas.ReferenceDocOut)
def get_reference(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.ReferenceDocument).filter(models.ReferenceDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.delete("/{doc_id}", status_code=204)
def delete_reference(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    doc = db.query(models.ReferenceDocument).filter(models.ReferenceDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    # Remove file if exists
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()


@router.post("/{req_id}/select/{doc_id}")
def select_reference(
    req_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Toggle reference selection for a requirement."""
    sel = db.query(models.ReferenceSelection).filter_by(
        requirement_id=req_id, document_id=doc_id
    ).first()
    if sel:
        sel.is_selected = not sel.is_selected
    else:
        sel = models.ReferenceSelection(
            requirement_id=req_id, document_id=doc_id, is_selected=True
        )
        db.add(sel)
    db.commit()
    return {"selected": sel.is_selected}


@router.get("/{req_id}/similar", response_model=List[schemas.SimilarTenderResult])
def get_similar_for_requirement(
    req_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get AI-recommended similar tenders from reference selections."""
    req = db.query(models.Requirement).filter(models.Requirement.id == req_id).first()
    if not req:
        raise HTTPException(404, "Requirement not found")

    selections = db.query(models.ReferenceSelection).filter_by(
        requirement_id=req_id
    ).order_by(models.ReferenceSelection.similarity_score.desc()).all()

    results = []
    for sel in selections:
        doc = sel.document
        results.append(schemas.SimilarTenderResult(
            id=doc.id,
            title=doc.original_name.replace(".pdf", "").replace(".docx", ""),
            department=doc.department,
            procurement_type=doc.procurement_type,
            year=doc.year,
            similarity_score=sel.similarity_score or 0.0,
            key_matching_reason=sel.key_matching_reason or "Similar procurement scope.",
            tags=doc.tags or [],
        ))
    return results
