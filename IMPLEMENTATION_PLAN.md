# ConsultAI — Implementation Plan

## Scope decision
Building the MVP exactly as scoped in the brief, with one simplification: PDF memo support
(pypdf) is included but kept optional/best-effort — if pypdf isn't installed or the PDF is
image-based, the app shows a clear error rather than failing silently. TXT memos are the
primary supported format for the demo fixtures.

## Build order
1. `consultai/schemas.py` — column/schema constants, file-size/extension limits, severity enum.
2. `consultai/ingest.py` — read CSV/TXT/PDF uploads, compute SHA-256, persist originals to `outputs/<run_id>/raw/`.
3. `consultai/validation.py` — deterministic pre-AI checks (schema, numeric, year sequence,
   profit reconciliation tolerance 0.1, cross-document labor-cost consistency, sensitive-data
   regex scan on memo text). Returns `ValidationIssue` list split into BLOCKING vs WARNING.
4. `consultai/metrics.py` — pure pandas/Python financial + operational metrics, unit-tested
   against the brief's worked numbers (margin 20.00% -> 10.7692%, etc.).
5. `consultai/issue_detection.py` — threshold-based candidate issues + documented weighted
   scoring (impact 50/evidence 30/relevance 20), returns ranked top-3 with evidence refs.
6. `consultai/scenarios.py` — pure-math COGS/revenue scenario simulator (no AI, no I/O).
7. `consultai/ai_client.py` — Anthropic SDK wrapper. Builds a system prompt that labels all
   uploaded content as untrusted data, requests strict JSON output, hard-fails (no fabricated
   content) if `ANTHROPIC_API_KEY` is missing or the response fails schema validation.
8. `consultai/claim_verification.py` — cross-checks every numeric claim the model returns
   against the validated metrics table; anything it can't match gets tagged
   `NEEDS HUMAN VERIFICATION`.
9. `consultai/review.py` — run-state machine (`BLOCKED_INPUT`, `CALCULATIONS_READY`,
   `DRAFT_REVIEW_REQUIRED`, `RETURNED_FOR_CORRECTION`, `REJECTED`, `APPROVED_INTERNAL`) with
   enforced transition rules (no self-approval, blocked input can't be approved, manager-only
   final approval).
10. `consultai/reports.py` — Markdown briefing generator; only shows an APPROVED banner when
    state is `APPROVED_INTERNAL`.
11. `consultai/audit.py` — append-only JSONL audit log per run, plus a test-log exporter.
12. `app.py` — Streamlit UI with the six-page sidebar nav specified in the brief, wiring all
    modules together and holding run state in `st.session_state`.
13. `sample_data/` — the exact fixtures specified in the brief (normal + two adversarial
    variants + injection memo).
14. `tests/` — pytest coverage for validation, metrics, issue scoring, scenario math, the
    state machine, and the AI client's missing-key / bad-JSON failure paths (mocked, not a
    real network call — real API calls are run manually by the user per the brief).
15. `docs/` — architecture (md + mermaid), manager protocol, OB analysis, job/task cross-check,
    test log template, report outline, demo script.
16. `requirements.txt`, `.env.example`, `.gitignore`, `README.md`.
17. Run `pytest -q`, fix defects, paste real terminal output into this plan's status section
    (not fabricated).

## What I will NOT fabricate
- No canned AI output. If `ANTHROPIC_API_KEY` is unset, the app shows `NO AI GENERATED` and
  that run cannot reach `APPROVED_INTERNAL`.
- No invented test results — pytest output quoted in this doc will be real output from this
  session's terminal.
- No claim that the real Anthropic API test runs (normal case, adversarial case) have happened
  until you run them yourself with your API key and I capture the actual output.

## Status
- [x] Scaffolding + modules built
- [x] pytest passing — real terminal output below:

```
$ pytest -q
................................                                         [100%]
32 passed in 0.95s
```

  (First run surfaced 2 real bugs, fixed before this result: a float-precision test
  assertion, and a validation gap where `FINANCE_MISSING_YEAR_IN_SEQUENCE` was skipped
  whenever a file also had too few rows — fixed in `consultai/validation.py` so the two
  checks run independently.)
- [x] Sample fixtures created (`sample_data/`)
- [x] Docs written (`docs/`)
- [x] Streamlit app boots cleanly (`streamlit run app.py` → real HTTP 200, no exceptions in log).
- [x] Core pipeline smoke-tested against the real sample files (bypassing the file-upload UI,
  which browser automation can't drive — this still exercises the real
  `validation`/`metrics`/`issue_detection` modules the app calls). Real output:

```
$ python scripts/smoke_test_pipeline.py

=== Test 1 — Normal case ===
Blocking errors: 0
Operating margin: 20.00% -> 10.77%
Revenue change: 30.00%  |  Operating profit change: -30.00%
Detected 5 candidate issue(s), top 3:
  - [5.00] Operating margin has deteriorated
  - [5.00] Revenue and operating profit are moving in opposite directions
  - [4.30] Cost of goods sold is consuming a growing share of revenue
RESULT: CALCULATIONS_READY (would proceed to AI call in the app).

=== Test 2 — Adversarial case (profit mismatch + injection memo) ===
Blocking errors: 1
  BLOCKING [FINANCE_PROFIT_MISMATCH] Reported operating profit does not reconcile with
  revenue - COGS - opex (difference 26.0000m exceeds tolerance 0.1m).
RESULT: BLOCKED_INPUT — no metrics/issue detection run (matches app behavior).
```

- [ ] **Not yet done, requires you:** the actual UI click-through (file uploads need a human,
  browser automation can't set file inputs) and the real Anthropic API call, with your own
  `ANTHROPIC_API_KEY`. See `docs/test_log_template.md` and `README.md` for exact steps. This
  is the piece that turns "the logic is correct" into "I ran a real AI tool and have evidence."
