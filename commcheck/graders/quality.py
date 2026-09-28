"""Layer 3 — Quality (LLM-as-judge).

Layers 1, 2 and 4 check what can be asserted deterministically. They cannot
tell a card that says "discuss performance" from one that says "lead with the
Q3 volume bridge". This layer asks a judge model to score each output against
a fixed rubric, with the outlet's input signals in view so it can check that
the card is specific to *this* outlet.

The judge returns its scores through a JSON schema enforced by the API
(structured outputs), so its output is valid by construction (the lesson
from Layer 1).

Scores are 1-5. A case passes Layer 3 when every applicable criterion scores
at least PASS_FLOOR. Escalation voice is scored only when the output
contains an escalate card.

Caveat: this judge is not yet calibrated against human labels. Treat its
scores as a consistent signal for comparing prompt versions, not as ground
truth on quality.
"""

import json

PASS_FLOOR = 4

RUBRIC = """You are grading pre-visit briefing cards written for a CPG field sales rep.
The rep reads these in about 90 seconds before walking into an outlet.

Score each criterion from 1 to 5.

specificity
  5 = every card is tied to this outlet's actual signals (tier, days since visit,
      order trend, promo, contract, payment, open issue) and names a concrete action
  3 = partly specific; some generic advice a rep could get for any outlet
  1 = generic ("discuss performance", "check in with the owner")

usability
  5 = plain language a rep could say to the buyer or act on immediately; no jargon
      the rep would have to translate; short enough to read in the car
  3 = usable but wordy, or needs rephrasing before use
  1 = reads like a system report

escalation_voice (only if there is an escalate card; otherwise null)
  5 = the escalation_message sounds like the rep wrote it to their manager:
      states the issue, what the rep is doing about it, and what they need
  3 = clear but stiff or templated
  1 = reads like a system alert

Grade what is written, not what the model might have meant. Give a one-sentence
reason per criterion that quotes or points to the text you are grading."""

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "specificity": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "specificity_reason": {"type": "string"},
        "usability": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
        "usability_reason": {"type": "string"},
        "escalation_voice": {"anyOf": [{"type": "integer", "enum": [1, 2, 3, 4, 5]},
                                        {"type": "null"}]},
        "escalation_voice_reason": {"anyOf": [{"type": "string"}, {"type": "null"}]},
    },
    "required": [
        "specificity", "specificity_reason",
        "usability", "usability_reason",
        "escalation_voice", "escalation_voice_reason",
    ],
    "additionalProperties": False,
}

CRITERIA = ("specificity", "usability", "escalation_voice")


def _has_escalate(parsed):
    outlets = parsed if isinstance(parsed, list) else [parsed]
    for o in outlets:
        if isinstance(o, dict):
            for c in o.get("cards") or []:
                if isinstance(c, dict) and c.get("type") == "escalate":
                    return True
    return False


def grade(client, judge_model, case_input, parsed):
    """Returns (passed, result dict). parsed=None means Layer 1 already failed."""
    if parsed is None:
        return False, {"error": "no parseable output to judge"}

    user = (
        "Outlet signals the rep entered:\n"
        f"{json.dumps(case_input, indent=2)}\n\n"
        "Briefing cards produced:\n"
        f"{json.dumps(parsed, indent=2)}"
    )
    resp = client.messages.create(
        model=judge_model,
        max_tokens=1000,
        system=RUBRIC,
        output_config={"format": {"type": "json_schema", "schema": JUDGE_SCHEMA}},
        messages=[{"role": "user", "content": user}],
    )
    scores = json.loads(next(b.text for b in resp.content if b.type == "text"))

    # The judge decides applicability of escalation_voice from the text; we
    # decide it from the structure, so a hallucinated escalate score is ignored.
    if not _has_escalate(parsed):
        scores["escalation_voice"] = None
        scores["escalation_voice_reason"] = None

    applicable = [scores[k] for k in CRITERIA if scores.get(k) is not None]
    passed = all(s >= PASS_FLOOR for s in applicable)
    return passed, scores
