import random
import string
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/api/requirements", tags=["Requirements"])


def _gen_ref_id(db: Session) -> str:
    year = datetime.now().year
    count = db.query(models.Requirement).count() + 1
    return f"REQ-{year}-{count:03d}"


def _calc_completeness(data: dict) -> tuple[int, str, list, str]:
    fields = {
        "title": 15, "department": 10, "procurement_type": 10,
        "category": 10, "scope": 15, "estimated_value": 10,
        "delivery_period": 10, "location": 5, "priority": 5,
        "additional_instructions": 10,
    }
    score = sum(w for f, w in fields.items() if data.get(f))
    missing = [f.replace("_", " ").title() for f, w in fields.items() if not data.get(f)]

    if score >= 80:
        confidence, action = "High", "Ready for AI drafting."
    elif score >= 50:
        confidence, action = "Medium", "Add scope details or select reference tenders to improve drafting accuracy."
    else:
        confidence, action = "Low", "Add more details to improve AI confidence before generating tender."

    return score, confidence, missing, action


@router.post("", response_model=schemas.RequirementOut, status_code=201)
def create_requirement(
    data: schemas.RequirementCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    score, confidence, missing, action = _calc_completeness(data.model_dump())
    req = models.Requirement(
        ref_id=_gen_ref_id(db),
        **data.model_dump(),
        completeness_score=score,
        ai_confidence=confidence,
        missing_inputs=missing,
        suggested_action=action,
        user_id=current_user.id,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


@router.get("", response_model=List[schemas.RequirementOut])
def list_requirements(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.Requirement)
    if status:
        q = q.filter(models.Requirement.status == status)
    return q.order_by(models.Requirement.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{req_id}", response_model=schemas.RequirementOut)
def get_requirement(
    req_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    req = db.query(models.Requirement).filter(models.Requirement.id == req_id).first()
    if not req:
        raise HTTPException(404, "Requirement not found")
    return req


@router.put("/{req_id}", response_model=schemas.RequirementOut)
def update_requirement(
    req_id: int,
    data: schemas.RequirementUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    req = db.query(models.Requirement).filter(models.Requirement.id == req_id).first()
    if not req:
        raise HTTPException(404, "Requirement not found")

    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(req, k, v)

    # Recalculate completeness
    current = {
        "title": req.title, "department": req.department,
        "procurement_type": req.procurement_type, "category": req.category,
        "scope": req.scope, "estimated_value": req.estimated_value,
        "delivery_period": req.delivery_period, "location": req.location,
        "priority": req.priority, "additional_instructions": req.additional_instructions,
    }
    score, confidence, missing, action = _calc_completeness(current)
    req.completeness_score = score
    req.ai_confidence = confidence
    req.missing_inputs = missing
    req.suggested_action = action

    db.commit()
    db.refresh(req)
    return req


@router.delete("/{req_id}", status_code=204)
def delete_requirement(
    req_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    req = db.query(models.Requirement).filter(models.Requirement.id == req_id).first()
    if not req:
        raise HTTPException(404, "Requirement not found")
    db.delete(req)
    db.commit()
