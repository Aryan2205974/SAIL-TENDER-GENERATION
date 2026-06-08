import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/api/bids", tags=["Bid Evaluation"])

BIDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "bids")
os.makedirs(BIDS_DIR, exist_ok=True)


@router.post("/upload", response_model=schemas.BidSubmissionOut, status_code=201)
async def upload_bid(
    tender_id: int = Form(...),
    vendor_name: str = Form(None),
    vendor_id: int = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tender = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "Tender not found")

    safe_name = f"bid_{db.query(models.BidSubmission).count() + 1}_{file.filename}"
    file_path = os.path.join(BIDS_DIR, safe_name)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    bid = models.BidSubmission(
        tender_id=tender_id,
        vendor_id=vendor_id,
        vendor_name=vendor_name,
        file_path=file_path,
        original_filename=file.filename,
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


@router.get("/{tender_id}", response_model=List[schemas.BidSubmissionOut])
def list_bids(
    tender_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.BidSubmission).filter_by(
        tender_id=tender_id
    ).order_by(models.BidSubmission.submitted_at.desc()).all()


@router.post("/evaluate", response_model=schemas.BidEvaluationOut)
def evaluate_bid(
    data: schemas.BidEvaluateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    bid = db.query(models.BidSubmission).filter(models.BidSubmission.id == data.bid_id).first()
    if not bid:
        raise HTTPException(404, "Bid not found")

    # AI evaluation simulation — in production, this would use the LLM
    import random
    tech = round(random.uniform(60, 95), 1)
    comm = round(random.uniform(55, 90), 1)
    overall = round((tech * 0.6 + comm * 0.4), 1)

    strengths = [
        "Strong technical capability demonstrated",
        "Good track record in similar projects",
        "Competitive pricing structure",
    ][:random.randint(1, 3)]

    weaknesses = [
        "Limited experience in public sector",
        "No ISO 27001 certification",
        "Delivery timeline needs improvement",
    ][:random.randint(0, 2)]

    recommendation = "Recommended" if overall >= 70 else ("Conditional" if overall >= 55 else "Not Recommended")

    evaluation = models.BidEvaluation(
        bid_id=bid.id,
        technical_score=tech,
        commercial_score=comm,
        overall_score=overall,
        ai_summary=f"Bid evaluation completed with overall score of {overall}/100. "
                    f"Technical: {tech}, Commercial: {comm}.",
        strengths=strengths,
        weaknesses=weaknesses,
        recommendation=recommendation,
    )
    db.add(evaluation)
    bid.status = "evaluated"
    db.commit()
    db.refresh(evaluation)
    return evaluation


@router.post("/technical-score")
def set_technical_score(
    data: schemas.BidScoreRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ev = db.query(models.BidEvaluation).filter_by(bid_id=data.bid_id).first()
    if not ev:
        raise HTTPException(404, "No evaluation found for this bid")
    ev.technical_score = data.score
    ev.overall_score = round((ev.technical_score * 0.6 + ev.commercial_score * 0.4), 1)
    db.commit()
    return {"bid_id": data.bid_id, "technical_score": data.score, "overall_score": ev.overall_score}


@router.post("/commercial-score")
def set_commercial_score(
    data: schemas.BidScoreRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ev = db.query(models.BidEvaluation).filter_by(bid_id=data.bid_id).first()
    if not ev:
        raise HTTPException(404, "No evaluation found for this bid")
    ev.commercial_score = data.score
    ev.overall_score = round((ev.technical_score * 0.6 + ev.commercial_score * 0.4), 1)
    db.commit()
    return {"bid_id": data.bid_id, "commercial_score": data.score, "overall_score": ev.overall_score}
