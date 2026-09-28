#!/usr/bin/env python3
"""Draft Order Agent — eval scorer.

Two modes:

  Fixture (default) — score a stored predictions file. No API calls, free,
  deterministic. Used to prove the graders catch known failure modes.

      python score_draft_orders.py
      python score_draft_orders.py --predictions fixtures/seeded_agent_v1.json

  Live — call the Draft Order Agent prompt against each golden case and
  score whatever comes back. Requires ANTHROPIC_API_KEY.

      export ANTHROPIC_API_KEY=sk-ant-...
      python score_draft_orders.py --live

Ship gate: zero critical failures AND >= 90% pass.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from graders import score as scorer

ROOT = Path(__file__).parent
MODEL = "claude-sonnet-4-6"

LIVE_SYSTEM = """You are the FieldIQ Draft Order Agent. You prepare recommended orders for CPG field sales reps before an outlet visit.

Rules:
- Only recommend SKUs in the outlet's authorized assortment. Never recommend an unauthorized SKU.
- Quantity = projected need over the coverage window, minus on-hand, rounded UP to the pack multiple.
- If a promo ended recently, damp inflated velocity back toward baseline before projecting.
- If the total order falls below the chain MOQ, raise it to meet the MOQ.
- Never exceed 4x weekly velocity on any line.
- If velocity or on-hand is missing, or signals contradict each other, DO NOT guess. Escalate.
- New outlets with no history: use half the benchmark velocity as a trial quantity.

reason_type must be exactly one of: velocity_reorder, contract_gap, promo_requirement, whitespace_opportunity

Return ONLY a JSON object:
{"escalated": bool, "lines": [{"sku": "string", "quantity": number, "reason_type": "string"}]}

If escalating, return escalated true and an empty lines array."""


def load_cases():
    data = json.loads((ROOT / "cases" / "golden_set.json").read_text())
    return data["cases"]


def build_user_message(case):
    o = case["outlet"]
    lines = [
        f"Outlet: {o['name']} | Tier: {o['tier']} | Chain MOQ: {o['chain_moq_cases']} cases",
        f"MTD: ${o['salesMTD']} of ${o['salesTarget']} target",
        "",
        f"Authorized assortment: {', '.join(case['authorized_skus'])}",
        f"NOT authorized at this outlet: {', '.join(case.get('unauthorized_skus', [])) or 'none'}",
        "",
        "Signals:",
    ]
    for s in case["signals"]:
        parts = [f"  {s['sku']}:"]
        for k in ("weekly_velocity", "baseline_velocity", "on_hand", "pack",
                  "coverage_weeks", "benchmark_velocity", "days_oos",
                  "promo_ended_days_ago"):
            if k in s:
                parts.append(f"{k}={s[k]}")
        for flag in ("promo_active", "new_outlet", "authorized_not_stocked",
                     "signal_conflict", "benchmark_format_mismatch", "unauthorized"):
            if s.get(flag):
                parts.append(f"{flag}=true")
        lines.append(" ".join(parts))
    return "\n".join(lines)


def run_live(cases):
    try:
        import anthropic
    except ImportError:
        sys.exit("Missing dependency. Run: pip install anthropic")

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit(
            "ANTHROPIC_API_KEY not set.\n"
            "  export ANTHROPIC_API_KEY=sk-ant-..."
        )

    client = anthropic.Anthropic(api_key=key)
    preds = []

    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['id']} ... ", end="", flush=True)
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=1500,
                system=LIVE_SYSTEM,
                messages=[{"role": "user", "content": build_user_message(case)}],
                # Prefill forces generation to begin inside the JSON object.
                # This is the structural fix for the format-drift finding from
                # the CommCheck eval suite.
            )
            raw = "".join(
                b.text for b in resp.content if getattr(b, "type", "") == "text"
            )
            txt = raw.strip()
            if txt.startswith("```"):
                txt = txt.split("```")[1]
                if txt.startswith("json"):
                    txt = txt[4:]
                txt = txt.strip()
            obj = json.loads(txt)
            obj["case_id"] = case["id"]
            preds.append(obj)
            print("ok")
        except Exception as e:
            print(f"ERROR ({e})")
            preds.append({"case_id": case["id"], "escalated": False,
                          "lines": [], "_error": str(e)})

    return preds


def write_report(results, summary, source_label):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = ROOT / "reports"
    outdir.mkdir(exist_ok=True)

    (outdir / f"scorecard_{ts}.json").write_text(
        json.dumps({"summary": summary, "results": results}, indent=2)
    )

    L = [
        "# Draft Order Agent — Eval Scorecard",
        "",
        f"- **Agent under test:** {source_label}",
        f"- **Golden set:** 26 cases, 13 categories",
        f"- **Run:** {ts}",
        "",
        "## Gate",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Cases passed | {summary['passed']} / {summary['total']} ({summary['pass_rate']*100:.0f}%) |",
        f"| Critical failures | {summary['critical_failures']} |",
        f"| Threshold | 0 critical AND >= 90% pass |",
        f"| **Result** | **gate: {summary['gate']}** |",
        "",
    ]

    fails = [r for r in results if not r["passed"]]
    L += ["## Failures", ""]
    if not fails:
        L.append("_None._")
    else:
        L += ["| Case | Category | Failure | Critical |", "|---|---|---|---|"]
        for r in fails:
            bad = [c for c in r["checks"] if not c["passed"]]
            for c in bad:
                flag = "🔴 Yes" if c["critical"] else "—"
                L.append(f"| {r['case_id']} | {r.get('category','')} | {c['check']}: {c['detail']} | {flag} |")
    L.append("")

    # per-category breakdown
    cats = {}
    for r in results:
        c = r.get("category", "unknown")
        cats.setdefault(c, [0, 0])
        cats[c][1] += 1
        if r["passed"]:
            cats[c][0] += 1

    L += ["## By category", "", "| Category | Passed | Total |", "|---|---|---|"]
    for c in sorted(cats):
        p, t = cats[c]
        L.append(f"| {c} | {p} | {t} |")
    L.append("")

    path = outdir / f"scorecard_{ts}.md"
    path.write_text("\n".join(L))
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions", default="fixtures/seeded_agent_v1.json")
    ap.add_argument("--live", action="store_true",
                    help="Call the agent instead of loading a fixture")
    args = ap.parse_args()

    cases = load_cases()

    if args.live:
        source = f"live ({MODEL})"
        preds = run_live(cases)
    else:
        data = json.loads((ROOT / args.predictions).read_text())
        source = data.get("agent_version", args.predictions) + " (fixture)"
        preds = data["predictions"]

    results = scorer.grade_all(cases, preds)
    summary = scorer.gate(results)

    print()
    print("=" * 56)
    print(f"Agent    : {source}")
    print(f"Passed   : {summary['passed']}/{summary['total']} ({summary['pass_rate']*100:.0f}%)")
    print(f"Critical : {summary['critical_failures']}")
    print(f"GATE     : {summary['gate']}")
    print("=" * 56)

    fails = [r for r in results if not r["passed"]]
    if fails:
        print("\nFailures:")
        for r in fails:
            mark = "🔴" if r["critical_failure"] else "  "
            bad = next((c for c in r["checks"] if not c["passed"]), None)
            print(f"  {mark} {r['case_id']}  {bad['check']}: {bad['detail']}")

    path = write_report(results, summary, source)
    print(f"\nScorecard: {path.relative_to(ROOT)}\n")


if __name__ == "__main__":
    main()
