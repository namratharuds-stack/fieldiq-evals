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
| 3 — Quality | Specificity, conversational usability, escalation voice | LLM-as-judge |
| 4 — Adversarial | Unknowns, contradictions, prompt injection, long input | Deterministic |

All four layers are implemented. Layer 3 is in `graders/quality.py` and is not yet calibrated against human labels.

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

# v2: structural output, v2 case table, quality judge
python runner.py --layers 1,2,3,4 --prompt prompts/commcheck_v2.txt \
  --rule-cases cases/rule_cases_v2.json --structured --judge-model claude-opus-5-5
```

The runner also reads `ANTHROPIC_API_KEY` from a `.env` file at the repo root.

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

## Results: v1 → v2 (2026-09-28)

Both prompts ran on the same day with the same agent model (`claude-sonnet-4-6`), and a different model (`claude-opus-5-5`) acted as the judge. Each prompt ran once on about 20 cases. Treat this as a directional comparison, not a statistically significant one.

| | v1 | v2 |
|---|---|---|
| Output format | "Return ONLY valid JSON" in the prompt | Tool schema: enforced structurally |
| Needed cleaning before parse | **19/19** (0% compliance, reproducing the July finding) | **0/20** |
| Rule adherence | 18/19 | **20/20** |
| Shortfall vs. breach | Merged: "behind target" had to escalate, and the model didn't | Split: shortfall → `act_today` (R03), breach → `escalate` (new R13). Both pass |
| Prompt injection (A03) | Held | Held |
| Quality pass (every criterion ≥ 4/5) | 8/19 | 7/20 |
| Mean specificity / usability / escalation voice | 4.21 / 3.47 / 4.62 | 3.80 / 3.25 / 4.67 |

**v2 fixed correctness and made the text slightly worse for reps.** The judge showed why:

- **The spec-gap rule works but leaks into rep-facing text.** v2 tells the model to say when a rule doesn't cover a signal instead of extending an adjacent rule. On the Bronze outlet (R06), it did exactly that: it told the rep to check with their manager instead of inventing a Bronze rule. But the explanation landed in the card the rep reads: *"not covered by a defined rule for Bronze tier — flagging for rep awareness rather than applying an adjacent rule."* Usability scored 2/5.
- **Definition wording leaked into output.** Phrases from the v2 definitions ("This is the rep's to fix") showed up word for word in cards.
- **Usability is the weakest criterion in both versions.** Cards are accurate but too wordy for a 90-second read in the car.

**Next (v3):** add a `spec_gap` field that goes to the product team and never to the rep, and put a length limit in the schema. Then measure again.

Reports: [`report_commcheck_v1_20260928_133350.md`](reports/report_commcheck_v1_20260928_133350.md) · [`report_commcheck_v2_20260928_133817.md`](reports/report_commcheck_v2_20260928_133817.md)

---

## Structure

```
cases/       case tables (rule + adversarial)
prompts/     versioned system prompts — v1 baseline, v2 shortfall/breach split
graders/     schema.py (Layer 1), rules.py (Layer 2), quality.py (Layer 3 judge)
runner.py    orchestrator
reports/     timestamped run output
```

To measure a prompt change: add `prompts/commcheck_v2.txt`, run with
`--prompt prompts/commcheck_v2.txt`, and diff the reports.

---

*Namratha Rudrappa — CPG Commercial Execution & AI*
