import os
import json
import time

from retrieve import build_context
from logger import logger
from openai import OpenAI

from datetime import datetime

from config import (
    OPENROUTER_API_KEY,
    MODEL_NAME,
    FALLBACK_MODELS,
    MAX_INFERENCE_TOKENS
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

START_SECTION = "NOTICE INVITING TENDER"
START_SUBSECTION = "Introduction"

# =====================================================
# CONFIG
# =====================================================


timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

OUTPUT_DIR = os.path.join(
    "generated_tenders",
    f"tender_{timestamp}",
    "subsections"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)
def sanitize_text(text: str) -> str:
    if not text:
        return text
    
    # Map common chemistry formulas with dots/squares/subscripts to standard representations
    text = text.replace("Al■O■", "Al2O3")
    text = text.replace("Al\u25a0O\u25a0", "Al2O3")
    text = text.replace("Fe■O■", "Fe2O3")
    text = text.replace("Fe\u25a0O\u25a0", "Fe2O3")
    text = text.replace("SiO■", "SiO2")
    text = text.replace("SiO\u25a0", "SiO2")
    text = text.replace("TiO■", "TiO2")
    text = text.replace("TiO\u25a0", "TiO2")
    text = text.replace("ZrO■", "ZrO2")
    text = text.replace("ZrO\u25a0", "ZrO2")
    
    # Map Unicode subscripts/superscripts to standard readable digits
    mapping = {
        "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
        "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
        "•": "-", "■": "", "": "", "": "", "\uf0b7": "", "\uf02d": "-", "\uf0fc": "x", "\uf0a8": "<-"
    }
    for k, v in mapping.items():
        text = text.replace(k, v)
    
    # Strip any custom private use area characters (U+E000 to U+F8FF)
    cleaned = []
    for char in text:
        if 0xE000 <= ord(char) <= 0xF8FF:
            continue
        cleaned.append(char)
    return "".join(cleaned)


def call_model(
        model_name,
        prompt,
        max_tokens
):

    response = client.chat.completions.create(

        model=model_name,

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.1,

        max_tokens=max_tokens

    )

    return (
        response
        .choices[0]
        .message
        .content
        .strip()
    )


def generate_text(
        prompt,
        desired_words
):

    models = [MODEL_NAME] + FALLBACK_MODELS

    max_tokens = min(
        MAX_INFERENCE_TOKENS,
        max(
            1024,
            int(desired_words * 1.5)
        )
    )

    last_error = None

    for model in models:

        for attempt in range(5):

            try:

                print(
                    f"\nUsing model: {model}"
                )

                return call_model(

                    model_name=model,

                    prompt=prompt,

                    max_tokens=max_tokens

                )

            except Exception as e:

                last_error = e

                error_message = str(e)

                print(
                    f"\nModel {model} failed:"
                )

                print(
                    error_message
                )

                if (
                    "rate limit" in error_message.lower()
                    or "429" in error_message
                ):

                    wait_time = min(
                        120,
                        30 * (attempt + 1)
                    )

                    print(
                        f"\nRetrying in {wait_time} seconds..."
                    )

                    time.sleep(
                        wait_time
                    )

                    continue

                break

    if last_error:
        raise last_error

    raise RuntimeError(
        "No model available."
    )

# =====================================================
# WORD TARGETS
# =====================================================

DEFAULT_SUBSECTION_WORDS = 600
MAX_WORDS_PER_SUBSECTION = 250

# =====================================================
# GENERATE SUBSECTION
# =====================================================

def generate_subsection(
        requirement,
        section,
        subsection,
        target_words=DEFAULT_SUBSECTION_WORDS
):

    logger.info("=" * 120)

    logger.info(
        f"SECTION: {section}"
    )

    logger.info(
        f"SUBSECTION: {subsection}"
    )

    retrieval_query = f"""
Tender Requirement:

{requirement}

Section:

{section}

Subsection:

{subsection}
"""

    print(
        "\nRetrieving Context..."
    )

    context = build_context(
    query=retrieval_query,
    section_name=section,
    top_k=12
    )

    if len(context) > 12000:
        context = context[:12000]

    logger.info(
        f"Context Length: {len(context)}"
    )

    prompt = f"""
You are a senior SAIL tender drafting consultant.

PROJECT REQUIREMENT

{requirement}

SECTION

{section}

SUBSECTION

{subsection}

REFERENCE TENDER CONTEXT

{context}

TASK

Generate only the subsection.

MANDATORY RULES

1. Use PSU / SAIL tender language.

2. Use clause numbering.

3. Generate industrial tender content.

4. Use retrieved context.

5. Do NOT invent:

- Turnover values
- Experience years
- EMD
- Security Deposit
- Performance Guarantee
- Quantities
- Delivery Periods

6. Any numerical value not explicitly present in retrieved context is prohibited.

7. If information is unavailable write:

"To be specified in the tender schedule."

8. Generate approximately {target_words} words.

9. Generate only content relevant to the subsection.

10. Do NOT force standard tender headings.

11. Avoid repeating:
- Requirements
- Compliance
- Documentation
- Inspection
- Testing
- Acceptance

unless naturally required.

13. Create unique content for each subsection.

14. Be concise and avoid repetition.

15. Return only tender content.

16. Return only tender content.
Do not include explanations.
Do not include conversational text.
Do not say "Here is..."
Do not say "Let me know..."

17. Do not exceed 10 numbered clauses.
Do not repeat any clause using different wording.
Stop when all key requirements are covered.

18. Generate between 150 and 250 words only.
Maximum 10 clauses.
Avoid repetition.
Do not repeat previously stated requirements.

Generate now.
"""

    print(
        "\nGenerating Section..."
    )

    generated_text = ""

    remaining_words = target_words

    max_passes = 1

    for pass_index in range(max_passes):

        prompt_text = prompt

        if generated_text:

            seed = " ".join(
                generated_text.split()[-150:]
            )

            prompt_text = f"""
Continue the tender subsection.

PREVIOUS CONTENT END

{seed}

Requirements:

1. Continue numbering correctly.
2. Maintain tender language.
3. Do not repeat content.
4. Add approximately {remaining_words} words.
5. Return only tender content.
"""

        try:

            output = generate_text(
                prompt_text,
                remaining_words
            )

        except Exception as e:

            logger.error(
                str(e)
            )

            print(
                f"\nError: {e}"
            )

            raise

        if not output:
            break

        if generated_text:

            generated_text += (
                "\n\n" +
                output.strip()
            )

        else:

            generated_text = (
                output.strip()
            )

        current_word_count = len(
            generated_text.split()
        )

        logger.info(
            f"Generated Length: {current_word_count}"
        )

        remaining_words = max(
            0,
            target_words - current_word_count
        )

        if remaining_words == 0:
            break

        if len(output.split()) < 150:
            break

    if not generated_text:

        raise RuntimeError(
            "No text was generated."
        )

    return sanitize_text(generated_text)

# =====================================================
# SAVE SUBSECTION
# =====================================================

def save_subsection(
        section,
        subsection,
        content
):

    section_dir = os.path.join(
        OUTPUT_DIR,
        section.replace(
            " ",
            "_"
        )
    )

    os.makedirs(
        section_dir,
        exist_ok=True
    )

    filename = os.path.join(

        section_dir,

        subsection
        .replace("/", "_")
        .replace(" ", "_")
        + ".md"
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(content)

    print(
        f"\nSaved: {filename}"
    )

# =====================================================
# GENERATE FROM PLAN
# =====================================================

def generate_from_plan(
        plan_file="tender_plan.json"
):

    reached_start = False

    with open(
        plan_file,
        "r",
        encoding="utf-8"
    ) as f:

        plan = json.load(f)

    requirement = plan["requirement"]

    for section_data in plan["sections"]:

        section = section_data["title"]

        target_words = section_data.get(
            "target_words",
            3000
        )

        subsections = section_data["subsections"]

        subsection_target = int(
            target_words /
            max(
            1,
            len(subsections)
            )
        )

        subsection_target = max(
            400,
            subsection_target
        )

        print("\n" + "=" * 120)
        print(f"SECTION: {section}")
        print(f"Subsection Target: {subsection_target}")
        print("=" * 120)

        for subsection in subsections:

            if not reached_start:

                if (
                    section == START_SECTION
                    and subsection == START_SUBSECTION
                ):
                    reached_start = True

                else:

                    print(
                        f"Skipping: {section} -> {subsection}"
                    )

                    continue

            try:

                content = generate_subsection(

                    requirement=requirement,

                    section=section,

                    subsection=subsection,

                    target_words=subsection_target

                )

                save_subsection(

                    section,

                    subsection,

                    content

                )

            except Exception as e:

                logger.error(
                    f"{section} | {subsection}"
                )

                logger.error(
                    str(e)
                )

                print(
                    f"\nFailed: {subsection}"
                )

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    print(
        "\nStarting Tender Generation..."
    )

    generate_from_plan()