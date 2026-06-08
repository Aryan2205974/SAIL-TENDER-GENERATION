from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/api/workflow", tags=["Workflow"])


def _get_tender(tender_id: int, db: Session) -> models.Tender:
    t = db.query(models.Tender).filter(models.Tender.id == tender_id).first()
    if not t:
        raise HTTPException(404, "Tender not found")
    return t


@router.post("/review")
def submit_for_review(
    data: schemas.WorkflowReviewRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tender = _get_tender(data.tender_id, db)
    tender.status = models.TenderStatus.in_review
    tender.current_stage = models.WorkflowStage.technical_review

    # Mark technical review as in_progress
    ap = db.query(models.Approval).filter_by(
        tender_id=tender.id,
        stage=models.WorkflowStage.technical_review,
    ).first()
    if ap:
        ap.status = models.ApprovalStatus.in_progress

    db.add(models.AuditLog(
        tender_id=tender.id,
        action=f"Sent for review by {current_user.name}",
        performed_by=current_user.name,
        details=data.comment,
    ))
    if data.comment:
        db.add(models.Comment(
            tender_id=tender.id,
            author_name=current_user.name,
            author_role=current_user.role.value,
            author_initials=current_user.avatar_initials or "?",
            content=data.comment,
        ))
    db.commit()
    return {"status": "in_review", "message": "Tender submitted for review"}


@router.post("/approve")
def approve_stage(
    data: schemas.WorkflowApproveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tender = _get_tender(data.tender_id, db)

    # Mark current approval as completed
    ap = db.query(models.Approval).filter_by(
        tender_id=tender.id, stage=data.stage
    ).first()
    if ap:
        ap.status = models.ApprovalStatus.completed

    # Advance workflow
    stage_order = [
        models.WorkflowStage.requirement_created,
        models.WorkflowStage.ai_draft_generated,
        models.WorkflowStage.technical_review,
        models.WorkflowStage.finance_review,
        models.WorkflowStage.procurement_cell_review,
        models.WorkflowStage.committee_review,
        models.WorkflowStage.ready_for_publishing,
    ]
    current_idx = stage_order.index(data.stage) if data.stage in stage_order else 0
    if current_idx + 1 < len(stage_order):
        next_stage = stage_order[current_idx + 1]
        tender.current_stage = next_stage
        # Activate next approval
        next_ap = db.query(models.Approval).filter_by(
            tender_id=tender.id, stage=next_stage
        ).first()
        if next_ap:
            next_ap.status = models.ApprovalStatus.in_progress
    else:
        tender.status = models.TenderStatus.approved

    db.add(models.AuditLog(
        tender_id=tender.id,
        action=f"Stage {data.stage.value} approved by {current_user.name}",
        performed_by=current_user.name,
        details=data.comment,
    ))
    if data.comment:
        db.add(models.Comment(
            tender_id=tender.id,
            author_name=current_user.name,
            author_role=current_user.role.value,
            author_initials=current_user.avatar_initials or "?",
            content=data.comment,
        ))
    db.commit()
    return {"status": "approved", "next_stage": tender.current_stage.value}


@router.post("/reject")
def reject_stage(
    data: schemas.WorkflowRejectRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tender = _get_tender(data.tender_id, db)
    tender.status = models.TenderStatus.rejected

    ap = db.query(models.Approval).filter_by(
        tender_id=tender.id, stage=data.stage
    ).first()
    if ap:
        ap.status = models.ApprovalStatus.rejected

    db.add(models.AuditLog(
        tender_id=tender.id,
        action=f"Stage {data.stage.value} rejected by {current_user.name}: {data.reason}",
        performed_by=current_user.name,
        details=data.reason,
    ))
    db.add(models.Comment(
        tender_id=tender.id,
        author_name=current_user.name,
        author_role=current_user.role.value,
        author_initials=current_user.avatar_initials or "?",
        content=f"Rejected: {data.reason}",
    ))
    db.commit()
    return {"status": "rejected", "reason": data.reason}


@router.post("/comment")
def add_comment(
    data: schemas.WorkflowCommentRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_tender(data.tender_id, db)
    comment = models.Comment(
        tender_id=data.tender_id,
        user_id=current_user.id,
        author_name=data.author_name or current_user.name,
        author_role=data.author_role or current_user.role.value,
        author_initials=current_user.avatar_initials or "?",
        content=data.content,
    )
    db.add(comment)
    db.add(models.AuditLog(
        tender_id=data.tender_id,
        action=f"Comment added by {current_user.name}",
        performed_by=current_user.name,
    ))
    db.commit()
    db.refresh(comment)
    return schemas.CommentOut.model_validate(comment)


@router.get("/{tender_id}/status", response_model=schemas.WorkflowStatusResponse)
def get_workflow_status(
    tender_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tender = _get_tender(tender_id, db)
    return {
        "tender_id": tender.id,
        "current_stage": tender.current_stage,
        "status": tender.status,
        "approvals": tender.approvals,
        "comments": tender.comments[-10:],
        "audit_logs": tender.audit_logs[-10:],
    }


@router.get("/{tender_id}/audit", response_model=List[schemas.AuditLogOut])
def get_audit_trail(
    tender_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_tender(tender_id, db)
    return db.query(models.AuditLog).filter_by(
        tender_id=tender_id
    ).order_by(models.AuditLog.created_at.asc()).all()


@router.post("/assign-reviewer")
def assign_reviewer(
    tender_id: int,
    stage: str,
    assignee_name: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    ap = db.query(models.Approval).filter_by(tender_id=tender_id).filter(
        models.Approval.stage_label.contains(stage)
    ).first()
    if ap:
        ap.assignee_name = assignee_name
        db.commit()
    db.add(models.AuditLog(
        tender_id=tender_id,
        action=f"Reviewer {assignee_name} assigned to {stage}",
        performed_by=current_user.name,
    ))
    db.commit()
    return {"status": "assigned", "assignee": assignee_name}
