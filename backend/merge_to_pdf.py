import os
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet



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


def merge_markdown(output_dir):

    merged_content = []

    for section in SECTION_ORDER:

        section_file = os.path.join(
            output_dir,
            section + ".md"
        )

        if not os.path.exists(section_file):
            continue

        with open(
            section_file,
            "r",
            encoding="utf-8"
        ) as f:
            merged_content.append(f.read())

        merged_content.append("\n\n")

    merged_text = "\n".join(merged_content)

    merged_md_path = os.path.join(
        output_dir,
        "Tender_Document.md"
    )

    with open(
        merged_md_path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(merged_text)

    print(
        f"Merged Markdown Saved: {merged_md_path}"
    )

    return merged_text, merged_md_path


def markdown_to_pdf(text, pdf_path):

    doc = SimpleDocTemplate(
        pdf_path
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
        f"PDF Saved: {pdf_path}"
    )

    return pdf_path


if __name__ == "__main__":
    # Find the latest tender folder in generated_tenders
    base_dir = "generated_tenders"
    if os.path.exists(base_dir):
        subdirs = [
            os.path.join(base_dir, d)
            for d in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, d)) 
            and d.startswith("tender_")
            and any(f.endswith(".md") and f != "Tender_Document.md" for f in os.listdir(os.path.join(base_dir, d)))
        ]
        if subdirs:
            # Sort by creation time / name to get the latest
            subdirs.sort()
            latest_dir = subdirs[-1]
            print(f"Automatically selected latest tender folder for merging: {latest_dir}")

            merged_text, merged_md_path = merge_markdown(latest_dir)
            pdf_path = os.path.join(latest_dir, "Tender_Document.pdf")
            markdown_to_pdf(merged_text, pdf_path)
        else:
            print(f"No tender folders found in '{base_dir}'. Please generate a tender first.")
    else:
        print(f"Directory '{base_dir}' does not exist. Please generate a tender first.")