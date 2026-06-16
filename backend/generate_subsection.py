import os
import json
import time
import threading

from retrieve import build_context
from logger import logger
from openai import OpenAI

from datetime import datetime

from config import (
    PROVIDER_CHAINS,
    MODEL_NAME,
    FALLBACK_MODELS,
    MAX_INFERENCE_TOKENS,
    TIMEOUT_SEC,
)

def _make_client(provider: dict):
    """Create an OpenAI-compatible client for the given provider dict."""
    return OpenAI(
        base_url=provider["base_url"],
        api_key=provider["api_key"],
        max_retries=0,
        timeout=TIMEOUT_SEC,
    )

START_SECTION = "NOTICE INVITING TENDER"
START_SUBSECTION = "Bid Opening"

# =====================================================
# CONFIG
# =====================================================


_lazy_output_dir = None

def get_output_dir() -> str:
    global _lazy_output_dir
    if _lazy_output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _lazy_output_dir = os.path.join(
            "generated_tenders",
            f"tender_{timestamp}"
        )
        os.makedirs(
            _lazy_output_dir,
            exist_ok=True
        )
    return _lazy_output_dir
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


import re as _re
import collections as _collections

# ── Per-provider TPM token log ─────────────────────────────────────────────
_token_log: dict = _collections.defaultdict(_collections.deque)

def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 3.5))

def _parse_retry_after(error_str: str) -> float:
    m = _re.search(r"retry_after_seconds[\s:\'\"]+([0-9.]+)", error_str)
    if m:
        return float(m.group(1)) + 1.0
    m = _re.search(r"try again in ([0-9.]+)s", error_str)
    if m:
        return float(m.group(1)) + 1.0
    return 35.0

def _throttle(provider_name: str, tpm_limit: int, prompt: str, max_tokens: int) -> None:
    """Sleep proactively if we are near the TPM limit for this provider."""
    budget  = int(tpm_limit * 0.82)
    req_tok = _estimate_tokens(prompt) + max_tokens
    log     = _token_log[provider_name]
    now     = time.monotonic()
    while log and now - log[0][0] > 60:
        log.popleft()
    used = sum(t for _, t in log)
    if used + req_tok > budget and log:
        wait = 61.0 - (now - log[0][0])
        if wait > 0:
            print(f"  [throttle:{provider_name}] {used}/{budget} TPM used — sleeping {wait:.1f}s…")
            time.sleep(wait)
            now = time.monotonic()
            while log and now - log[0][0] > 60:
                log.popleft()
    _token_log[provider_name].append((time.monotonic(), req_tok))


def _call_one(client, model_name: str, prompt: str, max_tokens: int) -> str:
    """Thread-safe single model call with hard timeout."""
    result, error = [None], [None]

    def target():
        try:
            res = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=max_tokens,
            )
            result[0] = res
        except Exception as e:
            error[0] = e

    t = threading.Thread(target=target, daemon=True)
    t.start()
    deadline = time.monotonic() + TIMEOUT_SEC
    try:
        while t.is_alive():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Model {model_name} timed out after {TIMEOUT_SEC}s.")
            t.join(timeout=min(1.0, remaining))
    except KeyboardInterrupt:
        print("\n[Interrupted - exiting cleanly]")
        raise SystemExit(1)

    if error[0] is not None:
        raise error[0]
    content = result[0].choices[0].message.content
    return (content or "").strip()


def _is_complete(text: str, min_words: int = 30) -> bool:
    """
    Returns True only if the response looks like a complete tender clause output.
    Rejects truncated responses that end mid-sentence.
    """
    if not text:
        return False
    words = text.split()
    if len(words) < min_words:
        return False
    # Must end with a sentence-terminating character
    last_char = text.rstrip()[-1]
    if last_char not in ('.', '!', '?', '"', "'"):
        return False
    return True



def generate_text(prompt: str, desired_words: int) -> str:
    """
    Tries every provider → every model in the PROVIDER_CHAINS list.
    On 429, waits the exact retry-after period then retries the SAME model.
    On decommission / auth / size errors, skips to the next model/provider.
    Rotates across all providers before cycling again.
    """
    if not PROVIDER_CHAINS:
        raise RuntimeError("No API providers configured. Check your .env file.")

    max_tokens = min(MAX_INFERENCE_TOKENS, max(1024, int(desired_words * 1.5)))
    last_error = None

    for cycle in range(3):
        for provider in PROVIDER_CHAINS:
            client = _make_client(provider)
            p_name = provider["name"]
            tpm    = provider["tpm_limit"]

            for model in provider["models"]:
                for attempt in range(3):
                    try:
                        label = f"{p_name}/{model} Cycle {cycle+1}" + (f" retry {attempt}" if attempt else "")
                        print(f"\nUsing model: {label}")
                        _throttle(p_name, tpm, prompt, max_tokens)

                        res = _call_one(client, model, prompt, max_tokens)
                        if not res:
                            raise RuntimeError("Empty response.")
                        if not _is_complete(res):
                            raise RuntimeError(
                                f"Truncated response from {model} "
                                f"({len(res.split())} words, ends: '{res[-30:].strip()}')"
                            )
                        return res

                    except SystemExit:
                        raise

                    except Exception as e:
                        last_error = e
                        err_str    = str(e)
                        err_low    = err_str.lower()
                        code_m     = _re.search(r"Error code: (\d+)", err_str)
                        status     = code_m.group(1) if code_m else ""
                        print(f"  [FAIL] {err_str[:180]}")

                        # Decommissioned / invalid model → skip model
                        if status in ("404",) or (
                            status == "400" and any(k in err_low for k in [
                                "decommission", "not a valid model", "no endpoints",
                                "unavailable for free", "not found"
                            ])
                        ):
                            print(f"  -> Model invalid/decommissioned, skipping.")
                            break

                        # Auth / credits / invalid key → skip entire provider
                        if (
                            status in ("401", "402")
                            or (status == "400" and any(k in err_low for k in [
                                "invalid auth", "api key not valid", "invalid_argument",
                                "access_token_type_unsupported"
                            ]))
                        ):
                            print(f"  -> {p_name} auth/key error, skipping provider.")
                            break

                        # Too large → skip model
                        if status == "413":
                            print(f"  -> Request too large, skipping model.")
                            break

                        # Rate limit (429) -> check if quota exceeded (skip) vs TPM (wait)
                        if status == "429" or "rate limit" in err_low or "token" in err_low:
                            # Quota exhausted (daily/monthly) -> skip provider immediately
                            if "quota" in err_low or "exceeded your current quota" in err_low or "billing" in err_low:
                                print(f"  -> {p_name} quota exhausted, skipping provider immediately.")
                                break
                            # Temporary TPM rate limit -> wait and retry
                            wait = _parse_retry_after(err_str)
                            if attempt < 2:
                                print(f"  -> Rate limited. Waiting {wait:.1f}s then retrying...")
                                time.sleep(wait)
                                continue
                            else:
                                print(f"  -> Rate limited 3x on {model}, moving to next model.")
                                break

                        # 503 Service Unavailable (Gemini overload) -> immediately skip to next model
                        if status == "503" or "503" in err_str or "overloaded" in err_low or "spike" in err_low or "service unavailable" in err_low:
                            print(f"  -> Service overloaded (503), skipping {model} immediately.")
                            break

                        # Timeout → skip model
                        if "timed out" in err_low or "timeout" in err_low:
                            print(f"  -> Timeout, skipping model.")
                            break

                        # Unknown → one retry then skip
                        if attempt == 0:
                            print(f"  -> Unknown error, retrying in 5s...")
                            time.sleep(5)
                        else:
                            print(f"  -> Still failing, skipping model.")
                            break

        if cycle < 2:
            print("\n⚠ All providers exhausted this cycle. Waiting 30s before retry…")
            time.sleep(30)

    if last_error:
        raise last_error
    raise RuntimeError("All providers and models failed.")


# Legacy shim — keeps existing call sites working
def call_model(model_name, prompt, max_tokens):
    for provider in PROVIDER_CHAINS:
        if model_name in provider["models"]:
            client = _make_client(provider)
            return _call_one(client, model_name, prompt, max_tokens)
    # fallback: use first provider
    client = _make_client(PROVIDER_CHAINS[0])
    return _call_one(client, model_name, prompt, max_tokens)


# generate_text defined above in multi-provider block


# =====================================================
# WORD TARGETS
# =====================================================

DEFAULT_SUBSECTION_WORDS = 450   # ~450 words × 85 subsections ≈ 38,000 words ≈ 75 pages
MAX_WORDS_PER_SUBSECTION = 500

# =====================================================
# GENERATE SUBSECTION
# =====================================================

def get_company_stats(company_name):
    if not company_name:
        return {}

    try:
        from retrieve import metadata, company_index
    except ImportError:
        return {}

    company_lookup = {k.upper(): k for k in company_index.keys()}
    matched_key = company_lookup.get(company_name.upper())
    if not matched_key:
        return {}

    chunk_ids = company_index[matched_key]
    seen_files = set()

    estimated_values = []
    emds = []
    turnovers = []
    experiences = []
    completion_periods = []

    for idx in chunk_ids:
        if idx < 0 or idx >= len(metadata):
            continue
        meta = metadata[idx]
        file_name = meta.get("source")
        if file_name in seen_files:
            continue
        seen_files.add(file_name)

        # 1. Estimated Value
        est_val = meta.get("estimated_value")
        if est_val is not None:
            try:
                estimated_values.append(float(est_val))
            except:
                pass

        # 2. EMD
        emd_val = meta.get("emd")
        if emd_val:
            try:
                cleaned = "".join(c for c in str(emd_val) if c.isdigit() or c == ".")
                if cleaned:
                    emds.append(float(cleaned))
            except:
                pass

        # 3. Turnover
        turnover_val = meta.get("turnover")
        if turnover_val:
            try:
                cleaned = str(turnover_val).strip().rstrip(".")
                cleaned = "".join(c for c in cleaned if c.isdigit() or c == ".")
                if cleaned:
                    turnovers.append(float(cleaned))
            except:
                pass

        # 4. Experience
        exp_val = meta.get("experience")
        if exp_val:
            try:
                cleaned = "".join(c for c in str(exp_val) if c.isdigit() or c == ".")
                if cleaned:
                    experiences.append(float(cleaned))
            except:
                pass

        # 5. Completion Period
        cp_val = meta.get("completion_period")
        if cp_val:
            try:
                cleaned = "".join(c for c in str(cp_val) if c.isdigit() or c == ".")
                if cleaned:
                    completion_periods.append(float(cleaned))
            except:
                pass

    # Compute averages
    stats = {}
    if estimated_values:
        stats["estimated_value"] = sum(estimated_values) / len(estimated_values)
    if emds:
        stats["emd"] = sum(emds) / len(emds)
    if turnovers:
        stats["turnover"] = sum(turnovers) / len(turnovers)
    if experiences:
        stats["experience"] = sum(experiences) / len(experiences)
    if completion_periods:
        stats["completion_period"] = sum(completion_periods) / len(completion_periods)

    return stats


def filter_stats_for_subsection(stats, section, subsection):
    if not stats:
        return {}
    sub_lower = subsection.lower()
    filtered = {}
    
    # 1. Estimated Value (Always provided to all subsections as a global context anchor)
    if "estimated_value" in stats:
        filtered["estimated_value"] = stats["estimated_value"]
            
    # 2. EMD
    emd_keywords = ["emd", "security", "deposit", "guarantee", "tender schedule", "bid submission"]
    if any(k in sub_lower for k in emd_keywords):
        if "emd" in stats:
            filtered["emd"] = stats["emd"]
            
    # 3. Turnover
    turnover_keywords = ["turnover", "financial", "eligibility", "annual", "tender schedule", "introduction"]
    if any(k in sub_lower for k in turnover_keywords):
        if "turnover" in stats:
            filtered["turnover"] = stats["turnover"]
            
    # 4. Experience
    experience_keywords = ["experience", "eligibility", "technical", "qualification", "work", "tender schedule", "introduction"]
    if any(k in sub_lower for k in experience_keywords):
        if "experience" in stats:
            filtered["experience"] = stats["experience"]
            
    # 5. Completion Period
    period_keywords = [
        "period", "delivery", "completion", "duration", "time", "delay", 
        "penalty", "liquidated", "timeline", "tender schedule"
    ]
    if any(k in sub_lower for k in period_keywords):
        if "completion_period" in stats:
            filtered["completion_period"] = stats["completion_period"]
            
    return filtered


def format_company_stats_prompt(company_name, stats):
    if not stats:
        return ""
    
    prompt_lines = [
        f"ESTIMATED/REPRESENTATIVE VALUES FOR '{company_name.upper()}' FROM THE DATASET:",
        "Use these estimated values for any clauses requiring specific numerical/financial values if they are not explicitly present in the retrieved context:"
    ]
    
    if "estimated_value" in stats:
        val = int(stats["estimated_value"])
        prompt_lines.append(f"- Estimated Tender Value: Rs. {val:,} (approximately Rs. {val/10000000:.2f} Crores)")
    if "emd" in stats:
        val = int(stats["emd"])
        prompt_lines.append(f"- Earnest Money Deposit (EMD): Rs. {val:,}")
    if "turnover" in stats:
        val = stats["turnover"]
        prompt_lines.append(f"- Minimum Annual Turnover Requirement: Rs. {val:.2f} Crores")
    if "experience" in stats:
        val = int(stats["experience"])
        prompt_lines.append(f"- Minimum Work Experience Required: {val} years")
    if "completion_period" in stats:
        val = int(stats["completion_period"])
        prompt_lines.append(f"- Contract/Completion Period: {val} Days")
        
    return "\n" + "\n".join(prompt_lines) + "\n"


def generate_subsection(
        requirement,
        section,
        subsection,
        target_words=DEFAULT_SUBSECTION_WORDS,
        company=None,
        previous_subsections=None
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
    company=company,
    top_k=20
    )

    if len(context) > 16000:
        context = context[:16000]

    logger.info(
        f"Context Length: {len(context)}"
    )

    # Calculate, filter and format company statistics based on the dataset
    company_stats = get_company_stats(company)
    filtered_stats = filter_stats_for_subsection(company_stats, section, subsection) if company else {}
    company_stats_section = format_company_stats_prompt(company, filtered_stats) if filtered_stats else ""

    # Build previously generated subsections context to prevent repetition
    prev_context = ""
    if previous_subsections:
        prev_lines = ["ALREADY GENERATED SUBSECTIONS (DO NOT REPEAT ANY OF THIS CONTENT):"]
        for prev_name, prev_summary in previous_subsections:
            prev_lines.append(f"- {prev_name}: {prev_summary}")
        prev_context = "\n".join(prev_lines)

    prompt = f"""
You are a senior PSU/SAIL tender drafting consultant with deep expertise in Indian public sector procurement language, NIT formats, and GFR compliance.

────────────────────────────────────────
PROJECT REQUIREMENT
{requirement}

COMPANY STATISTICS (authoritative source — use these directly as numerical values)
{company_stats_section}

SECTION       : {section}
SUBSECTION    : {subsection}

PREVIOUS SUBSECTIONS ALREADY DRAFTED (DO NOT REPEAT ANY POINT FROM THESE)
{prev_context}

RETRIEVED TENDER CONTEXT (secondary numerical source)
{context}
────────────────────────────────────────

TASK
Draft ONLY the subsection "{subsection}" in formal PSU/SAIL NIT language.
Target word count: approximately {target_words} words.
Write as many or as few numbered clauses as needed to reach the word target — there
is NO fixed clause count. Stop when all key requirements are covered AND the word
target is approximately met. Each clause should be substantive (40-80 words each).

════════════════════════════════════════
NUMERICAL DATA RULES  (highest priority)
════════════════════════════════════════

N1. Every financial figure (EMD, turnover, tender value, performance security, penalty
    rates, payment milestones), duration (completion period, DLP, warranty), and
    threshold (experience years, quantity) MUST be taken from either:
      (a) the COMPANY STATISTICS block above, or
      (b) the RETRIEVED TENDER CONTEXT block above.
    If the same figure appears in both, prefer COMPANY STATISTICS.

N2. The following phrases are ABSOLUTELY BANNED. Using any of them will make the
    output invalid. Replace each with the actual value from the data sources:
      BANNED: "specified in the tender schedule"
      BANNED: "specified in the tender document"
      BANNED: "as per terms and conditions"
      BANNED: "as specified"
      BANNED: "to be decided"
      BANNED: "as applicable"
      BANNED: "suitable value"
      BANNED: "adequate amount"
      BANNED: "as mutually agreed"
      BANNED: "on the date and time specified"
      BANNED: "by the competent authority"
      BANNED: "as per schedule"
      BANNED: "notified separately"
      BANNED: "intimated separately"
      BANNED: "shall be communicated"  (unless a specific date follows immediately)
    If a value exists in either data source — write it explicitly. No exceptions.

N3. If a specific value is genuinely absent from BOTH data sources, derive a
    reasonable industry-standard estimate based on the Estimated Tender Value and
    PSU norms (e.g., EMD = 2% of ETV, Performance Security = 10% of contract value,
    Turnover >= 2x annual contract value). State the derived value with the note
    "(estimated as per PSU norms)" — do NOT leave it blank or use placeholder text.

N4. Embed the Estimated Tender Value (ETV) naturally in the clause where it is most
    relevant (e.g., inside the clause describing bid value, EMD amount, or contract scope).
    Do NOT create a standalone clause 1 that only states the ETV.
    Do NOT repeat the ETV in more than one clause.

N5. DATES AND TIMES are mandatory specific values. For any clause mentioning bid opening,
    submission deadline, or price bid opening:
    - Use the actual date from the RETRIEVED TENDER CONTEXT (e.g., "14.03.2026 at 14:00 hours")
    - If no date is in the context, use a realistic future date "(estimated as per PSU norms)"
    - NEVER write "on a date to be notified", "on the scheduled date", or any vague date reference.

════════════════════════════════════════
CONTENT & LANGUAGE RULES
════════════════════════════════════════

C1. Write in PSU/SAIL NIT clause style: formal, numbered, third-person, imperative.

C2. This subsection must cover ONLY aspects that are UNIQUE to "{subsection}".
    STRICTLY DO NOT repeat any of the following if they have already appeared in
    PREVIOUS SUBSECTIONS:
    - Bid submission deadline dates/times
    - EMD amount or mode
    - ETV / tender value
    - Bidder eligibility / turnover / experience criteria
    - Two-part bid structure (Techno-Commercial + Price Bid)
    Check the PREVIOUS SUBSECTIONS block above and skip any point already covered.

C3. Do NOT force standard boilerplate headings unrelated to "{subsection}".

C4. Unless the subsection topic inherently requires them, avoid repeating:
    Compliance | Documentation | Inspection | Testing | Acceptance criteria

C5. Each numbered clause must introduce a DISTINCT point.
    No two clauses may restate the same requirement in different wording.

C6. Stop generating once all key requirements for "{subsection}" are covered.
    Do not pad clauses to reach the word target.

C7. DO NOT repeat the full procurement title ("Procurement of Alumina Magnesia Spinel
    Bricks for SMS – II Ladle application of Bokaro Steel Plant") in every clause.
    Refer to it as "this procurement", "the contract", or "the subject work" after
    the first mention.

C8. Each clause must START with a unique action verb or subject that is different
    from clause 1. Examples: "The bid opening committee...", "Authorized
    representatives...", "Only sealed bids...", "Late submissions..."
    NEVER start multiple clauses with "The [thing] for the procurement of...".

════════════════════════════════════════
OUTPUT FORMAT RULES
════════════════════════════════════════

O1. Return tender clause text only.
O2. Begin directly with clause "1." — no preamble, no heading, no title.
O3. Do not include explanations, commentary, or meta-text.
O4. Do not write "Here is...", "Let me...", "Note that...", or any conversational text.
O5. Write as many clauses as needed to reach the {target_words}-word target.
    Do NOT stop early just because a topic feels covered — expand on sub-points,
    procedural steps, and conditions until the word count is met.
    Do NOT pad with repetition — each additional clause must add new information.
O6. Every clause must be complete and end with a full stop. Never truncate mid-sentence.

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
        content,
        output_dir=None
):

    target_dir = output_dir if output_dir else get_output_dir()
    filename = os.path.join(
        target_dir,
        section.replace(" ", "_") + ".md"
    )

    # Initialize the file with a section heading if it doesn't exist
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# {section}\n\n")

    # Append the subsection heading and content
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"## {subsection}\n\n")
        f.write(f"{content}\n\n")

    print(
        f"\nAdded subsection '{subsection}' -> {filename}"
    )

# =====================================================
# GENERATE FROM PLAN
# =====================================================

def generate_from_plan(
        plan_file="tender_plan.json",
        output_dir=None
):

    reached_start = False

    # Dynamically generate output directory if not passed, to avoid static global timestamp reuse
    if not output_dir:
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("generated_tenders", f"tender_{run_timestamp}")

    os.makedirs(output_dir, exist_ok=True)
    print(f"\nSaving generated tender sections directly into: {output_dir}")

    with open(
        plan_file,
        "r",
        encoding="utf-8"
    ) as f:

        plan = json.load(f)

    requirement = plan["requirement"]
    company = plan.get("company")

    for section_data in plan["sections"]:

        section = section_data["title"]

        target_words = section_data.get(
            "target_words",
            3500   # ~3500 words per section / ~7 subsections = ~500 words each
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
            420,   # floor: never less than 420 words (keeps pages balanced)
            min(500, subsection_target)  # cap at 500 to avoid over-shooting
        )

        print("\n" + "=" * 120)
        print(f"SECTION: {section}")
        print(f"Subsection Target: {subsection_target}")
        print("=" * 120)

        # Track previously generated subsections within this section to prevent repetition
        generated_in_section = []

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

                     target_words=subsection_target,

                     company=company,

                     previous_subsections=generated_in_section

                )

                # Store the FULL generated content (first 300 words) to pass to next subsection
                summary = " ".join(content.split()[:300])
                generated_in_section.append((subsection, summary))

                save_subsection(

                     section,

                     subsection,

                     content,

                     output_dir=output_dir

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
    from planner import create_tender_plan, save_plan
    import sys

    print(
        "\nStarting Tender Generation..."
    )

    PLAN_FILE = "tender_plan.json"

    if os.path.exists(PLAN_FILE):
        print(f"INFO: Found existing plan file '{PLAN_FILE}'.")
        use_existing = input("Use existing plan? (y/n, default y): ").strip().lower()
        if use_existing == "n":
            os.remove(PLAN_FILE)
            print("Deleted existing plan file.")

    if not os.path.exists(PLAN_FILE):
        requirement = input("\nEnter Tender Query: ").strip()
        if not requirement:
            requirement = "Procurement of Alumina Magnesia Spinel Bricks for SMS - II Ladle application of Bokaro Steel Plant, Bokaro."
            print(f"Using default: {requirement}")

        company = input("Enter Company (e.g. SAIL, NTPC, BHEL): ").strip()
        if not company:
            company = "SAIL"
            print(f"Using default: {company}")

        print(f"\nCreating plan for: {requirement} (Company: {company})")
        plan = create_tender_plan(requirement, company=company)
        save_plan(plan, output_file=PLAN_FILE)
        print(f"Plan saved to '{PLAN_FILE}'.")
    else:
        print("(Note: To generate a new plan, run 'python planner.py' or delete 'tender_plan.json')\n")

    generate_from_plan(plan_file=PLAN_FILE)