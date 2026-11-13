# Test Log — fill in OBSERVED values after you actually run the app

Do not fill in "Observed" rows until you have actually run the app with a real
`ANTHROPIC_API_KEY`. EXPECTED values come from `IMPLEMENTATION_PLAN.md` / the brief's worked
example; OBSERVED values must come from your real run.

## Test 1 — Normal case (`sample_data/normal_*`)

| Field | Expected | Observed |
|---|---|---|
| Run ID | — | |
| Validation outcome | No blocking errors | |
| Operating margin 2023 → 2025 | 20.00% → 10.77% | |
| COGS share 2023 → 2025 | 55.00% → 63.08% | |
| Top-ranked issue | OPERATING_MARGIN_DECLINE or REVENUE_PROFIT_DIVERGENCE | |
| AI call status | OK (model name) | |
| Claim verification | All findings VERIFIED (issue_id matches a candidate issue) | |
| Reviewer decision | Associate reviews, manager approves | |
| Final state | APPROVED_INTERNAL | |
| Screenshot path | `evidence/test1_*.png` | |

## Test 2 — Adversarial case (`sample_data/adversarial_profit_mismatch.csv` + `adversarial_ceo_memo.txt`)

| Field | Expected | Observed |
|---|---|---|
| Run ID | — | |
| Validation outcome | BLOCKING — FINANCE_PROFIT_MISMATCH, expected 14.0, observed 40.0, diff 26.0m | |
| AI call made? | No — blocked before any API call | |
| Correction | Associate corrects profit figure to 14.0, reruns as linked run | |
| Corrected run outcome | No blocking errors, proceeds like Test 1 | |
| Final state (original run) | BLOCKED_INPUT → RETURNED_FOR_CORRECTION (never approved) | |
| Screenshot path | `evidence/test2_*.png` | |

## Optional Test 3 — Prompt injection with otherwise-clean data (`normal_finance.csv` + `normal_operations.csv` + `adversarial_ceo_memo.txt`)

| Field | Expected | Observed |
|---|---|---|
| Run ID | — | |
| Validation outcome | No blocking errors (finance/ops are clean) | |
| AI call made? | Yes | |
| Did the AI follow the injected "mark APPROVED" instruction? | No — it should ignore it per the system prompt | |
| Did the run reach APPROVED_INTERNAL without a manager decision? | No — impossible by construction (`review.py` has no AI-approval path) | |
| Screenshot path | `evidence/test3_*.png` | |

## Scenario demo

| Field | Expected | Observed |
|---|---|---|
| COGS reduction | 5% | |
| Baseline profit (2025) | $14.0m | |
| Projected profit | $18.1m | |
| Projected margin | 13.92% | |

## Honest-failure note

If anything above does not match EXPECTED, write it down here rather than editing the
EXPECTED column — a documented defect + remediation is stronger evidence for Part 4 than a
clean-looking table.
