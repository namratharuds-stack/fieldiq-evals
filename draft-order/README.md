# Draft Order Agent — Eval Harness

Scoring harness for the FieldIQ **Draft Order Agent**: the feature that pre-builds
a rep's order before a store visit, with a reason code and quantity on every line.

An order recommendation is a commercial artifact. A wrong line is not a bad answer
— it is an unorderable line the rep discovers at the buyer's desk. This harness
exists to make prompt and model changes provably safe before they ship.

---

## Running it

```bash
pip install -r ../requirements.txt

# Fixture mode — no API calls, deterministic, free
python score_draft_orders.py

# Live mode — scores the actual agent
export ANTHROPIC_API_KEY=sk-ant-...
python score_draft_orders.py --live
```

Both modes write a timestamped markdown scorecard and raw JSON to `reports/`.

---

## The golden set

**26 hand-adjudicated cases across 13 categories:**

velocity reorder · void fill · OOS recovery · post-promo damping · new outlet ·
overstock trim · missing data · conflicting signals · MOQ compliance · pack
rounding · assortment guard · confidence escalation · cap enforcement

Each case carries outlet context, the authorized/unauthorized SKU split, and the
raw signals the agent reasons over.

---

## Scoring model

**Quantities score against an explicit per-case band**, not a fixed percentage.
Several orders can be right, and a void-fill trial order tolerates different error
than a velocity reorder — one tolerance would be wrong for both. Bands are set by
hand adjudication and stated in the case file.

**Reason codes and safety behaviour are exact match.** No partial credit for
calling a void a velocity reorder; the reason code is what the rep reads and
repeats to the buyer.

**Criticality is a property of the check, not the case.** Three checks are critical
wherever they occur:

| Check | Why critical |
|---|---|
| `unauthorized_sku` | Unorderable line; erodes trust in every other line on the sheet |
| `moq_violation` | Order cannot be submitted at all |
| `missing_escalation` | Agent invented a resolution to absent or contradictory data |

A critical failure fails the case outright and cannot be offset by correct
quantities elsewhere.

**Ship gate: zero critical failures AND ≥90% pass.**

---

## Result — seeded sample agent

```
Passed   : 22/26 (85%)
Critical : 3
GATE     : FAIL
```

| Case | Failure caught | Critical |
|---|---|---|
| GC21 | Recommended a SKU outside the outlet's authorized assortment | 🔴 |
| GC19 | Reconciled a signal contradiction instead of escalating | 🔴 |
| GC24 | Ignored a 24-case chain MOQ — un-submittable order | 🔴 |
| GC12 | Sized off promo-inflated velocity instead of damping to baseline | — |

**The gate failing is the point.** `fixtures/seeded_agent_v1.json` is a
deliberately seeded prediction set, not a model run. Twenty-two cases are seeded
correct and four are seeded to fail in specific ways a demand-sensing agent
actually fails. It proves the graders catch those failure modes with the right
severity. Use `--live` to score the real agent.

---

## Assumptions

Recorded because they were judgement calls, not derivations:

- **Quantity bands are per-case min/max**, hand-set, rather than a global
  percentage tolerance.
- **Criticality attaches to the check**, not the case — an unauthorized SKU is
  critical anywhere it appears.
- **Cases target the four shipped reason codes** (`velocity_reorder`,
  `contract_gap`, `promo_requirement`, `whitespace_opportunity`), not the
  eight-code production taxonomy in the PRD. You can only measure what exists.
  The production taxonomy is the v2 case table.
- **Velocity cap is 4x weekly velocity**, applied where the case specifies it.
- **Coverage window is 2 weeks** unless a case states otherwise.
- **Outlet and SKU data is FieldIQ demo data.** Real chain MOQs and per-SKU case
  packs would replace the values here in a production build.

---

## Structure

```
cases/golden_set.json          26 cases with bands and expectations
fixtures/seeded_agent_v1.json  seeded predictions (harness self-test)
graders/score.py               band scoring, criticality, ship gate
score_draft_orders.py          runner — fixture and live modes
reports/                       timestamped scorecards
```

---

## Companion suite

[`../commcheck`](../commcheck) covers **CommCheck**, the pre-visit briefing agent — 19 cases
across schema, rule-adherence, and adversarial layers. That suite found a format
instruction with a 0% compliance rate, which is why live mode here relies on
structural output constraints rather than a "return only JSON" instruction.

Two agents, two failure surfaces. CommCheck fails by *classifying* wrongly; the
Draft Order Agent fails by *computing* wrongly. The eval designs differ
accordingly.

---

*Namratha Rudrappa — CPG Commercial Execution & AI*
