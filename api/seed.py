"""
Seed the database with demo users, requirements, references, tenders, vendors,
workflow approvals, validation checks, audit logs, and notifications.
Run automatically on startup if DB is empty.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import models
from auth import hash_password


def seed_all(db: Session):
    if db.query(models.User).count() > 0:
        return  # already seeded

    # ── USERS ─────────────────────────────────────────────────────────────
    users_data = [
        {"name": "Aryan Kumar", "email": "admin@sail.in", "password": "admin123",
         "role": models.UserRole.admin, "department": "Procurement", "avatar_initials": "AK"},
        {"name": "Amit Kumar", "email": "amit@sail.in", "password": "amit123",
         "role": models.UserRole.procurement_officer, "department": "Contracts & Procurement", "avatar_initials": "AK"},
        {"name": "Rajesh Kumar", "email": "rajesh@sail.in", "password": "rajesh123",
         "role": models.UserRole.procurement_officer, "department": "Information Technology", "avatar_initials": "RK"},
        {"name": "A. Verma", "email": "verma@sail.in", "password": "verma123",
         "role": models.UserRole.technical_reviewer, "department": "Technical", "avatar_initials": "AV"},
        {"name": "R. Sharma", "email": "sharma@sail.in", "password": "sharma123",
         "role": models.UserRole.finance_reviewer, "department": "Finance", "avatar_initials": "RS"},
        {"name": "P. Nair", "email": "nair@sail.in", "password": "nair123",
         "role": models.UserRole.committee_member, "department": "Procurement Cell", "avatar_initials": "PN"},
        {"name": "S. Iyer", "email": "iyer@sail.in", "password": "iyer123",
         "role": models.UserRole.committee_member, "department": "Committee Secretariat", "avatar_initials": "SI"},
        {"name": "N. Singh", "email": "singh@sail.in", "password": "singh123",
         "role": models.UserRole.approving_authority, "department": "Approving Authority", "avatar_initials": "NS"},
    ]
    users = []
    for u in users_data:
        user = models.User(
            name=u["name"], email=u["email"],
            password_hash=hash_password(u["password"]),
            role=u["role"], department=u["department"],
            avatar_initials=u["avatar_initials"]
        )
        db.add(user)
        users.append(user)
    db.flush()

    # ── REFERENCE DOCUMENTS ───────────────────────────────────────────────
    ref_docs_data = [
        {"original_name": "Annual Maintenance Contract - Enterprise Application.pdf",
         "doc_type": "Tender Document", "department": "IT Department",
         "procurement_type": "Service Contracting", "year": 2024,
         "category": "IT Services", "tags": ["Service Contracting", "IT Services", "AMC"]},
        {"original_name": "Software Support and System Integration Services.pdf",
         "doc_type": "Tender Document", "department": "Digital Systems",
         "procurement_type": "Service Procurement", "year": 2023,
         "category": "IT Services", "tags": ["Technical Evaluation", "SLA", "Support"]},
        {"original_name": "Workflow Automation System Implementation.pdf",
         "doc_type": "Technical Specification", "department": "Process Automation",
         "procurement_type": "Solution Implementation", "year": 2022,
         "category": "Software", "tags": ["Digital Platform", "Workflow", "Integration"]},
        {"original_name": "Cloud Infrastructure Management and Support.pdf",
         "doc_type": "Tender Document", "department": "IT Infrastructure",
         "procurement_type": "Service Contracting", "year": 2022,
         "category": "Cloud Services", "tags": ["Cloud Services", "Infrastructure", "SLA"]},
        {"original_name": "Antivirus and Endpoint Security Solutions.pdf",
         "doc_type": "Eligibility Criteria", "department": "IT Security",
         "procurement_type": "Goods & Services", "year": 2021,
         "category": "Security", "tags": ["Cyber Security", "Software"]},
        {"original_name": "Standard Eligibility Clause Library.pdf",
         "doc_type": "Standard Terms", "department": "Procurement",
         "procurement_type": "All", "year": 2024,
         "category": "Clauses", "tags": ["Eligibility", "Standard"]},
        {"original_name": "Payment and Penalty Terms Template.pdf",
         "doc_type": "Standard Terms", "department": "Finance",
         "procurement_type": "All", "year": 2024,
         "category": "Clauses", "tags": ["Payment", "Penalty"]},
        {"original_name": "JHA Safety Reference Manual.pdf",
         "doc_type": "JHA Reference", "department": "Safety",
         "procurement_type": "All", "year": 2023,
         "category": "Safety", "tags": ["Safety", "JHA"]},
    ]
    ref_docs = []
    for i, r in enumerate(ref_docs_data):
        doc = models.ReferenceDocument(
            filename=f"doc_{i+1}.pdf",
            original_name=r["original_name"],
            file_path=f"uploads/doc_{i+1}.pdf",
            doc_type=r["doc_type"],
            department=r["department"],
            procurement_type=r["procurement_type"],
            year=r["year"],
            category=r["category"],
            file_size=1024 * (200 + i * 50),
            is_chunked=True,
            is_embedded=True,
            chunk_count=45 + i * 12,
            tags=r["tags"],
        )
        db.add(doc)
        ref_docs.append(doc)
    db.flush()

    # ── REQUIREMENTS ──────────────────────────────────────────────────────
    req1 = models.Requirement(
        ref_id="REQ-2026-014",
        title="Annual Support for Enterprise Procurement Automation System",
        department="Contracts & Procurement",
        procurement_type="Service Contracting",
        tender_mode="Open Tender Enquiry",
        category="IT Services",
        scope=(
            "Requirement for annual support, maintenance, and enhancement of the "
            "Enterprise Procurement Automation System used by the Contracts & Procurement "
            "Department. The selected vendor shall ensure seamless operations, system "
            "reliability, user enablement, and continuous improvement of the platform."
        ),
        estimated_value=1250000.0,
        delivery_period="120 Days from PO",
        location="Lumbini Data Center, Bhairahawa",
        priority=models.Priority.high,
        additional_instructions=(
            "Please draft tender with standard terms. Follow latest public procurement "
            "guidelines and include quality compliance requirements."
        ),
        status=models.RequirementStatus.in_progress,
        completeness_score=68,
        ai_confidence="Medium",
        missing_inputs=[
            "Detailed technical specification",
            "Evaluation method",
            "Payment terms",
            "Mandatory eligibility criteria",
        ],
        suggested_action="Add scope details or select reference tenders to improve drafting accuracy.",
        user_id=users[1].id,
    )
    req2 = models.Requirement(
        ref_id="REQ-2026-015",
        title="Supply and Installation of Enterprise Network Equipment",
        department="Information Technology Department",
        procurement_type="Capital Procurement",
        tender_mode="OTE",
        category="IT Services",
        scope=(
            "Requirement for supply, installation, configuration and commissioning of enterprise "
            "network switches, routers and related accessories at multiple locations as per specifications."
        ),
        estimated_value=2500000.0,
        delivery_period="90 Days from PO",
        location="Lumbini Data Center, Bhairahawa",
        priority=models.Priority.medium,
        additional_instructions="",
        status=models.RequirementStatus.draft,
        completeness_score=45,
        ai_confidence="Low",
        missing_inputs=["Technical specification", "Evaluation criteria", "Site details"],
        suggested_action="Add technical specs to improve AI confidence.",
        user_id=users[2].id,
    )
    db.add(req1)
    db.add(req2)
    db.flush()

    # Reference selections for req1
    for i, (doc, score, reason) in enumerate(zip(
        ref_docs[:5],
        [0.92, 0.86, 0.81, 0.74, 0.68],
        [
            "Matches support scope, SLA structure, and eligibility criteria.",
            "Strong overlap in technical evaluation approach and support terms.",
            "Relevant to platform deployment, workflow design, and integration clauses.",
            "Partial overlap in infrastructure support and SLA terms.",
            "Relevant to software procurement and support conditions.",
        ]
    )):
        sel = models.ReferenceSelection(
            requirement_id=req1.id,
            document_id=doc.id,
            similarity_score=score,
            key_matching_reason=reason,
            is_selected=(i < 3),
        )
        db.add(sel)
    db.flush()

    # ── TENDER ────────────────────────────────────────────────────────────
    tender1 = models.Tender(
        tender_id="TD/2026/06/00125",
        requirement_id=req1.id,
        title="Annual Support for Enterprise Procurement Automation System",
        status=models.TenderStatus.in_review,
        current_stage=models.WorkflowStage.technical_review,
        draft_content="",
        ai_confidence="High",
        ai_output_version="v1.3",
        source_clauses_count=31,
        human_overrides_count=5,
        pending_validations_count=4,
        confidence_status="Medium-High",
        draft_completeness=86,
        mandatory_checks_completed=18,
        mandatory_checks_total=22,
        pending_human_inputs=4,
        source_references_linked=4,
        version=1,
        last_edited_by="Amit Kumar",
    )
    db.add(tender1)
    db.flush()

    # Tender sections
    sections_data = [
        ("Scope of Work", models.ValidationStatus.completed,
         """**1. Scope of Work**

The scope of the work under this tender is for providing annual support services for the Enterprise Procurement Automation System used by the Contracts & Procurement Department. The selected vendor shall ensure seamless operations, system reliability, user enablement, and continuous improvement of the platform.

1. Deployment, configuration, and stabilization support for the procurement automation system.
   *Source: Ref Tender 02, Clause 4.1*

2. Workflow setup for tender drafting, clause management, approvals, and audit tracking.
   *Source: Commercial Template A, Section 3.1*

3. Support for user onboarding, training, and change management.
   *Source: Ref Tender 01, Clause 2.7*

4. Periodic optimization, issue resolution, and reporting assistance.
   *Source: Commercial Template A, Section 5.1*""",
         "Ref Tender 02, Clause 4.1"),

        ("Technical Specifications", models.ValidationStatus.pending,
         "Technical details to be added. Specify system architecture, integration requirements, SLA parameters, performance benchmarks, and technology stack requirements.",
         None),

        ("Eligibility Criteria", models.ValidationStatus.completed,
         """**3. Eligibility Criteria**

3.1 The bidder shall have minimum 3 years of experience in similar IT procurement support projects.
3.2 Annual turnover as per tender schedule.
3.3 Valid PAN, GST registration.
3.4 ISO 9001:2015 or equivalent certification preferred.
3.5 Similar work completion certificates required.""",
         "Ref Tender 01, Clause 3.2"),

        ("Required Documents", models.ValidationStatus.completed,
         "GST, PAN, work orders, CA certificate listed. Bidder to submit: GST certificate, PAN card, work order copies (3 similar), CA turnover certificate, completion certificates, and undertakings.",
         None),

        ("Commercial Terms", models.ValidationStatus.warning,
         "Payment terms need finance validation. Standard 30-60-90 day milestone-based payment structure to be confirmed with Finance department.",
         None),

        ("Evaluation Method", models.ValidationStatus.pending,
         "Evaluation logic not finalized. Add evaluation criteria - technical and commercial weightages to be decided by committee.",
         None),

        ("JHA / Safety Reference", models.ValidationStatus.warning,
         "Safety reference required for works/service tender. Add JHA safety reference as per SAIL safety policy.",
         None),
    ]

    sections = []
    for i, (name, status, content, src) in enumerate(sections_data):
        sec = models.TenderSection(
            tender_id=tender1.id,
            section_name=name,
            content=content,
            status=status,
            source_ref=src,
            order_index=i,
        )
        db.add(sec)
        sections.append(sec)
    db.flush()

    # ── VALIDATION CHECKS ─────────────────────────────────────────────────
    checks_data = [
        ("1. Scope of Work", models.ValidationStatus.completed,
         "Scope drafted from selected references", "Review required", "Technical"),
        ("2. Technical Specification", models.ValidationStatus.pending,
         "Technical details incomplete", "Add missing specs", "User Department"),
        ("3. Eligibility Criteria", models.ValidationStatus.completed,
         "Similar work and turnover criteria drafted", "Validate threshold", "Procurement"),
        ("4. Required Documents", models.ValidationStatus.completed,
         "GST, PAN, work orders, CA certificate listed", "Confirm final list", "Procurement"),
        ("5. Commercial Terms", models.ValidationStatus.warning,
         "Payment terms need finance validation", "Review required", "Finance"),
        ("6. Evaluation Method", models.ValidationStatus.pending,
         "Evaluation logic not finalized", "Add evaluation criteria", "Committee/Procurement"),
        ("7. JHA / Safety Reference", models.ValidationStatus.warning,
         "Safety reference required for works/service tender", "Add reference", "Safety/Technical"),
    ]
    for i, (area, status, obs, action, owner) in enumerate(checks_data):
        vc = models.ValidationCheck(
            tender_id=tender1.id,
            check_area=area,
            status=status,
            ai_observation=obs,
            human_action_required=action,
            owner=owner,
            order_index=i,
        )
        db.add(vc)
    db.flush()

    # ── APPROVALS ─────────────────────────────────────────────────────────
    approval_stages = [
        (models.WorkflowStage.requirement_created, "Requirement Created", None, None, None,
         models.ApprovalStatus.completed, models.Priority.medium, 0),
        (models.WorkflowStage.ai_draft_generated, "AI Draft Generated", None, None, None,
         models.ApprovalStatus.completed, models.Priority.medium, 1),
        (models.WorkflowStage.technical_review, "Technical Review", "A. Verma", "Technical Reviewer",
         "Technical Reviewer", models.ApprovalStatus.in_progress, models.Priority.high, 2),
        (models.WorkflowStage.finance_review, "Finance Review", "R. Sharma", "Finance",
         "Finance Reviewer", models.ApprovalStatus.pending, models.Priority.medium, 3),
        (models.WorkflowStage.procurement_cell_review, "Procurement Cell Review", "P. Nair",
         "Procurement Cell", "Procurement Cell", models.ApprovalStatus.pending, models.Priority.high, 4),
        (models.WorkflowStage.committee_review, "Committee Review", "S. Iyer",
         "Committee Secretary", "Committee", models.ApprovalStatus.pending, models.Priority.medium, 5),
        (models.WorkflowStage.ready_for_publishing, "Ready for Publishing", "N. Singh",
         "Approving Authority", "Approving Authority", models.ApprovalStatus.pending, models.Priority.high, 6),
    ]
    base_date = datetime(2026, 6, 14)
    for stage, label, assignee, role, owner_role, status, priority, idx in approval_stages:
        ap = models.Approval(
            tender_id=tender1.id,
            stage=stage,
            stage_label=label,
            assignee_name=assignee,
            assignee_role=role,
            owner_role=owner_role,
            status=status,
            priority=priority,
            due_date=base_date + timedelta(days=idx) if assignee else None,
            order_index=idx,
        )
        db.add(ap)
    db.flush()

    # ── COMMENTS ──────────────────────────────────────────────────────────
    comments_data = [
        ("FM", "Finance to confirm payment terms.", "Finance Manager", "Finance"),
        ("TK", "Technical team to validate SLA.", "Technical Lead", "Technical"),
        ("PR", "Procurement to confirm eligibility wording.", "Procurement Officer", "Procurement"),
    ]
    for initials, content, name, role in comments_data:
        c = models.Comment(
            tender_id=tender1.id,
            author_initials=initials,
            author_name=name,
            author_role=role,
            content=content,
            created_at=datetime(2026, 6, 10, 14, 0) - timedelta(hours=[2, 3, 5][comments_data.index((initials, content, name, role))]),
        )
        db.add(c)
    db.flush()

    # ── AUDIT LOGS ────────────────────────────────────────────────────────
    audit_data = [
        ("Draft created by AI Assistant", "AI System", "10 Jun 2026, 10:15 AM"),
        ("Scope section edited by user", "Amit Kumar", "10 Jun 2026, 11:02 AM"),
        ("Eligibility criteria regenerated", "AI System", "10 Jun 2026, 11:45 AM"),
        ("Source references reviewed", "Amit Kumar", "10 Jun 2026, 01:10 PM"),
        ("Checklist exported", "Amit Kumar", "10 Jun 2026, 01:35 PM"),
        ("Sent to technical reviewer", "Amit Kumar", "10 Jun 2026, 02:05 PM"),
    ]
    base_audit = datetime(2026, 6, 10, 10, 15)
    for i, (action, by, _) in enumerate(audit_data):
        al = models.AuditLog(
            tender_id=tender1.id,
            action=action,
            performed_by=by,
            created_at=base_audit + timedelta(minutes=i * 30),
        )
        db.add(al)
    db.flush()

    # ── VENDORS ───────────────────────────────────────────────────────────
    vendors_data = [
        {"name": "TechSoft Solutions Pvt Ltd", "category": "IT Services",
         "annual_turnover": 50000000, "experience_years": 8,
         "certifications": ["ISO 9001:2015", "ISO 27001"], "location": "Pune"},
        {"name": "InfoSys Enterprise Ltd", "category": "IT Services",
         "annual_turnover": 250000000, "experience_years": 15,
         "certifications": ["CMMI Level 5", "ISO 9001:2015", "ISO 27001"], "location": "Bengaluru"},
        {"name": "NetSecure Technologies", "category": "Network & Security",
         "annual_turnover": 30000000, "experience_years": 6,
         "certifications": ["ISO 27001", "CEH"], "location": "Mumbai"},
        {"name": "CloudBase Systems", "category": "Cloud Services",
         "annual_turnover": 80000000, "experience_years": 5,
         "certifications": ["AWS Partner", "ISO 9001:2015"], "location": "Hyderabad"},
    ]
    for v in vendors_data:
        vendor = models.Vendor(
            name=v["name"], category=v["category"],
            annual_turnover=v["annual_turnover"],
            experience_years=v["experience_years"],
            certifications=v["certifications"],
            location=v["location"],
        )
        db.add(vendor)
        db.flush()
        score = models.VendorScore(
            vendor_id=vendor.id,
            technical_score=round(70 + vendors_data.index(v) * 5, 1),
            commercial_score=round(65 + vendors_data.index(v) * 4, 1),
            risk_score=round(20 + vendors_data.index(v) * 3, 1),
            delivery_performance=round(80 + vendors_data.index(v) * 3, 1),
            quality_score=round(75 + vendors_data.index(v) * 4, 1),
            overall_rating=round(72 + vendors_data.index(v) * 4, 1),
            risk_level=["high", "medium", "medium", "low"][vendors_data.index(v)],
        )
        db.add(score)
    db.flush()

    # ── NOTIFICATIONS ─────────────────────────────────────────────────────
    notif_data = [
        ("Technical Review Pending", "TD/2026/06/00125 requires your review", "warning"),
        ("New Tender Generated", "AI draft for REQ-2026-014 completed", "success"),
        ("Comment Added", "R. Sharma commented on payment terms", "info"),
        ("Checklist Warning", "2 items need human validation", "warning"),
    ]
    for title, msg, ntype in notif_data:
        n = models.Notification(
            user_id=users[0].id,
            title=title, message=msg, type=ntype,
        )
        db.add(n)

    db.commit()
    print("Database seeded successfully")
