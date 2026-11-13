"""Purpose-built PDF report: charts, a styled metrics table, an executive summary, and an
action-items list with owners — the things an actual consulting deliverable usually has that a
plain markdown-to-PDF conversion doesn't give you.

Kept separate from reports.py (which generates the markdown shown live in the app and used for
the .md download) because this builds its own layout directly with fpdf2 rather than converting
markdown, so it can embed real chart images and tables.
"""

from __future__ import annotations

import io
import re
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF, XPos, YPos
from fpdf.fonts import FontFace

from .metrics import YearMetrics
from .reports import overall_rating
from .review import Run
from .schemas import RunState

COLOR_REVENUE = "#2563EB"
COLOR_PROFIT = "#F97316"
COLOR_COGS = "#EF4444"
COLOR_OPEX = "#F59E0B"
COLOR_PROFIT_BAR = "#10B981"
HEADER_BLUE = (30, 58, 138)


def _ascii_safe(text: str) -> str:
    replacements = {
        "→": "->", "—": "-", "–": "-",
        "‘": "'", "’": "'", "“": '"', "”": '"',
        "⚠️": "[!]", "⚠": "[!]", "✅": "[OK]", "❌": "[X]",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def build_filename(company_name: str, run_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", company_name).strip("_") or "Company"
    return f"{slug}_Consulting_Briefing_{date.today().isoformat()}_{run_id[:6]}.pdf"


def _line_chart_png(years, series: dict, ylabel: str, title: str) -> io.BytesIO:
    fig, ax = plt.subplots(figsize=(6.3, 2.6))
    for label, (values, color) in series.items():
        ax.plot(years, values, marker="o", linewidth=2.5, color=color, label=label)
    ax.set_xticks(years)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.legend(fontsize=8, frameon=False)
    ax.grid(alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160)
    plt.close(fig)
    buf.seek(0)
    return buf


def _cost_breakdown_png(metrics: list[YearMetrics]) -> io.BytesIO:
    years = [m.year for m in metrics]
    cogs = [m.cogs_m for m in metrics]
    opex = [m.operating_expenses_m for m in metrics]
    profit = [m.operating_profit_m for m in metrics]
    bottom_opex = cogs
    bottom_profit = [c + o for c, o in zip(cogs, opex)]

    fig, ax = plt.subplots(figsize=(6.3, 2.6))
    ax.bar(years, cogs, color=COLOR_COGS, label="Cost of Goods Sold")
    ax.bar(years, opex, bottom=bottom_opex, color=COLOR_OPEX, label="Operating Expenses")
    ax.bar(years, profit, bottom=bottom_profit, color=COLOR_PROFIT_BAR, label="Profit")
    ax.set_xticks(years)
    ax.set_ylabel("USD millions", fontsize=9)
    ax.set_title("Where Each Revenue Dollar Goes", fontsize=10, fontweight="bold")
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160)
    plt.close(fig)
    buf.seek(0)
    return buf


def _rating_gauge_png(points: int) -> io.BytesIO:
    """Horizontal gauge matching the app's dashboard gauge: red (struggling) to green (doing
    well), with a marker showing where this run's score falls. No raw numbers shown."""
    import matplotlib.colors as mcolors

    cmap = mcolors.LinearSegmentedColormap.from_list(
        "rating", ["#EF4444", "#F59E0B", "#FACC15", "#84CC16", "#10B981"]
    )
    fig, ax = plt.subplots(figsize=(6.3, 0.9))
    gradient = [[i / 255 for i in range(256)]]
    ax.imshow(gradient, aspect="auto", cmap=cmap, extent=[0, 1, 0, 1])
    pct = max(0.0, min(1.0, (points + 4) / 8))
    ax.axvline(pct, color="#111827", linewidth=3)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels(["Struggling", "Worth watching", "Mixed", "Generally positive", "Doing well"], fontsize=7)
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160)
    plt.close(fig)
    buf.seek(0)
    return buf


class ConsultingPDF(FPDF):
    def __init__(self, company_name: str, status_text: str, run_id: str):
        super().__init__()
        self.company_name = _ascii_safe(company_name)
        self.status_text = _ascii_safe(status_text)
        self.run_id = run_id
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_fill_color(*HEADER_BLUE)
        self.rect(0, 0, 210, 24, "F")
        self.set_text_color(255, 255, 255)
        self.set_xy(10, 5)
        self.set_font("Helvetica", "B", 15)
        self.cell(0, 8, f"{self.company_name} -- Consulting Briefing", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_x(10)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 6, f"Status: {self.status_text}   |   Run ID: {self.run_id}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, f"Educational prototype -- not a real Bain system. Synthetic/illustrative "
                         f"data unless otherwise noted.   Page {self.page_no()}", align="C")

    def section_title(self, text: str):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(30, 58, 138)
        self.cell(0, 9, _ascii_safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def body_text(self, text: str, size: int = 10):
        self.set_font("Helvetica", "", size)
        self.set_x(self.l_margin)
        self.multi_cell(self.epw, 5.5, _ascii_safe(text))
        self.ln(1)

    def bullet_list(self, items: list[str], size: int = 10):
        self.set_font("Helvetica", "", size)
        for item in items:
            self.set_x(self.l_margin)
            self.multi_cell(self.epw, 5.5, f"-  {_ascii_safe(item)}")
        self.ln(1)


def build_pdf_report(
    run: Run,
    company_name: str,
    management_question: str,
    metrics: list[YearMetrics],
    period_summary: dict,
    verified_findings: list,
    ai_raw_json: dict | None,
    ai_model: str | None,
    ai_status: str,
    plain_english_overview: str,
) -> bytes:
    status_text = (
        "APPROVED INTERNAL" if run.state == RunState.APPROVED_INTERNAL
        else f"{run.state.value} -- DRAFT, HUMAN REVIEW REQUIRED"
    )

    pdf = ConsultingPDF(company_name, status_text, run.run_id)
    pdf.add_page()

    # Executive summary
    pdf.section_title("Executive Summary")
    rating = overall_rating(period_summary)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, 7, f"Overall trend: {rating['label']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.image(_rating_gauge_png(rating["points"]), w=160)
    pdf.body_text(f"This is {rating['why']}", size=9)
    exec_summary = plain_english_overview
    raw = ai_raw_json or {}
    bottom_line = ""
    if ai_status == "OK" and raw.get("strategic_options"):
        bottom_line = f" Top recommendation to consider: {raw['strategic_options'][0]}"
    elif ai_status == "OK" and raw.get("proposed_investigations"):
        bottom_line = f" Suggested next step: {raw['proposed_investigations'][0]}"
    pdf.body_text(exec_summary + bottom_line)

    pdf.body_text(f"Engagement question: {management_question}", size=9)

    # Key metrics table
    pdf.ln(2)
    pdf.section_title("Key Metrics")
    headers = ["Year", "Revenue (M)", "Op. Profit (M)", "Op. Margin %", "COGS Share %"]
    rows = [
        [str(m.year), f"{m.revenue_m:,.1f}", f"{m.operating_profit_m:,.1f}",
         f"{m.operating_margin_pct:.1f}%", f"{m.cogs_share_pct:.1f}%"]
        for m in metrics
    ]
    header_style = FontFace(emphasis="BOLD", fill_color=(219, 234, 254))
    with pdf.table(col_widths=(18, 28, 28, 26, 26), text_align="CENTER", headings_style=header_style) as table:
        row = table.row()
        for h in headers:
            row.cell(h)
        for r in rows:
            row = table.row()
            for v in r:
                row.cell(v)
    pdf.ln(2)

    # Charts
    years = [m.year for m in metrics]
    chart1 = _line_chart_png(
        years,
        {"Revenue": ([m.revenue_m for m in metrics], COLOR_REVENUE),
         "Operating Profit": ([m.operating_profit_m for m in metrics], COLOR_PROFIT)},
        "USD millions", "Revenue vs. Operating Profit",
    )
    pdf.image(chart1, w=180)
    chart2 = _line_chart_png(
        years,
        {"Operating Margin %": ([m.operating_margin_pct for m in metrics], COLOR_REVENUE),
         "COGS Share %": ([m.cogs_share_pct for m in metrics], COLOR_PROFIT)},
        "Percent", "Operating Margin vs. COGS Share",
    )
    pdf.image(chart2, w=180)
    chart3 = _cost_breakdown_png(metrics)
    pdf.image(chart3, w=180)

    # Findings & recommendations
    pdf.add_page()
    pdf.section_title("Key Findings")
    if ai_status != "OK":
        pdf.body_text(f"NO AI GENERATED -- {ai_status}")
    else:
        pdf.set_font("Helvetica", "", 10)
        for f in verified_findings:
            tag = "[VERIFIED]" if f.status == "VERIFIED" else "[NEEDS HUMAN VERIFICATION]"
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pdf.epw, 5.5, _ascii_safe(f"{tag} {f.summary}"))
            pdf.ln(1)

        if raw.get("why_important"):
            pdf.section_title("Why This Matters")
            pdf.body_text(raw["why_important"])

        if raw.get("hypotheses"):
            pdf.section_title("Possible Explanations (Unconfirmed)")
            pdf.bullet_list(raw["hypotheses"])

    # Action items with owners
    if ai_status == "OK" and (raw.get("proposed_investigations") or raw.get("strategic_options")):
        pdf.section_title("Recommended Next Steps")
        action_rows = []
        for item in raw.get("proposed_investigations", []):
            action_rows.append(["Investigate", "Associate", item])
        for item in raw.get("strategic_options", []):
            action_rows.append(["Decide", "Manager", item])

        action_header_style = FontFace(emphasis="BOLD", fill_color=(219, 234, 254))
        with pdf.table(col_widths=(25, 25, 130), text_align="LEFT", headings_style=action_header_style) as table:
            row = table.row()
            for h in ["Type", "Owner", "Action"]:
                row.cell(h)
            for r in action_rows:
                row = table.row()
                for v in r:
                    row.cell(_ascii_safe(v))
        pdf.ln(2)

    if ai_status == "OK" and raw.get("limitations"):
        pdf.section_title("Limitations")
        pdf.bullet_list(raw["limitations"])

    pdf.section_title("Review Decisions")
    if not run.decisions:
        pdf.body_text("No review decisions recorded yet.")
    else:
        for d in run.decisions:
            pdf.body_text(f"{d.timestamp} -- {d.reviewer_name} ({d.reviewer_role}): {d.decision} -- {d.reason}", size=9)

    return bytes(pdf.output())
