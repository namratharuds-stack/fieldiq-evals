"""Layer 1 — Structural validity.

Checks that CommCheck output is parseable JSON conforming to the
declared schema. This is the smoke test: anything below 100% here
is a hard failure, because downstream graders cannot run on
malformed output.
"""

import json
import re

VALID_CARD_TYPES = {"act_today", "escalate", "opportunity"}
REQUIRED_CARD_FIELDS = {"type", "risk_summary", "action"}


def extract_json(raw: str):
    """The prompt says 'return ONLY valid JSON', but models sometimes
    wrap output in markdown fences or add preamble. We strip those
    before parsing — but we RECORD that we had to, because needing
    to strip is itself a spec violation worth measuring."""
    had_to_clean = False
    text = raw.strip()

    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
        had_to_clean = True

    if not text.startswith(("{", "[")):
        start = min(
            (i for i in (text.find("{"), text.find("[")) if i != -1),
            default=-1,
        )
        if start > 0:
            text = text[start:]
            had_to_clean = True

    try:
        return json.loads(text), had_to_clean, None
    except json.JSONDecodeError as e:
        return None, had_to_clean, str(e)


def grade(raw_output: str):
    """Returns (passed: bool, findings: list[str], parsed: obj|None)."""
    findings = []
    parsed, had_to_clean, err = extract_json(raw_output)

    if parsed is None:
        return False, [f"JSON parse failed: {err}"], None

    if had_to_clean:
        findings.append(
            "SPEC VIOLATION: output required cleaning (markdown fence or preamble) "
            "despite 'Return ONLY valid JSON' instruction"
        )

    # Normalise: spec shows a single object, but multi-outlet calls
    # return an array. Accept both.
    outlets = parsed if isinstance(parsed, list) else [parsed]

    for idx, outlet in enumerate(outlets):
        prefix = f"outlet[{idx}]"

        if not isinstance(outlet, dict):
            findings.append(f"{prefix}: not an object")
            continue

        if "outlet_name" not in outlet:
            findings.append(f"{prefix}: missing 'outlet_name'")
        if "tier" not in outlet:
            findings.append(f"{prefix}: missing 'tier'")

        cards = outlet.get("cards")
        if not isinstance(cards, list):
            findings.append(f"{prefix}: 'cards' missing or not a list")
            continue

        for cidx, card in enumerate(cards):
            cprefix = f"{prefix}.cards[{cidx}]"

            if not isinstance(card, dict):
                findings.append(f"{cprefix}: not an object")
                continue

            missing = REQUIRED_CARD_FIELDS - set(card.keys())
            if missing:
                findings.append(f"{cprefix}: missing fields {sorted(missing)}")

            ctype = card.get("type")
            if ctype not in VALID_CARD_TYPES:
                findings.append(
                    f"{cprefix}: invalid type {ctype!r} "
                    f"(expected one of {sorted(VALID_CARD_TYPES)})"
                )

            for field in ("risk_summary", "action"):
                val = card.get(field)
                if isinstance(val, str) and not val.strip():
                    findings.append(f"{cprefix}: '{field}' is empty")

    hard_failures = [f for f in findings if "SPEC VIOLATION" not in f]
    return len(hard_failures) == 0, findings, parsed
