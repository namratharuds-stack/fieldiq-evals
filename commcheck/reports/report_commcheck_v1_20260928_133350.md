# CommCheck Eval Report

- **Prompt version:** `commcheck_v1`
- **Model:** `claude-sonnet-4-6`
- **Layers:** ['1', '2', '3', '4']
- **Output format:** prompt instruction
- **Rule cases:** `cases/rule_cases.json`
- **Run:** 20260928_133350

## Summary

| Layer | Passed | Total | Rate |
|---|---|---|---|
| 1 — Schema validity | 19 | 19 | 100% |
| 2 — Rule adherence | 18 | 19 | 95% |
| **Overall (1+2)** | **18** | **19** | **95%** |

## Failures

### `R03_contract_behind_escalates`
Contract breach must always escalate, never just note it

- SCHEMA: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- RULE FAILED: must contain 'escalate' card — card types present: ['act_today']

## Spec gaps (observed, not scored)

_These cases probe behaviour the system prompt does not define._

- `R06_bronze_promo_not_activated_UNDERSPECIFIED`: [OBSERVE] does output contain 'opportunity'? → YES — card types: ['opportunity']
- `R07_general_trade_promo_not_activated_UNDERSPECIFIED`: [OBSERVE] does output contain 'opportunity'? → YES — card types: ['opportunity']

## Soft violations

- `R01_payment_overdue_gold`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R02_payment_overdue_general_trade`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R03_contract_behind_escalates`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R04_gold_promo_not_activated`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R05_silver_promo_not_activated`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R06_bronze_promo_not_activated_UNDERSPECIFIED`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R07_general_trade_promo_not_activated_UNDERSPECIFIED`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R08_act_today_triple_signal`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R09_healthy_outlet_still_gets_card`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R10_multi_signal_multi_card`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R11_no_escalation_message_on_non_escalate`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R12_payment_overdue_with_sympathetic_context`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `A01_all_unknown`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `A02_contradictory_signals`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `A03_prompt_injection_open_issue`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `A04_injection_schema_break`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `A05_very_long_open_issue`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `A06_empty_outlet_name`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `A07_extreme_visit_gap`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction

## Layer 3 — Quality (LLM judge)

Judge: `claude-opus-5-5`. Pass = every applicable criterion ≥ 4/5. Not yet calibrated against human labels.

**Passed: 8/19**

| Case | Specificity | Usability | Escalation voice | Pass |
|---|---|---|---|---|
| `R01_payment_overdue_gold` | 4 | 4 | 4 | ✅ |
| `R02_payment_overdue_general_trade` | 4 | 3 | 5 | ❌ |
| `R03_contract_behind_escalates` | 4 | 3 | — | ❌ |
| `R04_gold_promo_not_activated` | 4 | 3 | — | ❌ |
| `R05_silver_promo_not_activated` | 4 | 4 | — | ✅ |
| `R06_bronze_promo_not_activated_UNDERSPECIFIED` | 4 | 4 | — | ✅ |
| `R07_general_trade_promo_not_activated_UNDERSPECIFIED` | 4 | 3 | — | ❌ |
| `R08_act_today_triple_signal` | 4 | 3 | — | ❌ |
| `R09_healthy_outlet_still_gets_card` | 5 | 4 | — | ✅ |
| `R10_multi_signal_multi_card` | 5 | 3 | 5 | ❌ |
| `R11_no_escalation_message_on_non_escalate` | 5 | 4 | — | ✅ |
| `R12_payment_overdue_with_sympathetic_context` | 5 | 4 | 5 | ✅ |
| `A01_all_unknown` | 3 | 4 | — | ❌ |
| `A02_contradictory_signals` | 5 | 3 | 5 | ❌ |
| `A03_prompt_injection_open_issue` | 4 | 4 | 5 | ✅ |
| `A04_injection_schema_break` | 4 | 4 | — | ✅ |
| `A05_very_long_open_issue` | 4 | 3 | 4 | ❌ |
| `A06_empty_outlet_name` | 3 | 3 | — | ❌ |
| `A07_extreme_visit_gap` | 5 | 3 | 4 | ❌ |

Mean scores: specificity 4.21 · usability 3.47 · escalation_voice 4.62

### Below the floor

- `R02_payment_overdue_general_trade` usability = 3: The suggested line to the buyer ("can we sort that out today so I can keep your orders flowing smoothly?") is ready to say, but the risk_summary reads like a system note ("creates credit risk and may block future order intake if it breaches terms") and the action paragraph is wordy for a 90-second read.
- `R03_contract_behind_escalates` usability = 3: The opening line ('we're sitting behind target and I want to make sure we protect your Silver tier benefits') is sayable as written, but the action paragraph is long for a car read and leans on jargon like 'SKU-level bridge proposal,' 'top-velocity SKU,' and 'rate-of-sale alone.'
- `R04_gold_promo_not_activated` usability = 3: The opener line is sayable, but the action block is long for a 90-second read, and phrases like 'priority execution standard' and 'sell-through numbers at risk' read like internal policy language rather than plain rep talk.
- `R07_general_trade_promo_not_activated_UNDERSPECIFIED` usability = 3: The opening script is sayable to the buyer, but the risk_summary uses jargon like "promo mechanics unexecuted" and "lost velocity," and the action block is long for a 90-second read in the car.
- `R08_act_today_triple_signal` usability = 3: The scripted lines are sayable, but the cards are wordy for a 90-second read, and jargon like "promotional mechanics," "sell-through on the table," and "layer in an incremental order on top of the volume bridge conversation" needs translating before use.
- `R10_multi_signal_multi_card` usability = 3: The cards are usable but wordy, with long multi-sentence action paragraphs and jargon like "Pull the Q3 volume bridge." They also contradict each other: the escalate card says "Do not process any new orders until payment status is resolved" while the act_today card says "Make it easy for them to say yes to a reorder."
- `A01_all_unknown` specificity = 3: The card correctly reads the empty signals ('no visit history, no recent order on record, and no commercial data') and turns them into concrete steps ('leave with at least a name, a phone number, and a rough sense of their monthly volume'), but with no real outlet data the advice is essentially a generic prospecting script any unknown outlet would get.
- `A02_contradictory_signals` usability = 3: The action is clear and actionable, but it is long for a 90-second read, and the risk_summary uses report-style phrasing like "contract breach in progress regardless of current surface-level metrics appearing healthy" that a rep would have to digest rather than use directly.
- `A05_very_long_open_issue` usability = 3: The quoted openers are sayable as written ('We're behind on the contract target and I want to close that gap today'). But the four cards carry long two-sentence risk summaries and multi-step actions, which is a lot to read in 90 seconds, and phrases like 'structural barrier to hitting contract targets' read more like analysis than car-ready notes.
- `A06_empty_outlet_name` specificity = 3: The card ties to real gaps ("Promo activation status is unconfirmed", "no contract visibility"), but the action is a catch-all "full commercial audit" with generic steps like "Leave with at least one concrete next action documented." It never uses the actual signals: 5 days since visit, steady orders, current payment.
- `A06_empty_outlet_name` usability = 3: The action is a long run-on checklist that is hard to scan in the car, and phrases like "flying blind" and "full commercial audit" are report-speak the rep would need to turn into something to say to the buyer.
- `A07_extreme_visit_gap` usability = 3: The actions are actionable, but the cards are wordy for a 90-second read and include jargon like 'relationship and contract breach risk' and 'bridge proposal'; the first card's 'Before the visit, alert your manager' duplicates the escalate cards, so the rep has to consolidate them before using.
