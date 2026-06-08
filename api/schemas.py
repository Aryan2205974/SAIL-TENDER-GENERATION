from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, EmailStr, field_validator
from models import (
    UserRole, RequirementStatus, TenderStatus, WorkflowStage,
    ApprovalStatus, Priority, ValidationStatus
)


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole = UserRole.procurement_officer
    department: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    department: Optional[str]
    avatar_initials: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# REQUIREMENTS
# ─────────────────────────────────────────────

class RequirementCreate(BaseModel):
    title: str
    department: str
    procurement_type: str
    tender_mode: Optional[str] = None
    category: str
    scope: Optional[str] = None
    estimated_value: Optional[float] = None
    delivery_period: Optional[str] = None
    location: Optional[str] = None
    priority: Priority = Priority.medium
    additional_instructions: Optional[str] = None

class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    procurement_type: Optional[str] = None
    tender_mode: Optional[str] = None
    category: Optional[str] = None
    scope: Optional[str] = None
    estimated_value: Optional[float] = None
    delivery_period: Optional[str] = None
    location: Optional[str] = None
    priority: Optional[Priority] = None
    additional_instructions: Optional[str] = None
    status: Optional[RequirementStatus] = None

class RequirementOut(BaseModel):
    id: int
    ref_id: str
    title: str
    department: str
    procurement_type: str
    tender_mode: Optional[str]
    category: str
    scope: Optional[str]
    estimated_value: Optional[float]
    delivery_period: Optional[str]
    location: Optional[str]
    priority: Priority
    additional_instructions: Optional[str]
    status: RequirementStatus
    completeness_score: int
    ai_confidence: str
    missing_inputs: List[str]
    suggested_action: Optional[str]
    user_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# REFERENCE DOCUMENTS
# ─────────────────────────────────────────────

class ReferenceDocOut(BaseModel):
    id: int
    filename: str
    original_name: str
    doc_type: Optional[str]
    department: Optional[str]
    procurement_type: Optional[str]
    year: Optional[int]
    category: Optional[str]
    file_size: Optional[int]
    is_chunked: bool
    is_embedded: bool
    chunk_count: int
    tags: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}

class SimilarTenderResult(BaseModel):
    id: int
    title: str
    department: Optional[str]
    procurement_type: Optional[str]
    year: Optional[int]
    similarity_score: float
    key_matching_reason: str
    tags: List[str]


# ─────────────────────────────────────────────
# RAG
# ─────────────────────────────────────────────

class ChunkRequest(BaseModel):
    document_id: Optional[int] = None

class EmbedRequest(BaseModel):
    document_id: Optional[int] = None

class SimilarTenderRequest(BaseModel):
    query: str
    top_k: int = 5

class RAGOperationResponse(BaseModel):
    status: str
    message: str
    count: Optional[int] = None


# ─────────────────────────────────────────────
# AI DRAFTING
# ─────────────────────────────────────────────

class AIPlanRequest(BaseModel):
    requirement_id: int

class AISectionRequest(BaseModel):
    requirement_id: Optional[int] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    target_words: int = 250
    tender_id: Optional[int] = None
    section_id: Optional[int] = None
    prompt: Optional[str] = None

class AIGenerateRequest(BaseModel):
    requirement_id: int
    selected_reference_ids: Optional[List[int]] = None

class AIPlanResponse(BaseModel):
    tender_id: int
    plan: Any
    status: str

class AIGenerateResponse(BaseModel):
    tender_id: int
    status: str
    message: str


# ─────────────────────────────────────────────
# TENDERS
# ─────────────────────────────────────────────

class TenderSectionOut(BaseModel):
    id: int
    section_name: str
    content: Optional[str]
    status: ValidationStatus
    source_ref: Optional[str]
    order_index: int

    model_config = {"from_attributes": True}

class TenderOut(BaseModel):
    id: int
    tender_id: str
    requirement_id: Optional[int]
    title: str
    status: TenderStatus
    current_stage: WorkflowStage
    ai_confidence: str
    ai_output_version: str
    source_clauses_count: int
    human_overrides_count: int
    pending_validations_count: int
    confidence_status: str
    draft_completeness: int
    mandatory_checks_completed: int
    mandatory_checks_total: int
    pending_human_inputs: int
    source_references_linked: int
    version: int
    last_edited_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    sections: List[TenderSectionOut] = []

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# WORKFLOW
# ─────────────────────────────────────────────

class WorkflowReviewRequest(BaseModel):
    tender_id: int
    comment: Optional[str] = None

class WorkflowApproveRequest(BaseModel):
    tender_id: int
    stage: WorkflowStage
    comment: Optional[str] = None

class WorkflowRejectRequest(BaseModel):
    tender_id: int
    stage: WorkflowStage
    reason: str

class WorkflowCommentRequest(BaseModel):
    tender_id: int
    content: str
    author_name: Optional[str] = None
    author_role: Optional[str] = None

class ApprovalOut(BaseModel):
    id: int
    stage: WorkflowStage
    stage_label: Optional[str]
    assignee_name: Optional[str]
    assignee_role: Optional[str]
    owner_role: Optional[str]
    status: ApprovalStatus
    priority: Priority
    due_date: Optional[datetime]
    order_index: int

    model_config = {"from_attributes": True}

class CommentOut(BaseModel):
    id: int
    author_name: Optional[str]
    author_role: Optional[str]
    author_initials: Optional[str]
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}

class AuditLogOut(BaseModel):
    id: int
    action: str
    performed_by: Optional[str]
    details: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}

class WorkflowStatusResponse(BaseModel):
    tender_id: int
    current_stage: WorkflowStage
    status: TenderStatus
    approvals: List[ApprovalOut]
    comments: List[CommentOut]
    audit_logs: List[AuditLogOut]


# ─────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────

class ValidationCheckOut(BaseModel):
    id: int
    check_area: str
    status: ValidationStatus
    ai_observation: Optional[str]
    human_action_required: Optional[str]
    owner: Optional[str]
    order_index: int

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# VENDORS
# ─────────────────────────────────────────────

class VendorCreate(BaseModel):
    name: str
    category: Optional[str] = None
    annual_turnover: Optional[float] = None
    experience_years: Optional[int] = None
    certifications: Optional[List[str]] = []
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    pan_number: Optional[str] = None
    gstin: Optional[str] = None

class VendorRatingRequest(BaseModel):
    vendor_id: int
    technical_score: float
    commercial_score: float
    delivery_performance: float
    quality_score: float

class VendorOut(BaseModel):
    id: int
    name: str
    category: Optional[str]
    annual_turnover: Optional[float]
    experience_years: Optional[int]
    certifications: List[str]
    location: Optional[str]
    contact_email: Optional[str]
    is_blacklisted: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class VendorRiskOut(BaseModel):
    vendor_id: int
    vendor_name: str
    risk_score: float
    risk_level: str
    technical_score: float
    commercial_score: float
    overall_rating: float
    risk_factors: List[str]


# ─────────────────────────────────────────────
# BIDS
# ─────────────────────────────────────────────

class BidEvaluateRequest(BaseModel):
    bid_id: int
    tender_id: int

class BidScoreRequest(BaseModel):
    bid_id: int
    score: float
    notes: Optional[str] = None

class BidSubmissionOut(BaseModel):
    id: int
    vendor_name: Optional[str]
    original_filename: Optional[str]
    submitted_at: datetime
    status: str

    model_config = {"from_attributes": True}

class BidEvaluationOut(BaseModel):
    id: int
    technical_score: float
    commercial_score: float
    overall_score: float
    ai_summary: Optional[str]
    strengths: List[str]
    weaknesses: List[str]
    recommendation: Optional[str]

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────

class DashboardResponse(BaseModel):
    total_requirements: int
    total_tenders: int
    tenders_in_review: int
    tenders_approved: int
    total_vendors: int
    total_bids: int
    active_workflows: int
    ai_generations_today: int
    recent_activity: List[AuditLogOut]


# ─────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: int
    title: str
    message: Optional[str]
    type: str
    is_read: bool
    link: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# Update forward refs
TokenResponse.model_rebuild()
