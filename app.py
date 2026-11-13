"""ConsultAI — Streamlit app.

Educational prototype for an Organizational Behavior assignment. Not affiliated with,
endorsed by, or built using any confidential systems of Bain & Company. All financial and
operational data in this app is synthetic unless the user explicitly affirms otherwise.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

from consultai import ai_client, audit, claim_verification, ingest, issue_detection, metrics as metrics_mod
from consultai import pdf_report, reports, scenarios, statement_parser, url_fetch, validation
from consultai.review import IllegalTransitionError, ReviewDecision, Run
from consultai.schemas import ALLOWED_MEMO_EXTENSIONS, RunState, ValidationResult

OUTPUTS_ROOT = Path(__file__).parent / "outputs"

st.set_page_config(page_title="ConsultAI — Educational Prototype", layout="wide", page_icon="📊")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;700;800&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, .consultai-banner h1 { font-family: 'Sora', sans-serif; }

    .block-container { padding-top: 1.5rem; }

    .consultai-banner {
        background: linear-gradient(120deg, #4338CA 0%, #2563EB 35%, #06B6D4 70%, #10B981 100%);
        padding: 1.6rem 1.9rem;
        border-radius: 18px;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 10px 30px -10px rgba(37, 99, 235, 0.45);
    }
    .consultai-banner h1 {
        color: white !important;
        margin: 0;
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.03em;
    }
    .consultai-banner p {
        color: #E0F2FE;
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
        font-weight: 500;
    }

    h2, h3 {
        font-weight: 700;
        background: linear-gradient(90deg, #4338CA, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E1B4B 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #E0E7FF !important;
        font-family: 'Inter', sans-serif;
    }
    section[data-testid="stSidebar"] h1 {
        font-family: 'Sora', sans-serif;
        background: linear-gradient(90deg, #A5B4FC, #67E8F9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    section[data-testid="stSidebar"] .stRadio label {
        font-weight: 600;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 0.5rem 0.7rem;
        margin-bottom: 0.35rem;
        transition: background 0.15s ease;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background: rgba(99, 102, 241, 0.35);
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #4338CA, #2563EB, #06B6D4);
        border: none;
        border-radius: 10px;
        font-weight: 700;
        font-family: 'Sora', sans-serif;
        letter-spacing: 0.01em;
        box-shadow: 0 4px 14px -4px rgba(37, 99, 235, 0.5);
    }
    div.stButton > button[kind="primary"]:hover {
        filter: brightness(1.08);
    }

    [data-testid="stMetricValue"] {
        font-family: 'Sora', sans-serif;
        background: linear-gradient(90deg, #4338CA, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    [data-testid="stMetric"] {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #2563EB;
        border-radius: 10px;
        padding: 0.8rem 1rem;
    }

    div[data-testid="stExpander"] {
        border-radius: 10px;
        border: 1px solid #E2E8F0;
    }

    section[data-testid="stSidebar"] code {
        background-color: rgba(255,255,255,0.1);
        color: #67E8F9 !important;
        padding: 2px 5px;
        border-radius: 5px;
        font-size: 0.85em;
        word-break: break-all;
    }
    section[data-testid="stSidebar"] div.stButton > button {
        background: rgba(255,255,255,0.08);
        color: #E0E7FF !important;
        border: 1px solid rgba(165,180,252,0.35);
        border-radius: 8px;
        font-weight: 600;
        font-family: 'Sora', sans-serif;
        width: 100%;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover {
        background: rgba(99,102,241,0.35);
        border-color: rgba(165,180,252,0.7);
        color: white !important;
    }
    </style>
    <div class="consultai-banner">
        <h1>📊 ConsultAI</h1>
        <p>Business Performance &amp; Strategy Assistant — educational prototype, synthetic data only</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "case" not in st.session_state:
    st.session_state.case = None  # type: ignore


def new_case_state(company_name: str, question: str) -> dict:
    run_id = uuid.uuid4().hex[:10]
    run_dir = OUTPUTS_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "company_name": company_name,
        "question": question,
        "run": Run(run_id=run_id),
        "finance_df": None,
        "ops_df": None,
        "memo_text": None,
        "finance_filename": None,
        "ops_filename": None,
        "memo_filename": None,
        "validation_result": ValidationResult(),
        "year_metrics": None,
        "period_summary": None,
        "candidate_issues": None,
        "verified_findings": None,
        "ai_status": "NOT RUN",
        "ai_model": None,
        "ai_error": None,
        "ai_raw_json": None,
        "scenario_result": None,
        "consent_checked": False,
        "parent_run_id": None,
    }


def state_badge(run: Run) -> None:
    if run.state == RunState.APPROVED_INTERNAL:
        st.success(f"Run `{run.run_id}` — APPROVED_INTERNAL")
    elif run.state == RunState.BLOCKED_INPUT:
        st.error(f"Run `{run.run_id}` — BLOCKED_INPUT")
    elif run.state == RunState.REJECTED:
        st.error(f"Run `{run.run_id}` — REJECTED")
    else:
        st.warning(f"Run `{run.run_id}` — {run.state.value} — DRAFT, HUMAN REVIEW REQUIRED")


def rating_gauge_html(points: int) -> str:
    """A simple visual gauge showing where the overall-rating score falls on its scale,
    from struggling (left, red) to doing well (right, green). No numbers shown to the user."""
    pct = max(0, min(100, (points + 4) / 8 * 100))
    return f"""
    <div style="margin: 6px 0 2px 0;">
      <div style="position:relative; height:16px; border-radius:8px;
                  background: linear-gradient(90deg, #EF4444 0%, #F59E0B 25%, #FACC15 50%, #84CC16 75%, #10B981 100%);">
        <div style="position:absolute; left:calc({pct}% - 3px); top:-5px; width:6px; height:26px;
                    background:#111827; border-radius:3px; box-shadow:0 0 0 2px white;"></div>
      </div>
      <div style="display:flex; justify-content:space-between; font-size:0.72rem; color:#64748B; margin-top:4px;">
        <span>Struggling</span><span>Worth watching</span><span>Mixed</span><span>Generally positive</span><span>Doing well</span>
      </div>
    </div>
    """


st.sidebar.title("ConsultAI")
st.sidebar.caption("Educational prototype — synthetic data only. Not a real Bain system.")
page = st.sidebar.radio(
    "Navigate",
    [
        "1. Case Setup",
        "2. Analysis Dashboard",
        "3. Findings & Recommendations",
        "4. Scenario Simulator",
        "5. Risks & Human Review",
        "6. Briefing & Audit Trail",
    ],
)

case = st.session_state.case

# This must run BEFORE any page below instantiates a widget with these same keys (e.g. the
# Case Setup company-name field) — Streamlit forbids changing a widget's session_state value
# after that widget has already been created in the same script run.
if st.sidebar.button("Reset / New Case"):
    st.session_state.case = None
    st.session_state.cs_company_name = ""
    st.session_state.cs_question = ""
    st.session_state.case_finance_draft = None
    st.session_state.case_finance_notes = []
    st.session_state.case_finance_company = None
    st.rerun()

if case is not None:
    state_badge(case["run"])

# ---------------------------------------------------------------------------
# PAGE 1 — CASE SETUP
# ---------------------------------------------------------------------------
if page == "1. Case Setup":
    st.header("Case Setup")
    st.caption(
        "Only the financial statement is required. Operations data and a strategy memo are "
        "optional extras — skip them if you don't have them."
    )

    if "cs_company_name" not in st.session_state:
        st.session_state.cs_company_name = ""
    if "cs_question" not in st.session_state:
        st.session_state.cs_question = ""

    company_name = st.text_input("Company name", key="cs_company_name", placeholder="e.g. Apple Inc.")
    question = st.text_area(
        "What do you want analyzed? (plain English is fine)",
        key="cs_question", height=100,
        placeholder="e.g. Analyze this company's financial performance. What stands out, and what should be investigated first?",
    )

    if "case_finance_draft" not in st.session_state:
        st.session_state.case_finance_draft = None
    if "case_finance_notes" not in st.session_state:
        st.session_state.case_finance_notes = []
    if "case_finance_company" not in st.session_state:
        st.session_state.case_finance_company = None

    st.subheader("Financial statement — required")
    cs_tab_upload, cs_tab_paste, cs_tab_url = st.tabs(["Upload file", "Paste text", "Paste a link"])

    finance_file = None
    with cs_tab_upload:
        finance_file = st.file_uploader("Upload CSV/XLSX", type=["csv", "xlsx"], key="cs_finance_upload")

    with cs_tab_paste:
        cs_pasted = st.text_area("Paste the income statement text", height=180, key="cs_finance_paste")
        if st.button("Extract with AI", key="cs_extract_paste"):
            try:
                result = statement_parser.extract_income_statement(cs_pasted)
                st.session_state.case_finance_draft = pd.DataFrame(result.years)
                st.session_state.case_finance_notes = result.extraction_notes
                st.session_state.case_finance_company = result.company_name
                st.success(f"Extracted with model `{result.model}`. Review it below before running.")
            except ai_client.NoAPIKeyError as e:
                st.error(str(e))
            except (statement_parser.ExtractionSchemaError, ai_client.AICallError) as e:
                st.error(f"Extraction failed, nothing was fabricated: {e}")

    with cs_tab_url:
        cs_url = st.text_input("Income statement page URL (e.g. stockanalysis.com)", key="cs_finance_url")
        if st.button("Fetch & extract with AI", key="cs_extract_url"):
            try:
                raw = url_fetch.fetch_url_text(cs_url) if cs_url else ""
                if not raw:
                    st.error("Enter a URL first.")
                else:
                    result = statement_parser.extract_income_statement(raw)
                    st.session_state.case_finance_draft = pd.DataFrame(result.years)
                    st.session_state.case_finance_notes = result.extraction_notes
                    st.session_state.case_finance_company = result.company_name
                    st.success(f"Extracted with model `{result.model}`. Review it below before running.")
            except url_fetch.UrlFetchError as e:
                st.error(str(e))
            except ai_client.NoAPIKeyError as e:
                st.error(str(e))
            except (statement_parser.ExtractionSchemaError, ai_client.AICallError) as e:
                st.error(f"Extraction failed, nothing was fabricated: {e}")

    if st.session_state.case_finance_draft is not None:
        st.warning("AI-EXTRACTED DRAFT — review every cell before running.")
        st.caption("Column names below are technical labels (e.g. 'cogs_m' means 'Cost of Goods Sold, in USD millions') — hover a header for the full description.")
        st.session_state.case_finance_draft = st.data_editor(
            st.session_state.case_finance_draft,
            num_rows="dynamic",
            key="cs_finance_editor",
            column_config={
                "year": st.column_config.NumberColumn("Year", help="Fiscal year", format="%d"),
                "revenue_m": st.column_config.NumberColumn("Revenue (revenue_m)", help="Total revenue, in USD millions"),
                "cogs_m": st.column_config.NumberColumn("Cost of Goods Sold (cogs_m)", help="Direct cost of producing goods/services, in USD millions"),
                "operating_expenses_m": st.column_config.NumberColumn("Operating Expenses (operating_expenses_m)", help="All other operating costs (SG&A, D&A, etc.), in USD millions"),
                "reported_operating_profit_m": st.column_config.NumberColumn("Operating Profit (reported_operating_profit_m)", help="Revenue minus COGS minus Operating Expenses, in USD millions"),
            },
        )
        if st.session_state.case_finance_notes:
            with st.expander("Extraction notes"):
                for n in st.session_state.case_finance_notes:
                    st.write(f"- {n}")
        if st.button("Clear extracted draft (use an uploaded file instead)"):
            st.session_state.case_finance_draft = None
            st.rerun()

    with st.expander("Optional: add operations data and/or a strategy memo for a richer analysis"):
        ops_file = st.file_uploader("Operations data (CSV/XLSX) — optional", type=["csv", "xlsx"])
        memo_file = st.file_uploader("Strategy memo / goals & constraints (TXT/PDF) — optional", type=["txt", "pdf"])

    consent = st.checkbox(
        "I affirm this data is synthetic, publicly available, or explicitly approved for use with "
        "a public AI API. No confidential or identifying information is included."
    )

    run_clicked = st.button("Run validation & calculations", type="primary")

    has_extracted_draft = st.session_state.case_finance_draft is not None

    if run_clicked:
        if not finance_file and not has_extracted_draft:
            st.error("The financial statement is required — upload a file, or paste/link one and click Extract.")
        elif not consent:
            st.error("You must affirm the data-safety checkbox before running the pipeline.")
        else:
            case = new_case_state(company_name, question)
            case["consent_checked"] = True
            vr = ValidationResult()

            if finance_file is not None:
                finance_name = finance_file.name
                try:
                    finance_bytes = finance_file.getvalue()
                    ingest.save_raw_file(finance_bytes, finance_name, case["run_dir"], {".csv", ".xlsx"})
                    finance_df = ingest.read_tabular(finance_bytes, finance_name)
                    case["finance_filename"] = finance_name
                    case["finance_df"] = finance_df
                    vr.extend(validation.validate_finance_df(finance_df, finance_name))
                except Exception as e:  # noqa: BLE001
                    from consultai.schemas import Severity, ValidationIssue
                    vr.issues.append(ValidationIssue(Severity.BLOCKING, "FINANCE_INGEST_ERROR", str(e), finance_name))
            else:
                finance_name = f"ai_extracted_{company_name.replace(' ', '_')}.csv"
                try:
                    finance_df = st.session_state.case_finance_draft
                    finance_bytes = finance_df.to_csv(index=False).encode("utf-8")
                    ingest.save_raw_file(finance_bytes, finance_name, case["run_dir"], {".csv"})
                    case["finance_filename"] = finance_name
                    case["finance_df"] = finance_df
                    vr.extend(validation.validate_finance_df(finance_df, finance_name))
                except Exception as e:  # noqa: BLE001
                    from consultai.schemas import Severity, ValidationIssue
                    vr.issues.append(ValidationIssue(Severity.BLOCKING, "FINANCE_INGEST_ERROR", str(e), finance_name))

            if ops_file is not None:
                try:
                    ops_bytes = ops_file.getvalue()
                    ingest.save_raw_file(ops_bytes, ops_file.name, case["run_dir"], {".csv", ".xlsx"})
                    ops_df = ingest.read_tabular(ops_bytes, ops_file.name)
                    case["ops_filename"] = ops_file.name
                    case["ops_df"] = ops_df
                    if case["finance_df"] is not None:
                        vr.extend(validation.validate_operations_df(ops_df, case["finance_df"], ops_file.name))
                except Exception as e:  # noqa: BLE001
                    from consultai.schemas import Severity, ValidationIssue
                    vr.issues.append(ValidationIssue(Severity.BLOCKING, "OPS_INGEST_ERROR", str(e), ops_file.name))

            if memo_file is not None:
                try:
                    memo_bytes = memo_file.getvalue()
                    ingest.save_raw_file(memo_bytes, memo_file.name, case["run_dir"], ALLOWED_MEMO_EXTENSIONS)
                    memo_text = ingest.read_memo_text(memo_bytes, memo_file.name)
                    case["memo_filename"] = memo_file.name
                    case["memo_text"] = memo_text
                    vr.extend(validation.scan_sensitive_data(memo_text, memo_file.name))
                except Exception as e:  # noqa: BLE001
                    from consultai.schemas import Severity, ValidationIssue
                    vr.issues.append(ValidationIssue(Severity.BLOCKING, "MEMO_INGEST_ERROR", str(e), memo_file.name))

            case["validation_result"] = vr
            case["run"].set_validation_outcome(vr.is_blocked)

            audit.append_event(case["run_dir"], "VALIDATION_RUN", {
                "blocking_count": len(vr.blocking),
                "warning_count": len(vr.warnings),
                "blocking_codes": [i.code for i in vr.blocking],
            })

            if not vr.is_blocked:
                year_metrics = metrics_mod.compute_year_metrics(case["finance_df"], case["ops_df"])
                case["year_metrics"] = year_metrics
                case["period_summary"] = metrics_mod.summarize_period(year_metrics)
                case["candidate_issues"] = issue_detection.detect_issues(
                    year_metrics, case["finance_filename"], case["ops_filename"], case["memo_text"]
                )
                audit.append_event(case["run_dir"], "METRICS_COMPUTED", {"years": [m.year for m in year_metrics]})

            st.session_state.case = case
            st.rerun()

    if case is not None:
        vr = case["validation_result"]
        if vr.issues:
            st.subheader("Validation results")
            for i in vr.blocking:
                st.error(f"BLOCKING [{i.code}] {i.file}" + (f" row {i.row}" if i.row else "") + f": {i.message}" +
                         (f" (expected {i.expected}, observed {i.observed})" if i.expected else ""))
            for i in vr.warnings:
                st.warning(f"WARNING [{i.code}] {i.file}: {i.message}")
            if not vr.is_blocked:
                st.success("No blocking errors. Calculations are ready — see Analysis Dashboard.")
        else:
            st.info("No case run yet.")

# ---------------------------------------------------------------------------
# PAGE 2 — ANALYSIS DASHBOARD
# ---------------------------------------------------------------------------
elif page == "2. Analysis Dashboard":
    st.header("Analysis Dashboard")
    if case is None or case["year_metrics"] is None:
        st.info("Run a case with no blocking errors on the Case Setup page first.")
    else:
        import altair as alt

        rating = reports.overall_rating(case["period_summary"])
        st.markdown(f"## {rating['emoji']} Overall trend: {rating['label']}")
        st.markdown(rating_gauge_html(rating["points"]), unsafe_allow_html=True)
        st.caption(f"This is {rating['why']}")

        st.markdown("### 📖 In plain English")
        st.info(reports.plain_english_overview(case["year_metrics"], case["period_summary"]))
        st.caption(
            "👉 Want specific recommendations and things to watch out for? Go to "
            "**'3. Findings & Recommendations'** and click 'Call Anthropic API now' — that's where "
            "the AI's advice shows up, not on this page."
        )

        df = pd.DataFrame([vars(m) for m in case["year_metrics"]])

        def line_chart(df, series: dict):
            long_df = df.melt(id_vars="year", value_vars=list(series.keys()), var_name="metric", value_name="value")
            long_df["label"] = long_df["metric"].map({k: v[0] for k, v in series.items()})
            colors = alt.Scale(domain=[v[0] for v in series.values()], range=[v[1] for v in series.values()])
            chart = (
                alt.Chart(long_df)
                .mark_line(point=True, strokeWidth=3)
                .encode(
                    x=alt.X("year:O", title="Year"),
                    y=alt.Y("value:Q", title=""),
                    color=alt.Color("label:N", scale=colors, legend=alt.Legend(title="")),
                    tooltip=["year", "label", "value"],
                )
                .properties(height=300)
            )
            return chart

        st.subheader("Revenue vs. operating profit (USD millions)")
        st.caption(
            "🔵 **Blue line = Revenue** — total money coming in. 🟠 **Orange line = Operating profit** "
            "— what's actually left after paying costs. **How to read it:** if blue is climbing but "
            "orange is flat or falling, the company is making more sales but keeping less of each "
            "dollar — costs are growing faster than revenue."
        )
        st.altair_chart(
            line_chart(df, {"revenue_m": ("Revenue", "#2563EB"), "operating_profit_m": ("Operating Profit", "#F97316")}),
            use_container_width=True,
        )

        st.subheader("Operating margin and COGS share (%)")
        st.caption(
            "🔵 **Blue line = Operating margin** — the % of each revenue dollar kept as profit (higher "
            "is better). 🟠 **Orange line = COGS share** — the % of each revenue dollar spent on direct "
            "costs (lower is better). **How to read it:** if orange is rising while blue is falling, "
            "rising direct costs are likely squeezing profit."
        )
        st.altair_chart(
            line_chart(df, {"operating_margin_pct": ("Operating Margin %", "#2563EB"), "cogs_share_pct": ("COGS Share %", "#F97316")}),
            use_container_width=True,
        )

        st.subheader("Where every revenue dollar goes, by year")
        st.caption(
            "Each bar is one year's total revenue, split into: 🟥 **Cost of goods sold**, "
            "🟨 **Operating expenses**, and 🟩 **Profit** (what's left over). A shrinking green "
            "slice over time means less of each dollar ends up as profit."
        )
        breakdown = df.melt(
            id_vars="year",
            value_vars=["cogs_m", "operating_expenses_m", "operating_profit_m"],
            var_name="category",
            value_name="amount",
        )
        breakdown["label"] = breakdown["category"].map(
            {"cogs_m": "Cost of goods sold", "operating_expenses_m": "Operating expenses", "operating_profit_m": "Profit"}
        )
        bar_colors = alt.Scale(
            domain=["Cost of goods sold", "Operating expenses", "Profit"],
            range=["#EF4444", "#F59E0B", "#10B981"],
        )
        bar_chart = (
            alt.Chart(breakdown)
            .mark_bar()
            .encode(
                x=alt.X("year:O", title="Year"),
                y=alt.Y("amount:Q", title="USD millions", stack="zero"),
                color=alt.Color("label:N", scale=bar_colors, legend=alt.Legend(title="")),
                tooltip=["year", "label", "amount"],
            )
            .properties(height=300)
        )
        st.altair_chart(bar_chart, use_container_width=True)

        with st.expander("📊 Full numbers behind these charts, year by year"):
            friendly = df.rename(columns={
                "year": "Year", "revenue_m": "Revenue (M)", "cogs_m": "COGS (M)",
                "operating_expenses_m": "Operating Expenses (M)", "operating_profit_m": "Operating Profit (M)",
                "gross_profit_m": "Gross Profit (M)", "gross_margin_pct": "Gross Margin %",
                "operating_margin_pct": "Operating Margin %", "cogs_share_pct": "COGS Share %",
                "opex_share_pct": "Opex Share %",
            }).set_index("Year")
            st.dataframe(friendly)

        with st.expander("🔧 Raw summary stats (for the technically curious)"):
            st.json(case["period_summary"])

# ---------------------------------------------------------------------------
# PAGE 3 — RANKED ISSUE FINDINGS
# ---------------------------------------------------------------------------
elif page == "3. Findings & Recommendations":
    st.header("Findings & Recommendations")
    st.caption("First: what the numbers flag as worth worrying about. Then, once you run the AI step below: what to think about doing next.")
    if case is None or case["candidate_issues"] is None:
        st.info("Run a case with no blocking errors on the Case Setup page first.")
    else:
        st.subheader("Code-detected candidate issues (ranked)")
        st.caption("Scoring: impact 50% + evidence strength 30% + relevance to stated goal 20%, each sub-score 1-5.")
        top3 = issue_detection.top_n(case["candidate_issues"], 3)
        for issue in top3:
            with st.expander(f"{issue.title}  —  score {issue.weighted_score:.2f}/5  [{issue.label}]"):
                st.write(issue.description)
                st.write("Evidence:")
                for ev in issue.evidence:
                    st.code(f"{ev.file} / {ev.year} / {ev.column} = {ev.value}")
                st.write(f"impact={issue.impact_score} evidence={issue.evidence_score} relevance={issue.relevance_score}")

        if not top3:
            st.info("No candidate issues crossed the detection thresholds for this dataset.")

        st.divider()
        st.subheader("Generate AI insight draft")
        st.caption(
            "Sends the validated metrics summary, the candidate issues above, and the memo "
            "text (labeled untrusted) to the configured Anthropic model. Requires ANTHROPIC_API_KEY."
        )
        sanitized_preview = {
            "management_question": case["question"],
            "validated_metrics_summary": case["period_summary"],
            "candidate_issues": [i.issue_id for i in top3],
            "memo_excerpt_chars_sent": len(case["memo_text"] or ""),
        }
        with st.expander("Preview of sanitized content that would be sent"):
            st.json(sanitized_preview)

        if st.button("Call Anthropic API now", type="primary"):
            payload_issues = [
                {
                    "issue_id": i.issue_id,
                    "title": i.title,
                    "description": i.description,
                    "evidence": [vars(e) for e in i.evidence],
                }
                for i in top3
            ]
            try:
                result = ai_client.generate_briefing(
                    metrics_summary=case["period_summary"],
                    candidate_issues_payload=payload_issues,
                    memo_excerpt=case["memo_text"] or "",
                    management_question=case["question"],
                )
                case["ai_status"] = "OK"
                case["ai_model"] = result.model
                case["ai_raw_json"] = result.raw_json
                verified = claim_verification.verify_findings(result.top_findings, case["candidate_issues"])
                case["verified_findings"] = verified
                case["run"].mark_ai_draft_ready()
                audit.append_event(case["run_dir"], "AI_CALL_SUCCESS", {"model": result.model, "raw_response": result.raw_json})
                st.success(f"AI draft generated using model `{result.model}`.")
            except ai_client.NoAPIKeyError as e:
                case["ai_status"] = "NO AI GENERATED — ANTHROPIC_API_KEY not set"
                case["ai_error"] = str(e)
                audit.append_event(case["run_dir"], "AI_CALL_NO_KEY", {"error": str(e)})
                st.error(str(e))
            except (ai_client.AIResponseSchemaError, ai_client.AICallError) as e:
                case["ai_status"] = f"NO AI GENERATED — {e}"
                case["ai_error"] = str(e)
                audit.append_event(case["run_dir"], "AI_CALL_FAILED", {"error": str(e)})
                st.error(f"AI call failed, no content was fabricated: {e}")
            st.session_state.case = case
            st.rerun()

        if case["ai_status"] == "OK" and case["verified_findings"]:
            raw = case.get("ai_raw_json") or {}

            st.divider()
            st.header("💡 Bottom line: what this means and what to do")
            st.caption(
                "Everything below is the AI's draft interpretation of the numbers above — read it "
                "critically, it's a starting point for a human, not a verified conclusion."
            )

            if raw.get("why_important"):
                st.markdown("### 📖 What's going on, in plain terms")
                st.write(raw["why_important"])

            if raw.get("hypotheses"):
                st.markdown("### 🤔 Possible reasons why (unconfirmed — just theories to test)")
                for h in raw["hypotheses"]:
                    st.write(f"- {h}")

            if raw.get("proposed_investigations"):
                st.markdown("### ⚠️ Things worth worrying about / checking before you act")
                for inv in raw["proposed_investigations"]:
                    st.write(f"- {inv}")

            if raw.get("strategic_options"):
                st.markdown("### ✅ Recommendations to consider (a manager still has to sign off)")
                for opt in raw["strategic_options"]:
                    st.write(f"- {opt}")

            if raw.get("source_conflicts"):
                st.markdown("### 🚩 Conflicting or suspicious information the AI noticed")
                for c in raw["source_conflicts"]:
                    st.write(f"- {c}")

            with st.expander("🔎 The specific data points behind these findings (for fact-checking)"):
                for f in case["verified_findings"]:
                    tag = "✅ confirmed against the real numbers" if f.status == "VERIFIED" else "⚠️ NOT independently confirmed"
                    st.write(f"**{f.issue_id}** ({tag}): {f.summary}")
                if raw.get("limitations"):
                    st.markdown("**What this analysis can't tell you:**")
                    for lim in raw["limitations"]:
                        st.write(f"- {lim}")
        elif case["ai_status"] not in ("NOT RUN", "OK"):
            st.warning(f"AI status: {case['ai_status']}")

# ---------------------------------------------------------------------------
# PAGE 4 — SCENARIO SIMULATOR
# ---------------------------------------------------------------------------
elif page == "4. Scenario Simulator":
    st.header("Scenario Simulator")
    st.caption(
        "A 'what if' calculator — move the sliders to see how changing costs or revenue would "
        "affect profit, holding everything else constant. Pure math, no AI, not a forecast."
    )
    if case is None or case["year_metrics"] is None:
        st.info("Run a case with no blocking errors on the Case Setup page first.")
    else:
        baseline = case["year_metrics"][-1]
        st.markdown(f"**Starting point ({baseline.year} actuals):**")
        b1, b2, b3 = st.columns(3)
        b1.metric("Revenue (M)", f"{baseline.revenue_m:,.1f}")
        b2.metric("Operating profit (M)", f"{baseline.operating_profit_m:,.1f}")
        b3.metric("Operating margin", f"{baseline.operating_margin_pct:.1f}%")

        st.divider()
        st.markdown("**Now try changing these:**")
        cogs_pct = st.slider("Cut costs (COGS) by...", 0, 20, 5, format="%d%%")
        rev_pct = st.slider("Grow revenue by...", 0, 15, 0, format="%d%%")
        result = scenarios.run_scenario(baseline, cogs_pct_change=cogs_pct, revenue_pct_change=rev_pct)
        case["scenario_result"] = result
        st.session_state.case = case

        st.markdown("**Result:**")
        col1, col2, col3 = st.columns(3)
        col1.metric("New operating profit (M)", f"{result.new_operating_profit_m:,.1f}",
                    delta=f"{result.profit_delta_m:+,.1f}")
        col2.metric("New operating margin", f"{result.new_operating_margin_pct:.1f}%",
                    delta=f"{result.new_operating_margin_pct - result.baseline_operating_margin_pct:+.1f} pp")
        col3.metric("Baseline profit (M)", f"{result.baseline_operating_profit_m:,.1f}")

        st.markdown("**Before vs. after, side by side:**")
        compare_df = pd.DataFrame(
            {
                "Operating profit (M)": [result.baseline_operating_profit_m, result.new_operating_profit_m],
                "Operating margin (%)": [result.baseline_operating_margin_pct, result.new_operating_margin_pct],
            },
            index=["Baseline", "Scenario"],
        )
        chart_col1, chart_col2 = st.columns(2)
        chart_col1.bar_chart(compare_df[["Operating profit (M)"]])
        chart_col2.bar_chart(compare_df[["Operating margin (%)"]])

        st.caption(result.assumptions)

# ---------------------------------------------------------------------------
# PAGE 5 — RISKS & HUMAN REVIEW
# ---------------------------------------------------------------------------
elif page == "5. Risks & Human Review":
    st.header("Risks & Human Review")
    st.caption(
        "📌 **What this page is for:** this is the 'don't just trust the AI' checkpoint. It shows "
        "any data problems or unverified AI claims, and it's where a human (you, playing the role "
        "of reviewer) actually signs off before anything counts as final — nothing is approved "
        "automatically."
    )
    if case is None:
        st.info("Run a case on the Case Setup page first.")
    else:
        run: Run = case["run"]
        vr = case["validation_result"]

        st.subheader("Blocking errors (must be corrected before any approval)")
        if vr.blocking:
            for i in vr.blocking:
                st.error(f"[{i.code}] {i.message}")
        else:
            st.success("None.")

        st.subheader("Warnings (human attention, not auto-blocking)")
        if vr.warnings:
            for i in vr.warnings:
                st.warning(f"[{i.code}] {i.message}")
        else:
            st.write("None.")

        if case["verified_findings"]:
            st.subheader("AI claim verification")
            for f in case["verified_findings"]:
                if f.status == "NEEDS HUMAN VERIFICATION":
                    st.warning(f"`{f.issue_id}`: {f.reason}")

        st.divider()
        st.subheader("Reviewer decision")
        st.caption("Student testing: you may role-play both Associate and Manager, but this must be "
                    "labeled a simulation of roles — no real company sign-off is implied.")

        reviewer_name = st.text_input("Reviewer name")
        reviewer_role = st.selectbox("Reviewer role", ["associate", "manager"])
        decision_type = st.selectbox("Decision", ["approve", "reject", "return_for_correction"])
        reason = st.text_area("Reason / notes")

        if st.button("Submit review decision", type="primary"):
            if not reviewer_name or not reason:
                st.error("Reviewer name and reason are required.")
            else:
                decision = ReviewDecision(reviewer_name, reviewer_role, decision_type, reason)
                try:
                    run.record_decision(decision)
                    audit.append_event(case["run_dir"], "REVIEW_DECISION", {
                        "reviewer_name": reviewer_name, "reviewer_role": reviewer_role,
                        "decision": decision_type, "reason": reason, "resulting_state": run.state.value,
                    })
                    st.success(f"Decision recorded. Run state is now {run.state.value}.")
                except IllegalTransitionError as e:
                    audit.append_event(case["run_dir"], "REVIEW_DECISION_REJECTED_BY_SYSTEM", {"error": str(e)})
                    st.error(f"Blocked by system rule: {e}")
                st.session_state.case = case
                st.rerun()

# ---------------------------------------------------------------------------
# PAGE 6 — BRIEFING & AUDIT TRAIL
# ---------------------------------------------------------------------------
elif page == "6. Briefing & Audit Trail":
    st.header("Briefing & Audit Trail")
    st.caption(
        "📌 **What this page is for:** the 'Briefing' is the final write-up document — everything "
        "from the other pages combined into one downloadable report. The 'Audit Trail' is a log of "
        "every action taken during this case (uploads, validation, the AI call, review decisions) "
        "— your evidence trail for the assignment."
    )
    if case is None or case["year_metrics"] is None:
        st.info("Run a case with no blocking errors on the Case Setup page first.")
    else:
        rating = reports.overall_rating(case["period_summary"])
        st.markdown(f"## {rating['emoji']} Overall trend: {rating['label']}")
        st.markdown(rating_gauge_html(rating["points"]), unsafe_allow_html=True)
        st.caption(f"This is {rating['why']}")
        st.divider()

        briefing_md = reports.render_briefing(
            run=case["run"],
            company_name=case["company_name"],
            management_question=case["question"],
            metrics=case["year_metrics"],
            period_summary=case["period_summary"],
            verified_findings=case["verified_findings"] or [],
            scenario_result=case["scenario_result"],
            ai_model=case["ai_model"],
            ai_status=case["ai_status"],
            ai_raw_json=case.get("ai_raw_json"),
        )
        st.markdown(briefing_md)

        pdf_bytes = pdf_report.build_pdf_report(
            run=case["run"],
            company_name=case["company_name"],
            management_question=case["question"],
            metrics=case["year_metrics"],
            period_summary=case["period_summary"],
            verified_findings=case["verified_findings"] or [],
            ai_raw_json=case.get("ai_raw_json"),
            ai_model=case["ai_model"],
            ai_status=case["ai_status"],
            plain_english_overview=reports.plain_english_overview(case["year_metrics"], case["period_summary"]),
        )
        pdf_filename = pdf_report.build_filename(case["company_name"], case["run_id"])

        dl_col1, dl_col2 = st.columns(2)
        dl_col1.download_button("📄 Download as PDF", pdf_bytes,
                                 file_name=pdf_filename, mime="application/pdf", type="primary")
        dl_col2.download_button("Download as Markdown", briefing_md, file_name=f"briefing_{case['run_id']}.md")

        st.divider()
        st.subheader("Audit log")
        events = audit.load_events(case["run_dir"])
        st.dataframe(pd.DataFrame(events)) if events else st.write("No events yet.")
        if st.button("Export test log"):
            dest = Path(case["run_dir"]) / "test_log_export.md"
            content = audit.export_test_log(case["run_dir"], str(dest))
            st.success(f"Exported to {dest}")
            st.download_button("Download test log", content, file_name="test_log_export.md")

st.sidebar.divider()
if case is not None:
    st.sidebar.caption(f"Run folder: `outputs/{case['run_id']}`")
