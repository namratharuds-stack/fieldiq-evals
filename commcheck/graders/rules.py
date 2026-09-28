"""Layer 2 — Rule adherence.

The CommCheck system prompt states explicit business rules. This grader
turns each into a checkable assertion. These are deterministic: no judge
model, no subjectivity.

Assertion types:
  must_contain_card_type   — output must include a card of this type
  must_not_contain_card_type
  escalate_must_have_message — every escalate card carries an escalation_message
  no_message_on_non_escalate — non-escalate cards must not carry one
  min_card_count
  schema_valid             — placeholder, satisfied by Layer 1
  observe_only             — records behaviour without pass/fail (spec gaps)
"""


def _cards(parsed):
    outlets = parsed if isinstance(parsed, list) else [parsed]
    out = []
    for o in outlets:
        if isinstance(o, dict):
            c = o.get("cards")
            if isinstance(c, list):
                out.extend([x for x in c if isinstance(x, dict)])
    return out


def _has_message(card):
    msg = card.get("escalation_message")
    return isinstance(msg, str) and bool(msg.strip())


def grade(parsed, assertions):
    """Returns (passed, results) where results is a list of dicts."""
    cards = _cards(parsed)
    types = [c.get("type") for c in cards]
    results = []

    for a in assertions:
        kind = a.get("type")
        want = a.get("value")

        if kind == "must_contain_card_type":
            ok = want in types
            results.append({
                "assertion": f"must contain '{want}' card",
                "passed": ok,
                "observed": f"card types present: {types}",
                "scored": True,
            })

        elif kind == "must_not_contain_card_type":
            ok = want not in types
            results.append({
                "assertion": f"must NOT contain '{want}' card",
                "passed": ok,
                "observed": f"card types present: {types}",
                "scored": True,
            })

        elif kind == "escalate_must_have_message":
            esc = [c for c in cards if c.get("type") == "escalate"]
            missing = [i for i, c in enumerate(esc) if not _has_message(c)]
            ok = bool(esc) and not missing
            observed = (
                "no escalate cards produced" if not esc
                else f"{len(esc)} escalate card(s), {len(missing)} missing message"
            )
            results.append({
                "assertion": "every escalate card has escalation_message",
                "passed": ok,
                "observed": observed,
                "scored": True,
            })

        elif kind == "no_message_on_non_escalate":
            offenders = [
                c.get("type") for c in cards
                if c.get("type") != "escalate" and _has_message(c)
            ]
            ok = not offenders
            results.append({
                "assertion": "no escalation_message on non-escalate cards",
                "passed": ok,
                "observed": (
                    "clean" if ok
                    else f"message present on: {offenders}"
                ),
                "scored": True,
            })

        elif kind == "min_card_count":
            ok = len(cards) >= want
            results.append({
                "assertion": f"at least {want} card(s)",
                "passed": ok,
                "observed": f"{len(cards)} card(s) produced",
                "scored": True,
            })

        elif kind == "schema_valid":
            results.append({
                "assertion": "schema valid (see Layer 1)",
                "passed": parsed is not None,
                "observed": "parsed" if parsed is not None else "unparseable",
                "scored": True,
            })

        elif kind == "observe_only":
            present = want in types
            results.append({
                "assertion": f"[OBSERVE] does output contain '{want}'?",
                "passed": None,
                "observed": f"{'YES' if present else 'NO'} — card types: {types}",
                "scored": False,
            })

        else:
            results.append({
                "assertion": f"unknown assertion type '{kind}'",
                "passed": False,
                "observed": "grader does not implement this",
                "scored": True,
            })

    scored = [r for r in results if r["scored"]]
    passed = all(r["passed"] for r in scored) if scored else True
    return passed, results
