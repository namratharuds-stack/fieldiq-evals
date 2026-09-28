# CommCheck Eval Report

- **Prompt version:** `commcheck_v1`
- **Model:** `claude-sonnet-4-6`
- **Layers:** ['1', '2']
- **Run:** 20260723_143820

## Summary

| Layer | Passed | Total | Rate |
|---|---|---|---|
| 1 — Schema validity | 3 | 3 | 100% |
| 2 — Rule adherence | 2 | 3 | 67% |
| **Overall** | **2** | **3** | **67%** |

## Failures

### `R03_contract_behind_escalates`
Contract breach must always escalate, never just note it

- SCHEMA: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- RULE FAILED: must contain 'escalate' card — card types present: ['act_today']

## Soft violations

- `R01_payment_overdue_gold`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R02_payment_overdue_general_trade`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
- `R03_contract_behind_escalates`: SPEC VIOLATION: output required cleaning (markdown fence or preamble) despite 'Return ONLY valid JSON' instruction
