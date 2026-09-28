#!/usr/bin/env python3
"""FieldIQ CommCheck eval runner.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python runner.py --layers 1,2
    python runner.py --layers 1,2,4 --prompt prompts/commcheck_v1.txt

Evaluates the CommCheck system prompt against the Anthropic API directly.
Note: this tests the prompt AS SPECIFIED. The deployed Lovable app runs a
substituted backend, so results here describe the intended system, not the
shipped one. Comparing the two is a separate run.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from graders import schema as schema_grader
from graders import rules as rules_grader

try:
    import anthropic
except ImportError:
    sys.exit("Missing dependency. Run: pip install anthropic")

ROOT = Path(__file__).parent
MODEL = "claude-sonnet-4-6"

USER_TEMPLATE = """Analyze these outlets and generate commercial briefing cards:

Outlet: {outlet_name} | Tier: {tier} | Days since last visit: {days_since_visit} | Last order: {last_order} | Promo activated: {promo_activated} | Contract target: {contract_target} | Payment: {payment_status} | Open issue: {open_issue}"""


def get_client():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit(
            "ANTHROPIC_API_KEY not set.\n\n"
            "  macOS/Linux:  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "  Windows:      set ANTHROPIC_API_KEY=sk-ant-...\n\n"
            "Get a key at console.anthropic.com"
        )
    return anthropic.Anthropic(api_key=key)


def load_cases(layers):
    cases = []
    if "1" in layers or "2" in layers:
        cases += json.loads((ROOT / "cases" / "rule_cases.json").read_text())
    if "4" in layers:
        cases += json.loads((ROOT / "cases" / "adversarial_cases.json").read_text())
    return cases


def call_model(client, system_prompt, case_input, retries=3):
    user_msg = USER_TEMPLATE.format(**case_input)
    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_msg}],
            )
            return "".join(
                b.text for b in resp.content if getattr(b, "type", "") == "text"
            )
        except Exception as e:
            if attempt == retries - 1:
                return f"__API_ERROR__: {e}"
            time.sleep(2 ** attempt)
    return "__API_ERROR__: exhausted retries"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", default="1,2",
                    help="Comma-separated: 1=schema 2=rules 4=adversarial")
    ap.add_argument("--prompt", default="prompts/commcheck_v1.txt")
    ap.add_argument("--limit", type=int, default=None,
                    help="Run only first N cases (for a quick smoke test)")
    args = ap.parse_args()

    layers = set(args.layers.split(","))
    prompt_path = ROOT / args.prompt
    system_prompt = prompt_path.read_text()
    prompt_version = prompt_path.stem

    client = get_client()
    cases = load_cases(layers)
    if args.limit:
        cases = cases[: args.limit]

    print(f"\nFieldIQ CommCheck Evals")
    print(f"  prompt : {prompt_version}")
    print(f"  model  : {MODEL}")
    print(f"  layers : {sorted(layers)}")
    print(f"  cases  : {len(cases)}\n")

    results = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['id']} ... ", end="", flush=True)

        raw = call_model(client, system_prompt, case["input"])

        if raw.startswith("__API_ERROR__"):
            print("API ERROR")
            results.append({
                "case_id": case["id"],
                "description": case["description"],
                "schema_passed": False,
                "schema_findings": [raw],
                "rules_passed": False,
                "rule_results": [],
                "raw_output": raw,
            })
            continue

        s_passed, s_findings, parsed = schema_grader.grade(raw)

        r_passed, r_results = (True, [])
        if "2" in layers or "4" in layers:
            r_passed, r_results = rules_grader.grade(parsed, case["assertions"])

        overall = s_passed and r_passed
        print("PASS" if overall else "FAIL")

        results.append({
            "case_id": case["id"],
            "description": case["description"],
            "schema_passed": s_passed,
            "schema_findings": s_findings,
            "rules_passed": r_passed,
            "rule_results": r_results,
            "raw_output": raw,
        })

    write_report(results, prompt_version, sorted(layers))


def write_report(results, prompt_version, layers):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = ROOT / "reports"
    outdir.mkdir(exist_ok=True)

    (outdir / f"run_{prompt_version}_{ts}.json").write_text(
        json.dumps(results, indent=2)
    )

    total = len(results)
    schema_pass = sum(1 for r in results if r["schema_passed"])
    rules_pass = sum(1 for r in results if r["rules_passed"])
    overall = sum(1 for r in results if r["schema_passed"] and r["rules_passed"])

    lines = [
        f"# CommCheck Eval Report",
        "",
        f"- **Prompt version:** `{prompt_version}`",
        f"- **Model:** `{MODEL}`",
        f"- **Layers:** {layers}",
        f"- **Run:** {ts}",
        "",
        "## Summary",
        "",
        "| Layer | Passed | Total | Rate |",
        "|---|---|---|---|",
        f"| 1 — Schema validity | {schema_pass} | {total} | {schema_pass/total*100:.0f}% |",
        f"| 2 — Rule adherence | {rules_pass} | {total} | {rules_pass/total*100:.0f}% |",
        f"| **Overall** | **{overall}** | **{total}** | **{overall/total*100:.0f}%** |",
        "",
        "## Failures",
        "",
    ]

    failures = [r for r in results if not (r["schema_passed"] and r["rules_passed"])]
    if not failures:
        lines.append("_None._")
    else:
        for r in failures:
            lines.append(f"### `{r['case_id']}`")
            lines.append(f"{r['description']}")
            lines.append("")
            for f in r["schema_findings"]:
                lines.append(f"- SCHEMA: {f}")
            for a in r["rule_results"]:
                if a["passed"] is False:
                    lines.append(f"- RULE FAILED: {a['assertion']} — {a['observed']}")
            lines.append("")

    obs = []
    for r in results:
        for a in r["rule_results"]:
            if not a["scored"]:
                obs.append(f"- `{r['case_id']}`: {a['assertion']} → {a['observed']}")

    if obs:
        lines += ["## Spec gaps (observed, not scored)", "",
                  "_These cases probe behaviour the system prompt does not define._",
                  ""] + obs + [""]

    notes = []
    for r in results:
        for f in r["schema_findings"]:
            if "SPEC VIOLATION" in f:
                notes.append(f"- `{r['case_id']}`: {f}")
    if notes:
        lines += ["## Soft violations", ""] + notes + [""]

    report_path = outdir / f"report_{prompt_version}_{ts}.md"
    report_path.write_text("\n".join(lines))

    print(f"\n{'='*50}")
    print(f"Overall: {overall}/{total} ({overall/total*100:.0f}%)")
    print(f"Report:  {report_path.relative_to(ROOT)}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
