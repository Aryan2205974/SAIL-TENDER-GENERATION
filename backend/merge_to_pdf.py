import os
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet

SUBSECTION_DIR = "subsections"



timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

MERGED_MD = f"Tender_Document_{timestamp}.md"
OUTPUT_PDF = f"Tender_Document_{timestamp}.pdf"

SECTION_ORDER = [
    "NOTICE_INVITING_TENDER",
    "INSTRUCTIONS_TO_BIDDERS",
    "ELIGIBILITY_CRITERIA",
    "SCOPE_OF_WORK",
    "TECHNICAL_SPECIFICATION",
    "QUALITY_ASSURANCE",
    "INSPECTION_AND_TESTING",
    "PACKING_AND_MARKING",
    "DELIVERY_CONDITIONS",
    "PAYMENT_TERMS",
    "SAFETY_REQUIREMENTS",
    "GENERAL_CONDITIONS_OF_CONTRACT",
    "SPECIAL_CONDITIONS_OF_CONTRACT",
    "PENALTY_CLAUSE",
    "ANNEXURES",
    "FORMS"
]


def merge_markdown():

    merged_content = []

    for section in SECTION_ORDER:

        section_path = os.path.join(
            SUBSECTION_DIR,
            section
        )

        if not os.path.exists(section_path):
            continue

        if not os.path.isdir(section_path):
            continue

        merged_content.append(
            f"# {section.replace('_', ' ')}\n\n"
        )

        # No alphabetical sorting
        for file in os.listdir(section_path):

            if not file.endswith(".md"):
                continue

            file_path = os.path.join(
                section_path,
                file
            )

            subsection = (
                file.replace(".md", "")
                .replace("_", " ")
            )

            merged_content.append(
                f"## {subsection}\n\n"
            )

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                merged_content.append(
                    f.read()
                )

            merged_content.append("\n\n")

    with open(
        MERGED_MD,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "\n".join(merged_content)
        )

    print(
        f"Merged Markdown Saved: {MERGED_MD}"
    )

    return "\n".join(
        merged_content
    )


def markdown_to_pdf(text):

    doc = SimpleDocTemplate(
        OUTPUT_PDF
    )

    styles = getSampleStyleSheet()

    story = []

    first_section = True

    for line in text.split("\n"):

        line = line.strip()

        if not line:
            story.append(
                Spacer(1, 6)
            )
            continue

        if line.startswith("# "):

            # Page break only after first section
            if not first_section:
                story.append(
                    PageBreak()
                )

            first_section = False

            story.append(
                Paragraph(
                    line[2:],
                    styles["Title"]
                )
            )

            story.append(
                Spacer(1, 12)
            )

        elif line.startswith("## "):

            story.append(
                Paragraph(
                    line[3:],
                    styles["Heading2"]
                )
            )

            story.append(
                Spacer(1, 6)
            )

        else:

            story.append(
                Paragraph(
                    line,
                    styles["BodyText"]
                )
            )

    doc.build(story)

    print(
        f"PDF Saved: {OUTPUT_PDF}"
    )


if __name__ == "__main__":

    merged_text = merge_markdown()

    markdown_to_pdf(
        merged_text
    )