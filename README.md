# FieldIQ Evals

Eval harnesses for two AI agents in [FieldIQ](https://fieldiq-pro-pilot.lovable.app), a field-selling platform for CPG sales reps.

An agent that drafts a commercial order or tells a rep what to escalate can't be judged by whether the demo looks right. These suites turn the product spec into a scoreboard, so a prompt or model change is shown to be safe before it ships.

| Suite | Agent | Fails by | Cases | Headline result |
|---|---|---|---|---|
| [`draft-order/`](draft-order) | **Draft Order Agent**: pre-builds a rep's order with a reason code and quantity on every line | *computing* wrong | 26 golden cases, 13 categories | Ship gate catches 3 critical failures on a seeded sample |
| [`commcheck/`](commcheck) | **CommCheck**: pre-visit briefing cards (`act_today`, `escalate`, `opportunity`) | *classifying* wrong | 20 cases: schema, rules, LLM-judged quality, adversarial | v1 → v2: format compliance 0% → 100%, rules 18/19 → 20/20, and a quality tradeoff the judge caught |

Two agents fail in two different ways, so the eval designs differ.

---

## Draft Order Agent: a ship gate built to say no

**Gate: zero critical failures AND ≥90% pass.**

- Quantities are scored against a hand-set band for each case, since more than one order can be right.
- Reason codes and safety behavior must match exactly.
- Three checks are critical anywhere they appear: an **unauthorized SKU**, an **MOQ violation**, or a **missing escalation** on absent or conflicting data. A critical failure fails the case, and correct quantities elsewhere can't make up for it.

```
Passed   : 22/26 (85%)
Critical : 3
GATE     : FAIL
```

| Case | Failure caught | Critical |
|---|---|---|
| GC21 | Recommended a SKU outside the outlet's authorized assortment | 🔴 |
| GC19 | Reconciled a signal contradiction instead of escalating | 🔴 |
| GC24 | Ignored a 24-case chain MOQ, so the order can't be submitted | 🔴 |
| GC12 | Sized off promo-inflated velocity instead of damping to baseline | — |

The failing gate is the point. The fixture is a seeded prediction set with four realistic misses. It shows the graders catch those failure modes and rate them at the right severity. `--live` scores the real agent.

## CommCheck: what 19 cases found

1. **A format instruction with 0% compliance.** The prompt said "Return ONLY valid JSON." All 19 responses came back wrapped in markdown fences anyway. *A prohibition in a prompt is a request.* Format has to be enforced structurally, which is why the Draft Order live mode doesn't rely on that instruction.
2. **Silent spec gaps.** The promo rule named Gold and Silver outlets and said nothing about Bronze or General Trade. The model flagged opportunities for those tiers anyway. That's a defensible call, but it's the model's decision, not the spec's. Those cases are marked `observe_only` and recorded, not scored.
3. **The failure was in my spec.** "Contract behind target" didn't trigger an escalation. The model was right: the spec had merged two different commercial events. A performance gap is something a rep can act on; a contractual breach is above the rep's authority. The fix was a new input signal, not a prompt tweak.

**What held up:** a prompt injection hidden in the rep's free-text field tried to suppress a mandatory payment escalation, and the escalation still fired. A sympathetic excuse for an overdue payment didn't soften it either. Payment escalation behaves as policy, not judgment.

### v1 → v2: fixing the findings, then measuring what the fix cost

v2 applied both fixes: format enforced through a tool schema, and shortfall split from breach. On a same-day rerun, outputs needing cleanup went from **19/19 to 0/20** and rule adherence from **18/19 to 20/20**.

A new LLM-judge layer (Opus 5.5 grading Sonnet 4.6) found the cost. v2's "say when a rule doesn't cover this" instruction worked, but the explanation leaked into the card the rep reads. Mean usability dropped from 3.47 to 3.25. The next fix is a separate `spec_gap` field for the product team. [Full comparison →](commcheck#results-v1--v2-2026-09-28)

---

## Run it

```bash
pip install -r requirements.txt

# Draft Order: fixture mode is free, offline, deterministic
cd draft-order && python score_draft_orders.py

# CommCheck: calls the Anthropic API (cents per run). Key from env or ../.env
export ANTHROPIC_API_KEY=...
cd commcheck && python runner.py --layers 1,2,4
cd commcheck && python runner.py --layers 1,2,3,4 --prompt prompts/commcheck_v2.txt \
  --rule-cases cases/rule_cases_v2.json --structured --judge-model claude-opus-5-5
```

Every run writes a timestamped markdown report and raw JSON to that suite's `reports/`. The runs quoted above are committed there.

## Structure

```
draft-order/   golden set, seeded fixture, band + criticality grader, ship gate
commcheck/     rule + adversarial cases, versioned prompt, schema + rule graders
```

To measure a prompt change, add a new version under `commcheck/prompts/`, run with `--prompt`, and diff the reports.

## Scope notes

- All outlet, SKU, contract, and velocity data is FieldIQ demo data. None of it comes from a real company.
- CommCheck is evaluated against its **specified** system prompt through the Anthropic API. The deployed prototype uses a different model backend, so these results describe the system as specified. Diffing the two is a separate exercise.
- The Layer 3 judge isn't calibrated against human labels yet. Use its scores to compare versions, not as an absolute measure of quality.

---

Built by [Namratha Rudrappa](https://namratharudrappa.com): Senior PM, Applied AI for CPG commercial execution.
