from consultai import issue_detection, metrics as metrics_mod


def test_normal_case_detects_expected_issues_in_order(normal_finance_df, normal_operations_df):
    ym = metrics_mod.compute_year_metrics(normal_finance_df, normal_operations_df)
    issues = issue_detection.detect_issues(
        ym, "normal_finance.csv", "normal_operations.csv",
        goal_text="restore operating margin to 15% without reducing patient access or increasing wait times",
    )
    ids = [i.issue_id for i in issues]

    # All five threshold-crossing issues should fire for the brief's worked example.
    assert "OPERATING_MARGIN_DECLINE" in ids
    assert "COGS_SHARE_RISING" in ids
    assert "REVENUE_PROFIT_DIVERGENCE" in ids
    assert "STAFF_HOURS_OUTPACING_VISITS" in ids
    assert "WAIT_TIME_RISING" in ids

    # Ranked descending by weighted score.
    scores = [i.weighted_score for i in issues]
    assert scores == sorted(scores, reverse=True)

    top3 = issue_detection.top_n(issues, 3)
    assert len(top3) == 3


def test_no_issues_for_a_flat_healthy_business(normal_finance_df, normal_operations_df):
    flat_finance = normal_finance_df.copy()
    flat_finance["revenue_m"] = [100.0, 100.0, 100.0]
    flat_finance["cogs_m"] = [55.0, 55.0, 55.0]
    flat_finance["operating_expenses_m"] = [25.0, 25.0, 25.0]
    flat_finance["reported_operating_profit_m"] = [20.0, 20.0, 20.0]

    flat_ops = normal_operations_df.copy()
    flat_ops["patient_visits"] = [100000, 100000, 100000]
    flat_ops["staff_hours"] = [200000, 200000, 200000]
    flat_ops["labor_cost_m"] = [14.0, 14.0, 14.0]
    flat_ops["average_wait_minutes"] = [22.0, 22.0, 22.0]

    ym = metrics_mod.compute_year_metrics(flat_finance, flat_ops)
    issues = issue_detection.detect_issues(ym, "f.csv", "o.csv")
    assert issues == []


def test_every_issue_has_evidence_refs(normal_finance_df, normal_operations_df):
    ym = metrics_mod.compute_year_metrics(normal_finance_df, normal_operations_df)
    issues = issue_detection.detect_issues(ym, "normal_finance.csv", "normal_operations.csv")
    for issue in issues:
        assert len(issue.evidence) >= 1
        assert issue.label == "OBSERVED"
