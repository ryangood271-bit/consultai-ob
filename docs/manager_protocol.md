# Manager Protocol — ConsultAI

One named human is accountable for accuracy, interpretation, and release at every stage.
AI can prepare an analysis; it cannot approve itself, release anything externally, or
overwrite evidence.

## Decision rights

| Decision | Owner |
|---|---|
| Initiate analysis, approve data sources | Consulting manager |
| Validate calculations, investigate errors | Associate consultant |
| Produce preliminary interpretation | AI system (draft only) |
| Review findings and hypotheses | Associate consultant |
| Approve strategic recommendations / internal release | Consulting manager (sole authority) |
| Authorize any client delivery | Consulting manager (out of scope for this prototype — never automated) |

## Failure 1 — Input data inconsistency

- **Detection:** `abs(reported_operating_profit_m - (revenue_m - cogs_m - operating_expenses_m)) > 0.1m`, OR a missing/duplicate year, OR `labor_cost_m > operating_expenses_m` for the same year.
- **Evidence that triggers escalation:** exact filename, row/year, column, expected value, observed value (shown verbatim in the UI and audit log).
- **Escalation:** run enters `BLOCKED_INPUT`; no AI call is permitted from this state.
- **Responsible reviewer:** Associate consultant.
- **Manual override:** None permitted — the associate must correct the source data (not bypass the check) after verifying the real figures.
- **Recovery:** A corrected file starts a new run linked to the original run ID; the failed run stays in the log.
- **Repeated failure:** After **two** similar failures on the same case, require a second analyst to independently verify the source data mapping before any further run is attempted.

## Failure 2 — Hallucinated or unsupported AI finding

- **Detection:** An AI-returned `issue_id` that doesn't match any code-detected candidate issue, or a numeric/causal claim with no matching evidence reference (flagged automatically as `NEEDS HUMAN VERIFICATION` by `claim_verification.py`).
- **Evidence:** the specific claim, plus the reason it couldn't be matched.
- **Escalation:** manager approval is blocked for that finding; it is surfaced on the Risks & Human Review page.
- **Responsible reviewer:** Associate removes/rewrites the finding with source-backed evidence; manager re-checks strategic implications before approving.
- **Manual override:** Associate may edit the AI draft text directly before passing to the manager — the edit is logged, the AI's original text is preserved in the audit trail.
- **Recovery:** Revise inputs/prompt framing if needed and regenerate; version both drafts in the log.
- **Repeated failure:** After **two** unsupported findings in the same case, require line-by-line manual verification of every AI claim before any further AI-assisted draft is allowed for that case.

## Failure 3 — Prompt injection / untrusted instruction in the memo

- **Detection:** memo text contains instruction-like language aimed at the system (e.g., "ignore checks," "mark approved," "system override"), or — if validation ever passed with such a memo — the AI's output appears to have followed it.
- **Evidence:** the quoted injection text, plus a side-by-side of what the system actually did vs. what the injected text requested.
- **Escalation:** the input is flagged/quarantined; if the model's behavior was affected, the associate must notify the manager immediately, regardless of whether the output "looked fine."
- **Responsible reviewer:** Associate consultant, manager informed if behavior was affected.
- **Manual override:** Quarantine the offending memo; continue using only validated, trusted financial/operational data. There is no "approve anyway" action in the system — approval always requires a named manager decision, never a bypass flag.
- **Recovery:** Remove the untrusted instruction text, rerun with a sanitized memo, and document the rerun as a new linked test.
- **Repeated failure:** Suspend memo-driven AI narrative generation for the case, strengthen input isolation (the system prompt already instructs the model to treat memo content as data-only — see `ai_client.py`), and require an adversarial regression test before re-enabling.

## What this protocol does not claim

- Detection is not perfect. The adversarial test in Part 4 is designed to show a real result —
  including a safeguard that fails — not to prove the system is unbeatable.
- The associate/manager roles are simulated by the same student tester in Part 4; this is
  explicitly labeled as a role-play, not a real organizational sign-off.
