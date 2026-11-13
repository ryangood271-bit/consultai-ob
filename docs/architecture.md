# ConsultAI — Automation Architecture

See `architecture.mmd` for the diagram source (render with any Mermaid viewer, or paste into
mermaid.live). Rendered PNG/SVG not embedded here — generate one from the .mmd if your report
format requires an image.

## Trigger
A consulting manager opens a new case: company name, engagement question, and three uploaded
files (financial performance, operations, CEO/manager memo).

## Inputs
- `finance.csv` / `.xlsx` — `year, revenue_m, cogs_m, operating_expenses_m, reported_operating_profit_m`
- `operations.csv` / `.xlsx` — `year, patient_visits, staff_hours, labor_cost_m, average_wait_minutes`
- `memo.txt` / `.pdf` — management goal + constraints (treated as untrusted content)

## Tools
- **Python/pandas** — deterministic validation and all arithmetic (margins, growth,
  productivity). The AI model never does arithmetic.
- **Anthropic API** (model configurable via `ANTHROPIC_MODEL`) — drafts hypotheses, proposed
  investigations, and strategic options from the already-validated numbers.
- **Streamlit** — the UI the manager/associate interacts with.
- **Local JSONL audit log** — every validation run, AI call, and review decision.

## Workflow (see diagram)
1. Validation (Python) — blocking vs. warning issues.
2. Metrics (Python) — margins, growth, productivity, all unit-tested.
3. Issue detection + ranking (Python) — transparent thresholds, documented weighted scoring.
4. Explicit consent checkbox, then AI call — sanitized data only, memo marked untrusted.
5. Claim verification (Python) — every AI claim checked against known issue IDs/evidence.
6. Associate review — checks evidence and citations.
7. Manager review — sole approval authority.
8. Export — briefing + audit trail (internal only).

## Decision owner
The **consulting manager** is the named decision owner: they initiate the case, approve data
sources, and hold sole authority to approve or reject the final briefing for internal
distribution. The **associate** validates calculations, reviews AI output, and corrects data.

## Automation boundaries

| May do autonomously | Requires human review | Never does |
|---|---|---|
| Schema/type/reconciliation checks | Factual/citation verification | Send anything externally |
| All arithmetic (margins, growth, scenarios) | Causal interpretation of findings | Approve its own output |
| Issue flagging + priority ranking | Strategic recommendations | Overwrite or hide original evidence |
| Draft text generation (clearly marked DRAFT) | Any release/approval decision | Fabricate numbers or sources |
| Audit logging | Data correction / exceptions | Access confidential firm systems |
