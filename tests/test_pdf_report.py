from consultai import metrics as metrics_mod, pdf_report, reports
from consultai.review import Run


def test_build_filename_slugifies_company_name():
    name = pdf_report.build_filename("BlueRiver Healthcare Services, Inc.", "abc123456")
    assert name.startswith("BlueRiver_Healthcare_Services_Inc_Consulting_Briefing_")
    assert name.endswith(".pdf")
    assert " " not in name


def test_pdf_builds_without_ai(normal_finance_df, normal_operations_df):
    ym = metrics_mod.compute_year_metrics(normal_finance_df, normal_operations_df)
    summary = metrics_mod.summarize_period(ym)
    run = Run(run_id="pdftest_noai")
    run.set_validation_outcome(False)

    overview = reports.plain_english_overview(ym, summary)
    pdf_bytes = pdf_report.build_pdf_report(
        run, "Test Co", "What's going on?", ym, summary, [], None, None, "NO AI GENERATED", overview
    )
    assert pdf_bytes[:5] == b"%PDF-"
    assert len(pdf_bytes) > 1000


def test_pdf_builds_with_fake_ai_output(normal_finance_df, normal_operations_df):
    ym = metrics_mod.compute_year_metrics(normal_finance_df, normal_operations_df)
    summary = metrics_mod.summarize_period(ym)
    run = Run(run_id="pdftest_withai")
    run.set_validation_outcome(False)
    run.mark_ai_draft_ready()

    fake_raw = {
        "why_important": "Margin is declining while revenue grows.",
        "hypotheses": ["Unverified: rising COGS is the driver."],
        "proposed_investigations": ["Check supplier contracts."],
        "strategic_options": ["Renegotiate key supplier terms."],
        "limitations": ["Synthetic data."],
        "source_conflicts": [],
    }
    overview = reports.plain_english_overview(ym, summary)
    pdf_bytes = pdf_report.build_pdf_report(
        run, "Test Co", "What's going on?", ym, summary, [], fake_raw, "claude-sonnet-5-5", "OK", overview
    )
    assert pdf_bytes[:5] == b"%PDF-"
    assert len(pdf_bytes) > 2000
