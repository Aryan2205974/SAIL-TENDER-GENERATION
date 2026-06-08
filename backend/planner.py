# import json

# ##from groq import Groq

# from config import (
#     HUGGINGFACE_API_KEY,
#     MODEL_NAME
# )

# from retrieve import build_context

# # =====================================================
# # GROQ CLIENT
# # =====================================================

# client = Groq(
#     api_key=GROQ_API_KEY
# )

# # =====================================================
# # SECTION TEMPLATES
# # =====================================================

# SECTION_TEMPLATES = {

#     "NOTICE INVITING TENDER": [
#         "Introduction",
#         "Tender Reference",
#         "Tender Schedule",
#         "Bid Submission",
#         "Bid Opening",
#         "Important Dates",
#         "Contact Details",
#         "Instructions for Participation"
#     ],

#     "INSTRUCTIONS TO BIDDERS": [
#         "Eligibility to Participate",
#         "Bid Preparation",
#         "Bid Submission Procedure",
#         "Bid Validity",
#         "Bid Security",
#         "Bid Evaluation",
#         "Award of Contract",
#         "Confidentiality",
#         "Clarifications",
#         "Amendments"
#     ],

#     "ELIGIBILITY CRITERIA": [
#         "General Eligibility",
#         "Technical Eligibility",
#         "Manufacturing Capability",
#         "Production Capacity",
#         "Similar Work Experience",
#         "Financial Eligibility",
#         "Quality Certifications",
#         "Statutory Compliance",
#         "Document Submission Requirements",
#         "Evaluation Methodology",
#         "Disqualification Criteria"
#     ],

#     "SCOPE OF WORK": [
#         "Scope Overview",
#         "Manufacturing Requirements",
#         "Raw Material Requirements",
#         "Production Requirements",
#         "Quality Control Requirements",
#         "Inspection Requirements",
#         "Testing Requirements",
#         "Packing Requirements",
#         "Marking Requirements",
#         "Transportation Requirements",
#         "Delivery Requirements",
#         "Warranty Requirements",
#         "Technical Support Requirements"
#     ],

#     "TECHNICAL SPECIFICATION": [
#         "Chemical Composition",
#         "Al2O3 Content",
#         "MgO Content",
#         "Spinel Content",
#         "Bulk Density",
#         "Apparent Porosity",
#         "Cold Crushing Strength",
#         "Permanent Linear Change",
#         "Thermal Shock Resistance",
#         "Refractoriness Under Load",
#         "Dimensional Tolerance",
#         "Sampling Procedure",
#         "Testing Requirements",
#         "Acceptance Criteria"
#     ],

#     "QUALITY ASSURANCE": [
#         "Quality Assurance System",
#         "Raw Material Inspection",
#         "Incoming Material Verification",
#         "In Process Inspection",
#         "Final Inspection",
#         "Testing Methodology",
#         "Calibration Requirements",
#         "Traceability Requirements",
#         "Corrective Actions",
#         "Quality Documentation"
#     ],

#     "INSPECTION AND TESTING": [
#         "General Inspection Requirements",
#         "Pre Dispatch Inspection",
#         "Witness Testing",
#         "Sampling Procedure",
#         "Laboratory Testing",
#         "Acceptance Testing",
#         "Rejection Criteria",
#         "Inspection Documentation"
#     ],

#     "PACKING AND MARKING": [
#         "Packing Requirements",
#         "Packing Materials",
#         "Packing Methodology",
#         "Marking Requirements",
#         "Identification Requirements",
#         "Storage Requirements",
#         "Handling Requirements"
#     ],

#     "DELIVERY CONDITIONS": [
#         "Delivery Schedule",
#         "Delivery Location",
#         "Transportation Requirements",
#         "Unloading Requirements",
#         "Delivery Documentation",
#         "Risk Transfer"
#     ],

#     "PAYMENT TERMS": [
#         "Payment Conditions",
#         "Invoice Requirements",
#         "Supporting Documents",
#         "Payment Schedule",
#         "Taxes and Duties",
#         "Recovery Provisions"
#     ],

#     "SAFETY REQUIREMENTS": [
#         "General Safety Requirements",
#         "Personal Protective Equipment",
#         "Handling Safety",
#         "Transportation Safety",
#         "Storage Safety",
#         "Incident Reporting"
#     ],

#     "GENERAL CONDITIONS OF CONTRACT": [
#         "Definitions",
#         "Contract Formation",
#         "Contract Documents",
#         "Responsibilities of Supplier",
#         "Responsibilities of Purchaser",
#         "Force Majeure",
#         "Termination",
#         "Dispute Resolution",
#         "Arbitration",
#         "Governing Law"
#     ],

#     "SPECIAL CONDITIONS OF CONTRACT": [
#         "Bokaro Steel Plant Requirements",
#         "Plant Specific Conditions",
#         "Quality Compliance",
#         "Inspection Requirements",
#         "Special Documentation",
#         "Performance Monitoring"
#     ],

#     "PENALTY CLAUSE": [
#         "Delay Penalty",
#         "Quality Penalty",
#         "Inspection Failure",
#         "Delivery Failure",
#         "Liquidated Damages",
#         "Recovery Mechanism"
#     ],

#     "ANNEXURES": [
#         "Technical Data Sheet",
#         "Guaranteed Technical Particulars",
#         "Quality Assurance Format",
#         "Inspection Format",
#         "Delivery Schedule Format",
#         "Compliance Format"
#     ],

#     "FORMS": [
#         "Bid Submission Form",
#         "Price Bid Format",
#         "Bank Guarantee Format",
#         "Integrity Pact",
#         "Declaration Format",
#         "Compliance Statement"
#     ]
# }

# # =====================================================
# # SECTION TARGET WORD COUNTS
# # =====================================================

# SECTION_TARGET_WORDS = {

#     "NOTICE INVITING TENDER": 1500,
#     "INSTRUCTIONS TO BIDDERS": 4000,
#     "ELIGIBILITY CRITERIA": 6000,
#     "SCOPE OF WORK": 8000,
#     "TECHNICAL SPECIFICATION": 12000,
#     "QUALITY ASSURANCE": 4000,
#     "INSPECTION AND TESTING": 4000,
#     "PACKING AND MARKING": 2500,
#     "DELIVERY CONDITIONS": 2500,
#     "PAYMENT TERMS": 2500,
#     "SAFETY REQUIREMENTS": 2500,
#     "GENERAL CONDITIONS OF CONTRACT": 8000,
#     "SPECIAL CONDITIONS OF CONTRACT": 5000,
#     "PENALTY CLAUSE": 2000,
#     "ANNEXURES": 4000,
#     "FORMS": 3000
# }

# # =====================================================
# # RETRIEVE CONTEXT
# # =====================================================

# def get_reference_context(requirement):

#     try:

#         context = build_context(
#             query=requirement,
#             top_k=10
#         )

#         return context[:10000]

#     except Exception as e:

#         print(
#             f"Warning: Retrieval Failed: {e}"
#         )

#         return ""

# # =====================================================
# # CREATE PLAN
# # =====================================================

# def create_tender_plan(requirement):

#     context = get_reference_context(
#         requirement
#     )

#     sections = []

#     for section_name, subsection_list in SECTION_TEMPLATES.items():

#         sections.append({

#             "title": section_name,

#             "target_words":
#             SECTION_TARGET_WORDS.get(
#                 section_name,
#                 3000
#             ),

#             "subsections":
#             subsection_list

#         })

#     plan = {

#         "requirement": requirement,

#         "reference_context":
#         context,

#         "sections":
#         sections
#     }

#     return plan

# # =====================================================
# # SAVE PLAN
# # =====================================================

# def save_plan(
#         plan,
#         output_file="tender_plan.json"
# ):

#     with open(
#         output_file,
#         "w",
#         encoding="utf-8"
#     ) as f:

#         json.dump(
#             plan,
#             f,
#             indent=4,
#             ensure_ascii=False
#         )

# # =====================================================
# # DISPLAY PLAN
# # =====================================================

# def display_plan(plan):

#     print("\n")

#     print("=" * 80)

#     print("GENERATED TENDER STRUCTURE")

#     print("=" * 80)

#     total_subsections = 0

#     for section in plan["sections"]:

#         print(
#             f"\n{section['title']}"
#         )

#         print(
#             f"Target Words: {section['target_words']}"
#         )

#         for subsection in section["subsections"]:

#             print(
#                 f"   - {subsection}"
#             )

#             total_subsections += 1

#     print("\n")

#     print("=" * 80)

#     print(
#         f"Sections: {len(plan['sections'])}"
#     )

#     print(
#         f"Subsections: {total_subsections}"
#     )

#     print("=" * 80)

# # =====================================================
# # MAIN
# # =====================================================

# if __name__ == "__main__":

#     requirement = input(
#         "\nTender Requirement:\n"
#     )

#     plan = create_tender_plan(
#         requirement
#     )

#     save_plan(plan)

#     display_plan(plan)

#     print(
#         "\nTender Plan Saved To: tender_plan.json"
#     )



# hugging phase



import json

from retrieve import build_context

# =====================================================
# SECTION TEMPLATES
# =====================================================

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
SECTION_LENGTH = {
    "NOTICE INVITING TENDER": 500,
    "INSTRUCTIONS TO BIDDERS": 1000,
    "ELIGIBILITY CRITERIA": 800,
    "SCOPE OF WORK": 1200,
    "TECHNICAL SPECIFICATION": 2500,
    "QUALITY ASSURANCE": 800,
    "INSPECTION AND TESTING": 800,
    "PACKING AND MARKING": 500,
    "DELIVERY CONDITIONS": 600,
    "PAYMENT TERMS": 500,
    "SAFETY REQUIREMENTS": 500,
    "GENERAL CONDITIONS OF CONTRACT": 1800,
    "SPECIAL CONDITIONS OF CONTRACT": 1000,
    "PENALTY CLAUSE": 400,
    "ANNEXURES": 1000,
    "FORMS": 800
}
TOTAL_TARGET_WORDS = sum(
    SECTION_LENGTH.values()
)
# =====================================================
# RETRIEVE CONTEXT
# =====================================================

def get_reference_context(requirement):

    try:
        context = build_context(
            query=requirement,
            top_k=10
        )

        return context[:6000]

    except Exception as e:

        print(f"Warning: Retrieval Failed: {e}")
        return ""

# =====================================================
# CREATE PLAN
# =====================================================

def create_tender_plan(requirement):

    context = get_reference_context(requirement)

    sections = []

    for section_name, subsection_list in SECTION_TEMPLATES.items():

        sections.append({

        "title": section_name,

        "target_words":
        SECTION_LENGTH.get(
            section_name,
            3000
        ),

        "subsections":
        subsection_list

    })
    return {

        "requirement": requirement,
        "reference_context": context,
        "sections": sections

    }

# =====================================================
# SAVE PLAN
# =====================================================

def save_plan(
    plan,
    output_file="tender_plan.json"
):

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            plan,
            f,
            indent=4,
            ensure_ascii=False
        )

# =====================================================
# DISPLAY PLAN
# =====================================================

def display_plan(plan):

    print("\n")
    print("=" * 80)
    print("GENERATED TENDER STRUCTURE")
    print("=" * 80)

    total_subsections = 0

    for section in plan["sections"]:

        print(f"\n{section['title']}")
        print(f"Target Words: {section['target_words']}")

        for subsection in section["subsections"]:

            print(f"   - {subsection}")
            total_subsections += 1

    print("\n")
    print("=" * 80)
    print(f"Sections: {len(plan['sections'])}")
    print(f"Subsections: {total_subsections}")
    print(f"Target Words: {TOTAL_TARGET_WORDS}")
    print(f"Estimated Pages: {TOTAL_TARGET_WORDS // 550}")
    print("=" * 80)
# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    requirement = input(
        "\nTender Requirement:\n"
    )

    plan = create_tender_plan(
        requirement
    )

    save_plan(plan)

    display_plan(plan)

    print(
        "\nTender Plan Saved To: tender_plan.json"
    )