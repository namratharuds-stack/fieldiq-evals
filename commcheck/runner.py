#!/usr/bin/env python3
"""FieldIQ CommCheck eval runner.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...     # or put it in ../.env
    python runner.py --layers 1,2
    python runner.py --layers 1,2,4 --prompt prompts/commcheck_v1.txt
    python runner.py --layers 1,2,3,4 --prompt prompts/commcheck_v2.txt \
        --rule-cases cases/rule_cases_v2.json --structured

--structured forces output through a tool schema instead of asking for JSON
in the prompt. Layer 3 adds an LLM judge (see graders/quality.py).

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
from graders import quality as quality_grader

try:
    import anthropic
except ImportError:
    sys.exit("Missing dependency. Run: pip install anthropic")

ROOT = Path(__file__).parent
MODEL = "claude-sonnet-4-6"

BRIEFING_TOOL = {
    "name": "submit_briefing",
    "description": "Submit the briefing cards for this outlet.",
    "input_schema": {
        "type": "object",
        "properties": {
            "outlet_name": {"type": "string"},
            "tier": {"type": "string"},
            "cards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string",
                                 "enum": ["act_today", "escalate", "opportunity"]},
                        "risk_summary": {"type": "string"},
                        "action": {"type": "string"},
                        "escalation_message": {"type": "string"},
                    },
                    "required": ["type", "risk_summary", "action"],
                },
            },
        },
        "required": ["outlet_name", "tier", "cards"],
    },
}


def load_dotenv():
    """Read KEY=value lines from ../.env without adding a dependency."""
    env = ROOT.parent / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

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
    headers = {}
    if os.environ.get("ANTHROPIC_WORKSPACE_ID"):
        headers["anthropic-workspace-id"] = os.environ["ANTHROPIC_WORKSPACE_ID"]
    return anthropic.Anthropic(api_key=key, default_headers=headers)


def load_cases(layers, rule_cases="cases/rule_cases.json"):
    cases = []
    if "1" in layers or "2" in layers or "3" in layers:
        cases += json.loads((ROOT / rule_cases).read_text())
    if "4" in layers:
        cases += json.loads((ROOT / "cases" / "adversarial_cases.json").read_text())
    return cases


def call_model(client, system_prompt, case_input, structured=False, retries=3):
    user_msg = USER_TEMPLATE.format(**case_input)
    extra = {}
    if structured:
        extra = {"tools": [BRIEFING_TOOL],
                 "tool_choice": {"type": "tool", "name": "submit_briefing"}}
    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=2000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_msg}],
                **extra,
            )
            if structured:
                return json.dumps(next(
                    b.input for b in resp.content if b.type == "tool_use"))
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
                    help="Comma-separated: 1=schema 2=rules 3=quality judge 4=adversarial")
    ap.add_argument("--prompt", default="prompts/commcheck_v1.txt")
    ap.add_argument("--rule-cases", default="cases/rule_cases.json")
    ap.add_argument("--structured", action="store_true",
                    help="Enforce output format with a tool schema, not a prompt instruction")
    ap.add_argument("--judge-model", default=MODEL,
                    help="Model used for the Layer 3 quality judge")
    ap.add_argument("--limit", type=int, default=None,
                    help="Run only first N cases (for a quick smoke test)")
    args = ap.parse_args()

    layers = set(args.layers.split(","))
    prompt_path = ROOT / args.prompt
    system_prompt = prompt_path.read_text()
    prompt_version = prompt_path.stem

    load_dotenv()
    client = get_client()
    cases = load_cases(layers, args.rule_cases)
    if args.limit:
        cases = cases[: args.limit]

    print(f"\nFieldIQ CommCheck Evals")
    print(f"  prompt : {prompt_version}")
    print(f"  model  : {MODEL}")
    print(f"  layers : {sorted(layers)}")
    print(f"  output : {'tool schema' if args.structured else 'prompt instruction'}")
    print(f"  cases  : {len(cases)}\n")

    results = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['id']} ... ", end="", flush=True)

        raw = call_model(client, system_prompt, case["input"], args.structured)

        if raw.startswith("__API_ERROR__"):
            print("API ERROR")
            results.append({
                "case_id": case["id"],
                "description": case["description"],
                "schema_passed": False,
                "schema_findings": [raw],
                "rules_passed": False,
                "rule_results": [],
                "quality_passed": None,
                "quality": None,
                "raw_output": raw,
            })
            continue

        s_passed, s_findings, parsed = schema_grader.grade(raw)

        r_passed, r_results = (True, [])
        if "2" in layers or "4" in layers:
            r_passed, r_results = rules_grader.grade(parsed, case["assertions"])

        q_passed, q_result = (None, None)
        if "3" in layers:
            try:
                q_passed, q_result = quality_grader.grade(
                    client, args.judge_model, case["input"], parsed)
            except Exception as e:
                q_passed, q_result = False, {"error": f"judge call failed: {e}"}

        overall = s_passed and r_passed
        print(("PASS" if overall else "FAIL")
              + ("" if q_passed is None else f"  quality {'PASS' if q_passed else 'FAIL'}"))

        results.append({
            "case_id": case["id"],
            "description": case["description"],
            "schema_passed": s_passed,
            "schema_findings": s_findings,
            "rules_passed": r_passed,
            "rule_results": r_results,
            "quality_passed": q_passed,
            "quality": q_result,
            "raw_output": raw,
        })

    meta = {"structured": args.structured, "rule_cases": args.rule_cases,
            "judge_model": args.judge_model if "3" in layers else None}
    write_report(results, prompt_version, sorted(layers), meta)


def write_report(results, prompt_version, layers, meta):
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
        f"- **Output format:** {'tool schema (structural)' if meta['structured'] else 'prompt instruction'}",
        f"- **Rule cases:** `{meta['rule_cases']}`",
        f"- **Run:** {ts}",
        "",
        "## Summary",
        "",
        "| Layer | Passed | Total | Rate |",
        "|---|---|---|---|",
        f"| 1 — Schema validity | {schema_pass} | {total} | {schema_pass/total*100:.0f}% |",
        f"| 2 — Rule adherence | {rules_pass} | {total} | {rules_pass/total*100:.0f}% |",
        f"| **Overall (1+2)** | **{overall}** | **{total}** | **{overall/total*100:.0f}%** |",
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

    judged = [r for r in results if r.get("quality_passed") is not None]
    if judged:
        from graders.quality import CRITERIA, PASS_FLOOR
        q_pass = sum(1 for r in judged if r["quality_passed"])
        lines += [
            "## Layer 3 — Quality (LLM judge)", "",
            f"Judge: `{meta['judge_model']}`. Pass = every applicable criterion ≥ {PASS_FLOOR}/5. "
            "Not yet calibrated against human labels.", "",
            f"**Passed: {q_pass}/{len(judged)}**", "",
            "| Case | Specificity | Usability | Escalation voice | Pass |",
            "|---|---|---|---|---|",
        ]
        for r in judged:
            q = r["quality"] or {}
            cell = lambda k: "—" if q.get(k) is None else str(q[k])
            lines.append(f"| `{r['case_id']}` | {cell('specificity')} | {cell('usability')} | "
                         f"{cell('escalation_voice')} | {'✅' if r['quality_passed'] else '❌'} |")
        means = []
        for k in CRITERIA:
            vals = [r["quality"][k] for r in judged
                    if r["quality"] and r["quality"].get(k) is not None]
            if vals:
                means.append(f"{k} {sum(vals)/len(vals):.2f}")
        lines += ["", "Mean scores: " + " · ".join(means), ""]
        low = [(r["case_id"], k, r["quality"][k], r["quality"].get(f"{k}_reason"))
               for r in judged if r["quality"]
               for k in CRITERIA
               if r["quality"].get(k) is not None and r["quality"][k] < PASS_FLOOR]
        if low:
            lines += ["### Below the floor", ""]
            lines += [f"- `{c}` {k} = {s}: {why}" for c, k, s, why in low]
            lines.append("")

    report_path = outdir / f"report_{prompt_version}_{ts}.md"
    report_path.write_text("\n".join(lines))

    print(f"\n{'='*50}")
    print(f"Overall: {overall}/{total} ({overall/total*100:.0f}%)")
    print(f"Report:  {report_path.relative_to(ROOT)}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
