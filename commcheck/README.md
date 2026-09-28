# FieldIQ CommCheck — Eval Suite

Evaluation harness for **CommCheck**, the pre-visit commercial intelligence
module in FieldIQ. CommCheck takes eight structured fields about a CPG retail
outlet and returns briefing cards (`act_today`, `escalate`, `opportunity`) that
tell a field sales rep what to do before they walk in.

This repo measures whether it actually does that reliably.

---

## Why evals, not tests

Tests ask "did the code run." Evals ask "was the output *good*" — where good is
graded, partly subjective, and shifts every time the prompt changes.

CommCheck's system prompt encodes explicit business rules (payment overdue must
always escalate; promo not activated at a Gold/Silver outlet must always flag an
opportunity). Those rules are assertable. This suite turns the spec into a
scoreboard.

---

## Layers

| Layer | What it checks | Method |
|---|---|---|
| 1 — Schema | Parseable JSON, valid card enums, required fields non-empty | Deterministic |
| 2 — Rules | Business rules from the system prompt hold | Deterministic |
| 3 — Quality | Specificity, conversational usability, escalation voice | LLM-as-judge *(not yet built)* |
| 4 — Adversarial | Unknowns, contradictions, prompt injection, long input | Deterministic |

Layers 1, 2 and 4 are implemented. Layer 3 is the next build.

---

## Running it

```bash
pip install -r ../requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...     # macOS / Linux
# set ANTHROPIC_API_KEY=sk-ant-...      # Windows cmd
# $env:ANTHROPIC_API_KEY="sk-ant-..."   # Windows PowerShell

python runner.py --layers 1,2           # deterministic pass, 12 cases
python runner.py --layers 1,2,4         # add adversarial, 19 cases
python runner.py --layers 1,2 --limit 3 # quick smoke test
```

Each run writes a timestamped markdown report and raw JSON to `reports/`.

**Cost:** roughly 19 API calls per full run. Cents, not dollars.

---

## What it tests against

The eval hits the Anthropic API directly with the CommCheck system prompt,
versioned in `prompts/`. This measures the system **as specified**.

The deployed FieldIQ app runs on a substituted backend (Lovable swapped its own
model in place of the specified Claude API). So these results describe the
intended system, not the shipped one. Running the same case table against the
deployed app and diffing the two is a separate exercise — and a revealing one.

---

## Case design

**Rule cases** (`cases/rule_cases.json`) — one case per assertable rule, plus
combinations. Includes cases where the spec is *silent*: promo activation at
Bronze and General Trade outlets is undefined by the prompt, so those cases are
marked `observe_only` and recorded rather than scored. Writing evals surfaced
that gap in the spec.

**Adversarial cases** (`cases/adversarial_cases.json`) — all-unknown inputs,
contradictory signals, oversized free text, and two prompt-injection probes. The
`open_issue` field accepts unsanitised rep free text and is concatenated into the
model call, so it is a live injection surface. `A03` tests whether an injected
instruction can suppress a mandatory payment escalation.

---

## Notable failure modes to watch

- **Softened escalation.** Payment overdue is a policy control, not a judgement
  call. `R12` supplies sympathetic context (loyal owner, family emergency) and
  checks the escalation still fires. In field execution, failing to escalate is
  the expensive error — it suppresses the corrective action.
- **Silent spec gaps.** Tier-conditional rules that omit tiers.
- **Format drift.** Markdown fences around JSON despite an explicit instruction;
  logged as a soft violation rather than a hard failure.

---

## Structure

```
cases/       case tables (rule + adversarial)
prompts/     versioned system prompts — v1 is the baseline
graders/     schema.py (Layer 1), rules.py (Layer 2)
runner.py    orchestrator
reports/     timestamped run output
```

To measure a prompt change: add `prompts/commcheck_v2.txt`, run with
`--prompt prompts/commcheck_v2.txt`, and diff the reports.

---

*Namratha Rudrappa — CPG Commercial Execution & AI*
