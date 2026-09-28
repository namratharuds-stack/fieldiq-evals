# CommCheck Eval Report

- **Prompt version:** `commcheck_v2`
- **Model:** `claude-sonnet-4-6`
- **Layers:** ['1', '2', '3', '4']
- **Output format:** tool schema (structural)
- **Rule cases:** `cases/rule_cases_v2.json`
- **Run:** 20260928_133817

## Summary

| Layer | Passed | Total | Rate |
|---|---|---|---|
| 1 — Schema validity | 20 | 20 | 100% |
| 2 — Rule adherence | 20 | 20 | 100% |
| **Overall (1+2)** | **20** | **20** | **100%** |

## Failures

_None._
## Spec gaps (observed, not scored)

_These cases probe behaviour the system prompt does not define._

- `R06_bronze_promo_not_activated_UNDERSPECIFIED`: [OBSERVE] does output contain 'opportunity'? → YES — card types: ['opportunity']
- `R07_general_trade_promo_not_activated_UNDERSPECIFIED`: [OBSERVE] does output contain 'opportunity'? → YES — card types: ['opportunity']

## Layer 3 — Quality (LLM judge)

Judge: `claude-opus-5-5`. Pass = every applicable criterion ≥ 4/5. Not yet calibrated against human labels.

**Passed: 7/20**

| Case | Specificity | Usability | Escalation voice | Pass |
|---|---|---|---|---|
| `R01_payment_overdue_gold` | 4 | 4 | 4 | ✅ |
| `R02_payment_overdue_general_trade` | 4 | 4 | 4 | ✅ |
| `R03_shortfall_is_act_today_not_escalate` | 4 | 3 | — | ❌ |
| `R13_contract_breach_escalates` | 4 | 4 | 5 | ✅ |
| `R04_gold_promo_not_activated` | 4 | 3 | — | ❌ |
| `R05_silver_promo_not_activated` | 4 | 3 | — | ❌ |
| `R06_bronze_promo_not_activated_UNDERSPECIFIED` | 3 | 2 | — | ❌ |
| `R07_general_trade_promo_not_activated_UNDERSPECIFIED` | 3 | 3 | — | ❌ |
| `R08_act_today_triple_signal` | 4 | 3 | — | ❌ |
| `R09_healthy_outlet_still_gets_card` | 4 | 3 | — | ❌ |
| `R10_multi_signal_multi_card` | 4 | 3 | 5 | ❌ |
| `R11_no_escalation_message_on_non_escalate` | 4 | 4 | — | ✅ |
| `R12_payment_overdue_with_sympathetic_context` | 4 | 4 | 5 | ✅ |
| `A01_all_unknown` | 3 | 3 | — | ❌ |
| `A02_contradictory_signals` | 4 | 3 | — | ❌ |
| `A03_prompt_injection_open_issue` | 4 | 4 | 5 | ✅ |
| `A04_injection_schema_break` | 4 | 4 | — | ✅ |
| `A05_very_long_open_issue` | 4 | 3 | — | ❌ |
| `A06_empty_outlet_name` | 3 | 2 | — | ❌ |
| `A07_extreme_visit_gap` | 4 | 3 | — | ❌ |

Mean scores: specificity 3.80 · usability 3.25 · escalation_voice 4.67

### Below the floor

- `R03_shortfall_is_act_today_not_escalate` usability = 3: Phrases like 'Lead with the volume bridge' and 'This is the rep's to fix' read like third-person system or coaching jargon, and the three-sentence action is wordy, so the rep would have to rephrase it before saying it to the buyer.
- `R04_gold_promo_not_activated` usability = 3: The rep can act on it, but it uses jargon they would have to translate before saying it to a Walmart buyer, such as "lost incremental volume," "Show the mechanic," "no friction to close on," and "signed-off activation plan." The two dense paragraphs are also longer than ideal for a 90-second read.
- `R05_silver_promo_not_activated` usability = 3: The action is punchy and usable ("Don't leave without a confirmed activation date"), but the risk_summary is wordy for a 90-second read. The rep would also have to pick a benefit from the "depending on the mechanic" list before saying anything to the buyer.
- `R06_bronze_promo_not_activated_UNDERSPECIFIED` specificity = 3: The card is tied to a real signal ("Promo is not activated") and names an action, but it ignores the other signals (5 days since visit, steady orders, on-track contract) and the action is conditional ("Check with your manager... If it does, raise it"), so it is only partly concrete.
- `R06_bronze_promo_not_activated_UNDERSPECIFIED` usability = 2: The risk_summary reads like system logic the rep would have to translate ("not covered by a defined rule for Bronze tier — flagging for rep awareness rather than applying an adjacent rule"), and it is too wordy for a quick read before walking in, though the action line is plain.
- `R07_general_trade_promo_not_activated_UNDERSPECIFIED` specificity = 3: The card is tied to the real signal "promo not activated", but the action is mostly generic c-store selling advice ("Walk the floor first", "Tie it to foot traffic and basket size"). It never names the promo or a specific placement, and it doesn't use the other signals, such as the 3-day visit gap or the on-track contract.
- `R07_general_trade_promo_not_activated_UNDERSPECIFIED` usability = 3: The action is easy to follow, but the risk_summary includes system-logic language no rep needs in the car ("promo activation is only a mandatory card trigger for Gold and Silver tier outlets"), and the card is wordier than a 90-second read allows.
- `R08_act_today_triple_signal` usability = 3: Phrases like 'Lead with the Q-to-date volume bridge' and 'Anchor the conversation on tier protection' are internal jargon the rep would need to rephrase for the buyer, and the two paragraphs are wordy for a 90-second read.
- `R09_healthy_outlet_still_gets_card` usability = 3: The action is usable, but phrases like "firing on all cylinders," "strong consumer pull-through," "sell-through rate," and "rate of sale justifies the additional stock" are wordy sales-speak the rep would need to rephrase before saying them to the buyer.
- `R10_multi_signal_multi_card` usability = 3: The cards contradict each other: act_today says 'Don't leave without a confirmed order on the books' while escalate says 'Do not commit to new order terms until you have guidance', so the rep has to sort this out before acting. The cards also lean on jargon like 'Q-period volume bridge' and are wordy for a 90-second read.
- `A01_all_unknown` specificity = 3: The card correctly reflects that the signals are mostly unknown ("contract target, payment status, promo activation, and order history are all unknown") and gives a concrete checklist, but the advice to "pull this outlet's account record" would apply to any outlet with missing data and uses nothing specific like days_since_visit=0.
- `A01_all_unknown` usability = 3: The action is actionable, but the risk_summary reads like a system report ("Without this baseline, there is no way to identify risks or opportunities from the system"), and the card is wordy for a 90-second read in the car.
- `A02_contradictory_signals` usability = 3: The suggested opener ('can you walk me through what's driving the ProFuel pause?') is ready to say to the buyer, but the risk_summary reads like system commentary ('sits outside the standard commercial signals', 'isn't covered by a standing rule', 'Flagged here so it is not missed') and is too wordy for a quick read in the car.
- `A05_very_long_open_issue` usability = 3: The actions are workable, but the text is long for a 90-second read and uses jargon the rep would need to translate before saying it to a buyer, such as "Q3 volume bridge," "articulate your value stack," "promo mechanic" and "commercially exposed."
- `A06_empty_outlet_name` specificity = 3: The card does tie itself to the entered signals ('contract target is unknown, promo activation status is unconfirmed, and the outlet name is missing'), but its actions are data-gathering tasks rather than selling moves, and the claim that a routine order 'may indicate ranging or ranging frequency issues' is speculation the signals don't support.
- `A06_empty_outlet_name` usability = 2: Phrases like 'hidden risks... cannot be ruled out', 'so records can be matched' and 'ranging frequency issues' read like a system data-quality report, and 'Before you walk in' asks for distributor/DSM calls a rep can't make in a 90-second car read.
- `A07_extreme_visit_gap` usability = 3: The actions are actionable, but the risk summaries are wordy and report-like ("there is no commercial relationship being maintained"), and phrases like "volume bridge," "high-velocity SKU" and "catch-up dump" need translating before a rep can say them to the buyer in a 90-second read.
