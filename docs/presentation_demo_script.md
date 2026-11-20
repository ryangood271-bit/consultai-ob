# Demo Script — 3 to 5 minutes

Matches the live app exactly as of this build. Use your live Streamlit Cloud link so it's
clear this runs for real, not just on your laptop. Record your screen (QuickTime, Loom, or
Zoom's local recording all work) and just follow this — minimal narration needed beyond what's
in brackets.

**Before recording:** have two browser tabs ready — your live app, and a stockanalysis.com
income-statement page for a real company you haven't shown me yet (keeps it genuinely live,
not rehearsed-looking). Also have `sample_data/adversarial_profit_mismatch.csv` easy to find
in Finder for the difficult case.

---

**0:00–0:20 — Intro**
"This is ConsultAI, a system I built that automates part of a Bain Associate Consultant's job
— diagnosing a company's financial performance and drafting a first-pass briefing. It uses a
real AI model, Claude, through the Anthropic API, with a human required to approve anything
before it's final."

**0:20–1:00 — Case Setup (normal case)**
- Type the company name.
- Go to "Paste a link," paste a stockanalysis.com income-statement URL, click "Fetch & extract
  with AI."
- Show the extracted table appearing — "the AI pulled these numbers out itself; I can edit any
  cell before trusting it."
- Click "Run validation & calculations." Point out: "this is Python checking the math reconciles
  — no AI, no blocking errors, so we can proceed."

**1:00–1:40 — Analysis Dashboard**
- Point at the overall rating gauge: "this is a deterministic score — not an AI opinion — showing
  where the company falls, with a plain reason why."
- Scroll past the plain-English paragraph and the three charts: "revenue vs. profit, margin
  trend, and where every dollar of revenue actually goes."

**1:40–2:30 — Findings & Recommendations (the real AI step)**
- Point at the headline "Top Issue" card, then the "Detected Issues" tab — each ranked issue
  with its evidence.
- Switch to the "AI Analysis & Recommendations" tab, click "Call Anthropic API now" — let it
  load on camera (takes a few seconds, that's the real network call).
- Scroll to the "Bottom line" section: "this is the AI's interpretation — what's going on,
  unconfirmed theories, and recommendations. Everything it says gets checked against the real
  numbers afterward — anything it can't back up gets flagged, not trusted."

**2:30–2:50 — Scenario Simulator (quick)**
- Move the COGS slider, show the projected profit/margin update instantly. "Pure math, no AI,
  just a what-if calculator."

**2:50–3:30 — Human-in-the-loop control (the actual point of the assignment)**
- Go to Risks & Human Review — point at the three green status cards (Blocking Errors /
  Warnings / Unverified AI Claims). Fill in your name, role = "associate," decision = "approve,"
  click submit. **Pause a beat for the page to refresh, then show the refusal** — "only a
  'manager' role can approve; the system enforces this in code, not just on paper."
- Change role to "manager," submit again — show it succeeding, state changes to
  APPROVED_INTERNAL.

**3:30–3:50 — Output + the new "communicating with people" step**
- Go to Briefing & Audit Trail — the "📋 Briefing" tab, download the PDF briefly on camera.
- Click the "✉️ Client Email" tab — now unlocked because the run is approved. Click "Draft
  client email," show the generated draft. "This only works after approval, only uses verified
  findings, and there's no send button anywhere — I'd copy this into my own email."

**3:50–4:30 — The difficult/adversarial case**
- Click "Reset / New Case."
- Upload `adversarial_profit_mismatch.csv` as the financial statement — this file has a
  deliberately wrong profit figure, off by $26M.
- Click "Run validation & calculations." **Show the exact blocking error on screen** — expected
  vs. observed numbers. "No AI call happens from here. There's no bypass button — I tried, and
  the system refuses to let anything be approved while this is blocked."

**4:30–4:50 — Close**
"I've automated the routine financial diagnosis, I have a risk protocol tested against real
bad data and a real prompt-injection attempt — not just described on paper — and I can now
spend my time checking the AI's work and framing strategy instead of recalculating margins by
hand."

---

## What to say if something breaks on camera
Don't edit it out — show it. Say what you expected, what actually happened, and whether that's
a real limitation (good evidence for Part 3's "what failed") or just needs a page refresh.
