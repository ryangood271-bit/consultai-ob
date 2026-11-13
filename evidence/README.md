# Evidence folder

Put real outputs here only — screenshots, downloaded briefings, and exported audit/test logs
from actual app runs. Nothing in this folder should be fabricated or hand-written to look
like a tool output.

Suggested naming: `test1_<page>_<description>.png`, `test2_<page>_<description>.png`,
`test1_briefing.md`, `test2_audit_log.jsonl`.

## How to capture screenshots

1. Run the app (`streamlit run app.py`), open it in your browser at `localhost:8501`.
2. Walk through Case Setup → Analysis Dashboard → Ranked Issue Findings → (adversarial case)
   → Risks & Human Review → Briefing & Audit Trail.
3. Screenshot each meaningful state (validation blocked, AI draft, claim-verification tags,
   review decision, final briefing) and save here.
4. Copy the downloaded briefing Markdown and exported test log here too — those are real
   artifacts, not just images.
