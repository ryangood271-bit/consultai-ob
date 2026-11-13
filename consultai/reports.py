"""Markdown briefing generator. Never shows an APPROVED banner unless the run is actually
in APPROVED_INTERNAL state."""

from __future__ import annotations

from datetime import datetime, timezone

from .metrics import YearMetrics
from .review import Run
from .schemas import RunState

_PDF_UNICODE_REPLACEMENTS = {
    "→": "->",
    "—": "-",
    "–": "-",
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "⚠️": "[!]",
    "⚠": "[!]",
    "✅": "[OK]",
    "❌": "[X]",
}


def _sanitize_for_pdf(text: str) -> str:
    for old, new in _PDF_UNICODE_REPLACEMENTS.items():
        text = text.replace(old, new)
    # Safety net for any other character the core PDF font can't render.
    return text.encode("latin-1", errors="replace").decode("latin-1")


def render_briefing_pdf(markdown_text: str) -> bytes:
    """Convert the markdown briefing into a simple, readable PDF for submission.

    Best-effort formatting (headings, bold, bullet lists) via markdown -> HTML -> PDF; not
    pixel-perfect, but a genuine, inspectable downloadable document.
    """
    import markdown as md_lib
    from fpdf import FPDF

    html = md_lib.markdown(_sanitize_for_pdf(markdown_text))

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.write_html(html)
    return bytes(pdf.output())


def _direction(change: float, positive_word: str, negative_word: str) -> str:
    if change is None:
        return "stayed about the same"
    if change > 0.5:
        return f"{positive_word} by {abs(change):.1f}%"
    if change < -0.5:
        return f"{negative_word} by {abs(change):.1f}%"
    return "stayed about the same"


def overall_rating(period_summary: dict) -> dict:
    """A deterministic, plain-English rollup of revenue/profit/margin trends into one simple
    label. NOT an AI judgment call — documented point thresholds on numbers already computed
    elsewhere (reproducible, explainable), but the raw point math is an internal detail — what
    the user sees is a label plus a one-sentence reason, not a score.

    Internal scoring (not shown to the user):
      Operating margin change:  >=+2pp: +2   >+0.5pp: +1   <=-5pp: -2   <-0.5pp: -1   else 0
      Revenue change:           >=+5%: +1    <=-5%: -1    else 0
      Operating profit change:  >=+5%: +1    <=-5%: -1    else 0
    Margin is weighted heaviest because it's the clearest single signal of whether the business
    is becoming more or less profitable per dollar of sales, independent of its size.
    """
    margin_pp = period_summary.get("operating_margin_change_pp", 0.0)
    revenue_pct = period_summary.get("revenue_change_pct") or 0.0
    profit_pct = period_summary.get("operating_profit_change_pct") or 0.0
    margin_start = period_summary.get("operating_margin_start_pct")
    margin_end = period_summary.get("operating_margin_end_pct")

    points = 0
    if margin_pp >= 2:
        points += 2
    elif margin_pp > 0.5:
        points += 1
    elif margin_pp <= -5:
        points -= 2
    elif margin_pp < -0.5:
        points -= 1

    points += 1 if revenue_pct >= 5 else (-1 if revenue_pct <= -5 else 0)
    points += 1 if profit_pct >= 5 else (-1 if profit_pct <= -5 else 0)

    if points >= 3:
        label, emoji = "Doing well", "🟢"
    elif points >= 1:
        label, emoji = "Generally positive", "🟢"
    elif points == 0:
        label, emoji = "Mixed", "🟡"
    elif points >= -2:
        label, emoji = "Worth watching", "🟠"
    else:
        label, emoji = "Struggling", "🔴"

    if margin_start is not None and margin_end is not None:
        if margin_pp > 0.5:
            why = (f"mainly because operating margin improved from {margin_start:.1f}% to "
                    f"{margin_end:.1f}% — it's keeping more of each sales dollar as profit")
        elif margin_pp < -0.5:
            why = (f"mainly because operating margin fell from {margin_start:.1f}% to "
                    f"{margin_end:.1f}% — it's keeping less of each sales dollar as profit")
        else:
            why = f"because operating margin held roughly steady around {margin_end:.1f}%"
    else:
        why = "based on the revenue and profit trend"

    extra = []
    if revenue_pct >= 5:
        extra.append(f"revenue grew {revenue_pct:.0f}%")
    elif revenue_pct <= -5:
        extra.append(f"revenue shrank {abs(revenue_pct):.0f}%")
    if profit_pct >= 5:
        extra.append(f"profit grew {profit_pct:.0f}%")
    elif profit_pct <= -5:
        extra.append(f"profit fell {abs(profit_pct):.0f}%")
    if extra:
        why += ", and " + " and ".join(extra)
    why += "."

    return {"label": label, "emoji": emoji, "points": points, "why": why}


def plain_english_overview(metrics: list[YearMetrics], period_summary: dict) -> str:
    """A deterministic, jargon-free paragraph explaining the headline trend.

    No AI involved — this is plain arithmetic translated into plain sentences, so it's always
    available even before (or without) any AI call.
    """
    first, last = metrics[0], metrics[-1]
    rev_change = period_summary.get("revenue_change_pct")
    profit_change = period_summary.get("operating_profit_change_pct")
    margin_change_pp = period_summary.get("operating_margin_change_pp", 0.0)

    rev_phrase = _direction(rev_change, "grew", "shrank")
    profit_phrase = _direction(profit_change, "grew", "shrank")

    if margin_change_pp > 0.5:
        margin_sentence = (
            f"The company is now keeping MORE of each dollar of revenue as profit than it used to "
            f"(operating margin went from {first.operating_margin_pct:.1f}% to {last.operating_margin_pct:.1f}%) "
            f"— that's a good sign."
        )
    elif margin_change_pp < -0.5:
        margin_sentence = (
            f"The company is now keeping LESS of each dollar of revenue as profit than it used to "
            f"(operating margin went from {first.operating_margin_pct:.1f}% to {last.operating_margin_pct:.1f}%) "
            f"— that's worth paying attention to."
        )
    else:
        margin_sentence = (
            f"How much profit it keeps per dollar of revenue (operating margin) has stayed roughly "
            f"flat, around {last.operating_margin_pct:.1f}%."
        )

    warning = ""
    if rev_change is not None and profit_change is not None and rev_change > 0 and profit_change < 0:
        warning = (
            " ⚠️ This is a pattern worth flagging: the company is bringing in more money overall, "
            "but costs are rising even faster, so less of it turns into actual profit."
        )

    return (
        f"From {first.year} to {last.year}, revenue (total money coming in) {rev_phrase}, and "
        f"operating profit (what's left after costs) {profit_phrase}. {margin_sentence}{warning}"
    )


def render_briefing(
    run: Run,
    company_name: str,
    management_question: str,
    metrics: list[YearMetrics],
    period_summary: dict,
    verified_findings: list,
    scenario_result,
    ai_model: str | None,
    ai_status: str,
    ai_raw_json: dict | None = None,
) -> str:
    status_banner = (
        "**STATUS: APPROVED_INTERNAL**" if run.state == RunState.APPROVED_INTERNAL
        else f"**STATUS: {run.state.value} — DRAFT, HUMAN REVIEW REQUIRED**"
    )

    rating = overall_rating(period_summary)

    lines = [
        f"# Preliminary Consulting Briefing — {company_name}",
        "",
        status_banner,
        "",
        f"**{rating['emoji']} Overall trend: {rating['label']}** — this is {rating['why']}",
        "",
        f"*Educational prototype output. Fictional/synthetic data only. Run ID: {run.run_id}. "
        f"Generated: {datetime.now(timezone.utc).isoformat()}*",
        "",
        "## Management Question",
        management_question,
        "",
        "## Key Metrics (computed deterministically in Python, not by the AI model)",
    ]
    for m in metrics:
        lines.append(
            f"- **{m.year}**: revenue {m.revenue_m:.1f}M, operating profit {m.operating_profit_m:.1f}M, "
            f"operating margin {m.operating_margin_pct:.2f}%, COGS share {m.cogs_share_pct:.2f}%"
        )
    lines.append("")
    lines.append(f"- Revenue change {period_summary['start_year']}→{period_summary['end_year']}: "
                 f"{period_summary['revenue_change_pct']:.2f}%")
    lines.append(f"- Operating profit change: {period_summary['operating_profit_change_pct']:.2f}%")
    lines.append(f"- Operating margin change: {period_summary['operating_margin_change_pp']:.2f} pp")

    lines += ["", "## Ranked Findings (code-detected, AI-interpreted)", ""]
    if ai_status != "OK":
        lines.append(f"**NO AI GENERATED** — {ai_status}")
    else:
        lines.append(f"*AI model used: {ai_model}*")
        for f in verified_findings:
            lines.append(f"- **[{f.status}]** `{f.issue_id}`: {f.summary} (evidence: {f.evidence_refs})")

        raw = ai_raw_json or {}
        if raw.get("why_important"):
            lines += ["", "### Why this matters", raw["why_important"]]
        if raw.get("hypotheses"):
            lines += ["", "### Possible explanations (unverified)"]
            lines += [f"- {h}" for h in raw["hypotheses"]]
        if raw.get("proposed_investigations"):
            lines += ["", "### What to investigate next"]
            lines += [f"- {i}" for i in raw["proposed_investigations"]]
        if raw.get("strategic_options"):
            lines += ["", "### Options to consider (requires manager sign-off)"]
            lines += [f"- {o}" for o in raw["strategic_options"]]
        if raw.get("source_conflicts"):
            lines += ["", "### Source conflicts flagged by the AI"]
            lines += [f"- {c}" for c in raw["source_conflicts"]]

    if scenario_result is not None:
        lines += [
            "",
            "## Scenario Simulation (mechanical, illustrative only)",
            f"- Baseline {scenario_result.baseline_year}: profit {scenario_result.baseline_operating_profit_m:.1f}M, "
            f"margin {scenario_result.baseline_operating_margin_pct:.2f}%",
            f"- Scenario (COGS {scenario_result.cogs_pct_change:+.1f}%, revenue {scenario_result.revenue_pct_change:+.1f}%): "
            f"projected profit {scenario_result.new_operating_profit_m:.1f}M, "
            f"margin {scenario_result.new_operating_margin_pct:.2f}%, "
            f"delta {scenario_result.profit_delta_m:+.1f}M",
            f"- Assumptions: {scenario_result.assumptions}",
        ]

    lines += ["", "## Review Decisions", ""]
    if not run.decisions:
        lines.append("*No review decisions recorded yet.*")
    for d in run.decisions:
        lines.append(f"- {d.timestamp} — {d.reviewer_name} ({d.reviewer_role}): **{d.decision}** — {d.reason}")

    lines += [
        "",
        "## Limitations",
        "- All findings are observed patterns in synthetic data, not proven causes.",
        "- This is a hypothetical prototype; no real client, firm system, or confidential data is involved.",
        "- Nothing in this document authorizes external distribution or action.",
    ]

    return "\n".join(lines)
