# 5-Minute Demo Script

1. **(30s)** "This is ConsultAI — a prototype automating part of a Bain Associate
   Consultant's financial-diagnosis and briefing-prep work. It's an educational prototype,
   not a real Bain system."
2. **(60s) Case Setup:** upload `normal_finance.csv`, `normal_operations.csv`,
   `normal_ceo_memo.txt`; check the consent box; run. Show validation passing.
3. **(60s) Analysis Dashboard:** show the revenue-vs-profit and margin charts — point out
   revenue up 30%, profit down 30%, all computed in Python.
4. **(60s) Ranked Issue Findings:** show the top-3 ranked issues with evidence refs; click
   "Call Anthropic API"; show the real model response and claim-verification tags.
5. **(30s) Scenario Simulator:** slide COGS reduction to 5%, show $18.1m / 13.92% appear.
6. **(60s) Risks & Human Review → adversarial case:** reload with
   `adversarial_profit_mismatch.csv` + `adversarial_ceo_memo.txt`; show it gets BLOCKED before
   any AI call, with the exact row/expected/observed numbers.
7. **(20s) Briefing & Audit Trail:** show the DRAFT banner, the audit log, and that nothing
   reaches APPROVED_INTERNAL without a named manager decision.

**Closing line:** "I've automated the routine financial diagnosis, I have a tested risk
protocol for three concrete failure modes, and I can now spend my time on evidence
verification and strategic framing instead of recomputing margins by hand."
