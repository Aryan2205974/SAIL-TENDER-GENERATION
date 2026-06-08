from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean,
    DateTime, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from database import Base
import enum


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin = "admin"
    procurement_officer = "procurement_officer"
    technical_reviewer = "technical_reviewer"
    finance_reviewer = "finance_reviewer"
    committee_member = "committee_member"
    approving_authority = "approving_authority"


class RequirementStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    in_progress = "in_progress"
    completed = "completed"


class TenderStatus(str, enum.Enum):
    draft = "draft"
    generating = "generating"
    generated = "generated"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    published = "published"


class WorkflowStage(str, enum.Enum):
    requirement_created = "requirement_created"
    ai_draft_generated = "ai_draft_generated"
    technical_review = "technical_review"
    finance_review = "finance_review"
    procurement_cell_review = "procurement_cell_review"
    committee_review = "committee_review"
    ready_for_publishing = "ready_for_publishing"


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    rejected = "rejected"


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ValidationStatus(str, enum.Enum):
    completed = "completed"
    pending = "pending"
    warning = "warning"
    failed = "failed"


# ─────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.procurement_officer)
    department = Column(String(255), nullable=True)
    avatar_initials = Column(String(4), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    requirements = relationship("Requirement", back_populates="owner")
    comments = relationship("Comment", back_populates="author")
    notifications = relationship("Notification", back_populates="user")


# ─────────────────────────────────────────────
# REQUIREMENTS
# ─────────────────────────────────────────────

class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    ref_id = Column(String(50), unique=True, index=True)   # REQ-2026-014
    title = Column(String(500), nullable=False)
    department = Column(String(255), nullable=False)
    procurement_type = Column(String(255), nullable=False)
    tender_mode = Column(String(100), nullable=True)
    category = Column(String(255), nullable=False)
    scope = Column(Text, nullable=True)
    estimated_value = Column(Float, nullable=True)
    delivery_period = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    priority = Column(SAEnum(Priority), default=Priority.medium)
    additional_instructions = Column(Text, nullable=True)
    status = Column(SAEnum(RequirementStatus), default=RequirementStatus.draft)
    completeness_score = Column(Integer, default=0)          # 0-100
    ai_confidence = Column(String(50), default="Low")        # Low/Medium/High
    missing_inputs = Column(JSON, default=list)
    suggested_action = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="requirements")
    tenders = relationship("Tender", back_populates="requirement")
    reference_selections = relationship("ReferenceSelection", back_populates="requirement")


# ─────────────────────────────────────────────
# REFERENCE DOCUMENTS
# ─────────────────────────────────────────────

class ReferenceDocument(Base):
    __tablename__ = "reference_documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), nullable=False)
    original_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    doc_type = Column(String(100), nullable=True)           # Tender Document, Technical Spec, etc.
    department = Column(String(255), nullable=True)
    procurement_type = Column(String(255), nullable=True)
    tender_mode = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    category = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    is_chunked = Column(Boolean, default=False)
    is_embedded = Column(Boolean, default=False)
    chunk_count = Column(Integer, default=0)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    selections = relationship("ReferenceSelection", back_populates="document")


class ReferenceSelection(Base):
    """Which references are selected for a given requirement."""
    __tablename__ = "reference_selections"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    document_id = Column(Integer, ForeignKey("reference_documents.id"))
    similarity_score = Column(Float, nullable=True)
    key_matching_reason = Column(Text, nullable=True)
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    requirement = relationship("Requirement", back_populates="reference_selections")
    document = relationship("ReferenceDocument", back_populates="selections")


# ─────────────────────────────────────────────
# TENDERS
# ─────────────────────────────────────────────

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(50), unique=True, index=True)   # TD/2026/06/00125
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    title = Column(String(500), nullable=False)
    status = Column(SAEnum(TenderStatus), default=TenderStatus.draft)
    current_stage = Column(SAEnum(WorkflowStage), default=WorkflowStage.requirement_created)
    draft_content = Column(Text, nullable=True)
    ai_confidence = Column(String(50), default="Medium")
    ai_output_version = Column(String(20), default="v1.0")
    source_clauses_count = Column(Integer, default=0)
    human_overrides_count = Column(Integer, default=0)
    pending_validations_count = Column(Integer, default=0)
    confidence_status = Column(String(50), default="Medium")
    draft_completeness = Column(Integer, default=0)           # 0-100
    mandatory_checks_completed = Column(Integer, default=0)
    mandatory_checks_total = Column(Integer, default=22)
    pending_human_inputs = Column(Integer, default=0)
    source_references_linked = Column(Integer, default=0)
    version = Column(Integer, default=1)
    last_edited_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirement = relationship("Requirement", back_populates="tenders")
    sections = relationship("TenderSection", back_populates="tender", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="tender", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="tender", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="tender", cascade="all, delete-orphan")
    validation_checks = relationship("ValidationCheck", back_populates="tender", cascade="all, delete-orphan")
    bid_submissions = relationship("BidSubmission", back_populates="tender")


class TenderSection(Base):
    __tablename__ = "tender_sections"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"))
    section_name = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    status = Column(SAEnum(ValidationStatus), default=ValidationStatus.pending)
    source_ref = Column(String(500), nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    tender = relationship("Tender", back_populates="sections")
    subsections = relationship("TenderSubsection", back_populates="section", cascade="all, delete-orphan")


class TenderSubsection(Base):
    __tablename__ = "tender_subsections"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("tender_sections.id"))
    subsection_name = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    source_refs = Column(JSON, default=list)
    order_index = Column(Integer, default=0)

    section = relationship("TenderSection", back_populates="subsections")


# ─────────────────────────────────────────────
# WORKFLOW
# ─────────────────────────────────────────────

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"))
    stage = Column(SAEnum(WorkflowStage), nullable=False)
    stage_label = Column(String(255), nullable=True)
    assignee_name = Column(String(255), nullable=True)
    assignee_role = Column(String(255), nullable=True)
    owner_role = Column(String(255), nullable=True)
    status = Column(SAEnum(ApprovalStatus), default=ApprovalStatus.pending)
    priority = Column(SAEnum(Priority), default=Priority.medium)
    due_date = Column(DateTime, nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tender = relationship("Tender", back_populates="approvals")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    author_name = Column(String(255), nullable=True)
    author_role = Column(String(255), nullable=True)
    author_initials = Column(String(4), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tender = relationship("Tender", back_populates="comments")
    author = relationship("User", back_populates="comments")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"))
    action = Column(String(500), nullable=False)
    performed_by = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tender = relationship("Tender", back_populates="audit_logs")


class ValidationCheck(Base):
    __tablename__ = "validation_checks"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"))
    check_area = Column(String(255), nullable=False)
    status = Column(SAEnum(ValidationStatus), default=ValidationStatus.pending)
    ai_observation = Column(Text, nullable=True)
    human_action_required = Column(Text, nullable=True)
    owner = Column(String(255), nullable=True)
    order_index = Column(Integer, default=0)

    tender = relationship("Tender", back_populates="validation_checks")


# ─────────────────────────────────────────────
# VENDORS
# ─────────────────────────────────────────────

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    category = Column(String(255), nullable=True)
    annual_turnover = Column(Float, nullable=True)
    experience_years = Column(Integer, nullable=True)
    certifications = Column(JSON, default=list)
    location = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    pan_number = Column(String(20), nullable=True)
    gstin = Column(String(20), nullable=True)
    is_blacklisted = Column(Boolean, default=False)
    registration_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scores = relationship("VendorScore", back_populates="vendor", cascade="all, delete-orphan")
    bids = relationship("BidSubmission", back_populates="vendor")


class VendorScore(Base):
    __tablename__ = "vendor_scores"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    technical_score = Column(Float, default=0.0)
    commercial_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    delivery_performance = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    overall_rating = Column(Float, default=0.0)
    risk_level = Column(String(50), default="medium")
    evaluated_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="scores")


# ─────────────────────────────────────────────
# BIDS
# ─────────────────────────────────────────────

class BidSubmission(Base):
    __tablename__ = "bid_submissions"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"))
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    vendor_name = Column(String(500), nullable=True)
    file_path = Column(String(1000), nullable=True)
    original_filename = Column(String(500), nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(100), default="submitted")

    tender = relationship("Tender", back_populates="bid_submissions")
    vendor = relationship("Vendor", back_populates="bids")
    evaluation = relationship("BidEvaluation", back_populates="bid", uselist=False)


class BidEvaluation(Base):
    __tablename__ = "bid_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    bid_id = Column(Integer, ForeignKey("bid_submissions.id"))
    technical_score = Column(Float, default=0.0)
    commercial_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    ai_summary = Column(Text, nullable=True)
    strengths = Column(JSON, default=list)
    weaknesses = Column(JSON, default=list)
    recommendation = Column(String(100), nullable=True)
    evaluated_at = Column(DateTime, default=datetime.utcnow)

    bid = relationship("BidSubmission", back_populates="evaluation")


# ─────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=True)
    type = Column(String(100), default="info")   # info, warning, success, error
    is_read = Column(Boolean, default=False)
    link = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
