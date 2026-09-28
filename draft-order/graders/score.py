"""Draft Order Agent — grading logic.

Scoring model
-------------
Quantities are scored against an explicit per-case BAND (qty_min..qty_max)
set by hand adjudication, because several orders can be right. A void-fill
trial order and a velocity reorder tolerate different error, so a single
percentage tolerance would be wrong for both.

Reason codes and safety behaviour are EXACT MATCH. There is no partial
credit for calling a void a velocity reorder.

Criticality is a property of the CHECK, not the case. These three are
critical wherever they occur:

  - unauthorized_sku   : recommending a SKU outside the outlet assortment
  - moq_violation      : total order below the chain minimum (un-submittable)
  - missing_escalation : silently resolving conflicting or absent data

A critical failure fails the case outright and cannot be bought back by
correct quantities elsewhere. This mirrors the field consequence: one
unorderable line costs the rep trust in every other line on the sheet.

Ship gate: zero critical failures AND >= 90% pass.
"""

CRITICAL_CHECKS = {"unauthorized_sku", "moq_violation", "missing_escalation"}

PASS_THRESHOLD = 0.90


def _find_case(cases, case_id):
    for c in cases:
        if c["id"] == case_id:
            return c
    return None


def grade_case(case, pred):
    """Grade one prediction against one golden case.

    Returns dict with: case_id, passed, critical_failure, checks[]
    """
    exp = case.get("expect", {})
    checks = []

    pred_lines = pred.get("lines", [])
    pred_escalated = bool(pred.get("escalated", False))
    pred_skus = [l.get("sku") for l in pred_lines]

    authorized = set(case.get("authorized_skus", []))

    # ---- CRITICAL: unauthorized SKU -------------------------------------
    unauthorized_hits = [s for s in pred_skus if s not in authorized]
    explicit_forbidden = set(exp.get("must_not_include_skus", []))
    forbidden_hits = [s for s in pred_skus if s in explicit_forbidden]
    bad_skus = sorted(set(unauthorized_hits) | set(forbidden_hits))

    checks.append({
        "check": "unauthorized_sku",
        "critical": True,
        "passed": not bad_skus,
        "detail": "clean" if not bad_skus else f"recommended outside assortment: {bad_skus}",
    })

    # ---- CRITICAL: escalation behaviour ---------------------------------
    if exp.get("must_escalate"):
        ok = pred_escalated and not pred_lines
        checks.append({
            "check": "missing_escalation",
            "critical": True,
            "passed": ok,
            "detail": (
                "escalated correctly" if ok
                else f"expected escalation; got escalated={pred_escalated}, "
                     f"{len(pred_lines)} line(s)"
            ),
        })
    elif exp.get("must_not_escalate"):
        checks.append({
            "check": "spurious_escalation",
            "critical": False,
            "passed": not pred_escalated,
            "detail": "no escalation" if not pred_escalated else "escalated when it should not have",
        })

    # ---- CRITICAL: chain MOQ --------------------------------------------
    moq = exp.get("order_moq_cases")
    if moq is not None and pred_lines:
        total = sum(l.get("quantity", 0) for l in pred_lines)
        ok = total >= moq
        checks.append({
            "check": "moq_violation",
            "critical": True,
            "passed": ok,
            "detail": f"order total {total} cases vs chain MOQ {moq}",
        })

    # ---- Expected lines: presence, reason code, quantity band -----------
    for e in exp.get("lines", []):
        sku = e["sku"]
        match = next((l for l in pred_lines if l.get("sku") == sku), None)

        if match is None:
            checks.append({
                "check": f"line_present[{sku}]",
                "critical": False,
                "passed": False,
                "detail": "expected line missing from order",
            })
            continue

        checks.append({
            "check": f"line_present[{sku}]",
            "critical": False,
            "passed": True,
            "detail": "present",
        })

        # reason code — exact match
        want_reason = e.get("reason_type")
        got_reason = match.get("reason_type")
        checks.append({
            "check": f"reason_code[{sku}]",
            "critical": False,
            "passed": got_reason == want_reason,
            "detail": f"expected {want_reason}, got {got_reason}",
        })

        # quantity band
        qty = match.get("quantity", 0)
        lo, hi = e.get("qty_min"), e.get("qty_max")
        if lo is not None and hi is not None:
            checks.append({
                "check": f"qty_band[{sku}]",
                "critical": False,
                "passed": lo <= qty <= hi,
                "detail": f"qty {qty} vs band {lo}-{hi}",
            })

        # pack rounding
        pack = e.get("pack_multiple")
        if pack:
            checks.append({
                "check": f"pack_rounding[{sku}]",
                "critical": False,
                "passed": qty % pack == 0,
                "detail": f"qty {qty} vs pack multiple {pack}",
            })

    # ---- Velocity cap ----------------------------------------------------
    cap_mult = exp.get("velocity_cap_multiple")
    if cap_mult:
        for sig in case.get("signals", []):
            v = sig.get("weekly_velocity")
            if not v:
                continue
            match = next((l for l in pred_lines if l.get("sku") == sig["sku"]), None)
            if match:
                cap = v * cap_mult
                qty = match.get("quantity", 0)
                checks.append({
                    "check": f"velocity_cap[{sig['sku']}]",
                    "critical": False,
                    "passed": qty <= cap,
                    "detail": f"qty {qty} vs cap {cap} ({cap_mult}x velocity {v})",
                })

    # ---- Cases expecting an empty order ---------------------------------
    if exp.get("lines") == [] and not exp.get("must_escalate"):
        forbidden = set(exp.get("must_not_include_skus", []))
        if forbidden:
            hit = [s for s in pred_skus if s in forbidden]
            checks.append({
                "check": "no_order_expected",
                "critical": False,
                "passed": not hit,
                "detail": "correctly held" if not hit else f"ordered {hit} when no order was warranted",
            })

    critical_failure = any(
        c["critical"] and not c["passed"] for c in checks
    )
    passed = all(c["passed"] for c in checks)

    return {
        "case_id": case["id"],
        "category": case.get("category"),
        "description": case.get("description", ""),
        "passed": passed,
        "critical_failure": critical_failure,
        "checks": checks,
    }


def grade_all(cases, predictions):
    results = []
    for pred in predictions:
        case = _find_case(cases, pred["case_id"])
        if case is None:
            results.append({
                "case_id": pred["case_id"],
                "passed": False,
                "critical_failure": False,
                "checks": [{"check": "case_lookup", "critical": False,
                            "passed": False, "detail": "no matching golden case"}],
            })
            continue
        results.append(grade_case(case, pred))
    return results


def gate(results):
    """Ship gate: zero critical failures AND >= 90% pass."""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    criticals = sum(1 for r in results if r["critical_failure"])
    rate = passed / total if total else 0.0
    return {
        "total": total,
        "passed": passed,
        "pass_rate": rate,
        "critical_failures": criticals,
        "gate": "PASS" if (criticals == 0 and rate >= PASS_THRESHOLD) else "FAIL",
    }
