import pytest

from consultai import metrics as metrics_mod


def test_year_metrics_match_worked_example(normal_finance_df, normal_operations_df):
    ym = metrics_mod.compute_year_metrics(normal_finance_df, normal_operations_df)
    first, last = ym[0], ym[-1]

    assert first.year == 2023 and last.year == 2025
    assert first.operating_profit_m == pytest.approx(20.0)
    assert last.operating_profit_m == pytest.approx(14.0)
    assert first.operating_margin_pct == pytest.approx(20.0)
    assert last.operating_margin_pct == pytest.approx(130 and (14 / 130 * 100))
    assert last.operating_margin_pct == pytest.approx(10.76923, rel=1e-4)
    assert first.cogs_share_pct == pytest.approx(55.0)
    assert last.cogs_share_pct == pytest.approx(63.07692, rel=1e-4)
    assert first.staff_hours_per_visit == pytest.approx(2.0)
    assert last.staff_hours_per_visit == pytest.approx(2.4)


def test_summarize_period_matches_brief_worked_numbers(normal_finance_df, normal_operations_df):
    ym = metrics_mod.compute_year_metrics(normal_finance_df, normal_operations_df)
    summary = metrics_mod.summarize_period(ym)

    assert summary["revenue_change_pct"] == pytest.approx(30.0)
    assert summary["operating_profit_change_pct"] == pytest.approx(-30.0)
    assert summary["operating_margin_change_pp"] == pytest.approx(-9.2308, rel=1e-3)
    assert summary["cogs_share_change_pp"] == pytest.approx(8.0769, rel=1e-3)
    assert summary["staff_hours_per_visit_change_pct"] == pytest.approx(20.0)
    assert summary["average_wait_minutes_change_pct"] == pytest.approx(40.909, rel=1e-3)


def test_pct_change_handles_zero_baseline():
    assert metrics_mod.pct_change(0, 10) is None
