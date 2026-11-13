# Job & Task Cross-Check

**Method used:** Part 1 option (b) — current job posting checked against an authoritative
task list. No interview was conducted.

## Source 1 — Employer job posting

- **Employer:** Bain & Company
- **Role:** Associate Consultant (Non-MBA), Job ID 10397, General Consulting, Permanent Full-Time
- **Posting URL:** https://www.bain.com/careers/find-a-role/position/?jobid=10397
- **Date reviewed:** 2026-11-12

Quoted responsibilities (short, attributed quotes from the posting text the student supplied):

> "Break down complex problems using hypothesis-led thinking and rigorous analysis to generate insights that shape strategic decisions."

> "Own discrete workstreams such as market sizing, financial modeling, scenario planning, or benchmarking to deliver clear, actionable recommendations."

> "Use data, tools, and digital platforms, which may include Bain's proprietary platforms and emerging capabilities such as generative AI to support analysis and decision making."

> "Adapt and deliver by taking on varied responsibilities depending on the needs of each case, from research and analysis to implementation support."

## Source 2 — Authoritative task list

- **Source:** O*NET OnLine, Management Analysts, 13-1111.00
- **URL:** https://www.onetonline.org/link/details/13-1111.00
- **Status:** **PENDING USER REVIEW.** This cross-check was built from the Bain posting text
  the student provided directly; O*NET's task language was not independently re-fetched in
  this build session, so it is not quoted here. Before submitting, open the O*NET link above,
  confirm it lists tasks matching "collect and organize information... analyze data...
  prepare recommendations... develop solutions," and paste a short attributed quote into this
  section with the date you checked it. Do not submit this file with the PENDING marker left in.

## Task mapping used to scope ConsultAI

| Real job responsibility (Bain posting) | What ConsultAI automates |
|---|---|
| Financial modeling and hypothesis-led analysis | Deterministic revenue/cost/margin calculations + threshold-based issue detection |
| Research and synthesizing data | Structured ingestion and validation of financial, operational, and memo inputs |
| Hypothesis development | AI-drafted, source-cited hypotheses — explicitly labeled unverified |
| Preparing recommendations | Draft strategic options and proposed investigations, gated on human review |
| Client communication | Structured internal briefing output (never sent externally) |

ConsultAI automates a **real subset** of this job — routine financial/operational diagnosis
and first-draft briefing prep — not the full consulting role. Client interaction, final
judgment, and strategic recommendation ownership remain explicitly human (see
`manager_protocol.md`).

**Disclosure:** This project is an independent educational prototype built for a hypothetical
consulting team. It is not an official Bain & Company system, does not use Bain's internal
tools or data, and does not imply Bain affiliation or endorsement.
