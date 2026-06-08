from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/api/vendors", tags=["Vendors"])


@router.post("", response_model=schemas.VendorOut, status_code=201)
def create_vendor(
    data: schemas.VendorCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    vendor = models.Vendor(**data.model_dump())
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("", response_model=List[schemas.VendorOut])
def list_vendors(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.Vendor)
    if category:
        q = q.filter(models.Vendor.category == category)
    return q.order_by(models.Vendor.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{vendor_id}", response_model=schemas.VendorOut)
def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    v = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not v:
        raise HTTPException(404, "Vendor not found")
    return v


@router.post("/rating")
def submit_vendor_rating(
    data: schemas.VendorRatingRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    vendor = db.query(models.Vendor).filter(models.Vendor.id == data.vendor_id).first()
    if not vendor:
        raise HTTPException(404, "Vendor not found")

    # Risk score = inverse of performance metrics
    risk_score = max(0, 100 - (data.technical_score + data.commercial_score + data.delivery_performance) / 3)
    overall = (data.technical_score + data.commercial_score + data.delivery_performance + data.quality_score) / 4

    risk_level = "low" if risk_score < 30 else ("medium" if risk_score < 60 else "high")

    score = models.VendorScore(
        vendor_id=data.vendor_id,
        technical_score=data.technical_score,
        commercial_score=data.commercial_score,
        risk_score=round(risk_score, 1),
        delivery_performance=data.delivery_performance,
        quality_score=data.quality_score,
        overall_rating=round(overall, 1),
        risk_level=risk_level,
    )
    db.add(score)
    db.commit()
    db.refresh(score)

    return {
        "vendor_id": data.vendor_id,
        "overall_rating": overall,
        "risk_score": risk_score,
        "risk_level": risk_level,
    }


@router.get("/risk/{vendor_id}", response_model=schemas.VendorRiskOut)
def get_vendor_risk(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    vendor = db.query(models.Vendor).filter(models.Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(404, "Vendor not found")

    # Get latest score
    score = db.query(models.VendorScore).filter_by(vendor_id=vendor_id).order_by(
        models.VendorScore.evaluated_at.desc()
    ).first()

    if not score:
        raise HTTPException(404, "No rating found for vendor")

    risk_factors = []
    if score.technical_score < 60:
        risk_factors.append("Low technical score")
    if score.commercial_score < 60:
        risk_factors.append("Unfavorable commercial terms")
    if score.delivery_performance < 70:
        risk_factors.append("Poor delivery track record")
    if vendor.is_blacklisted:
        risk_factors.append("Vendor is blacklisted")
    if (vendor.experience_years or 0) < 3:
        risk_factors.append("Limited industry experience")
    if not risk_factors:
        risk_factors.append("No significant risk factors identified")

    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "risk_score": score.risk_score,
        "risk_level": score.risk_level,
        "technical_score": score.technical_score,
        "commercial_score": score.commercial_score,
        "overall_rating": score.overall_rating,
        "risk_factors": risk_factors,
    }
