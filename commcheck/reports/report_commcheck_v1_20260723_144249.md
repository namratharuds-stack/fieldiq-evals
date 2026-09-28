# CommCheck Eval Report

- **Prompt version:** `commcheck_v1`
- **Model:** `claude-sonnet-4-6`
- **Layers:** ['1', '2', '4']
- **Run:** 20260723_144249

## Summary

| Layer | Passed | Total | Rate |
|---|---|---|---|
| 1 — Schema validity | 19 | 19 | 100% |
| 2 — Rule adherence | 18 | 19 | 95% |
| **Overall** | **18** | **19** | **95%** |

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
