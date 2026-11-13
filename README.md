# ConsultAI — Business Performance & Strategy Assistant

Educational prototype built for an Organizational Behavior assignment. **Not** an official
Bain & Company system — an independent prototype referencing a public Bain job posting and
the O*NET Management Analysts task list as evidence of a real job's responsibilities. No
Bain branding, confidential data, or internal systems are used or implied.

## What this is

A small Streamlit app that automates a real subset of an entry-level management consultant's
work — financial/operational diagnosis and first-draft internal briefing prep — while keeping
every approval decision, citation check, and client-facing judgment under explicit human
control. See `docs/architecture.md` for the full design and `docs/manager_protocol.md` for
the failure/escalation rules.

## Setup

```bash
cd consultai-ob
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your own `ANTHROPIC_API_KEY`:

```bash
cp .env.example .env
```

Then export it before running (Streamlit does not auto-load `.env`):

```bash
export $(grep -v '^#' .env | xargs)
```

## Run the app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Use the files in `sample_data/` to run Test 1 (normal) and
Test 2 (adversarial) — see `docs/test_log_template.md` for exactly what to record.

**Without an API key**, the app still runs: validation, metrics, charts, issue ranking, and
the scenario simulator all work. The "Call Anthropic API" button will show a clear
`NO AI GENERATED` error instead of fabricating any content — that mode alone does not satisfy
the assignment's "real AI tools" requirement, so you need a working key for your actual test
runs.

## Run the tests

```bash
pytest -q
```

All tests are offline — the AI-contract tests mock the Anthropic client so no network call or
real API key is needed to run the suite. Real end-to-end API behavior is verified manually,
with your own key, using the app itself (see Part 4 of the assignment).

## Project structure

See `IMPLEMENTATION_PLAN.md` for the build log and real pytest output, and `docs/` for the
architecture diagram, manager protocol, OB analysis, job cross-check, test log template,
report outline, and demo script.

## Data safety

- `sample_data/` contains only fictional, synthetic data for a fictional company
  ("BlueRiver Healthcare Services").
- Do not upload real, confidential, or identifying data to this app — the UI requires an
  explicit consent checkbox before any content reaches the Anthropic API, and memo text is
  scanned for SSN/email/phone-shaped patterns as an extra guard, but you are still responsible
  for what you upload.
- `outputs/` (raw uploads, audit logs) is gitignored — do not commit it.
