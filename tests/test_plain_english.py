from consultai import metrics as metrics_mod, reports


def test_plain_english_flags_revenue_up_profit_down(normal_finance_df, normal_operations_df):
    ym = metrics_mod.compute_year_metrics(normal_finance_df, normal_operations_df)
    summary = metrics_mod.summarize_period(ym)
    text = reports.plain_english_overview(ym, summary)

    assert "grew" in text
    assert "shrank" in text
    assert "worth flagging" in text


def test_overall_rating_flags_weak_for_declining_case(normal_finance_df, normal_operations_df):
    ym = metrics_mod.compute_year_metrics(normal_finance_df, normal_operations_df)
    summary = metrics_mod.summarize_period(ym)
    rating = reports.overall_rating(summary)
    # margin -9.2pp (-2), revenue +30% (+1), profit -30% (-1) => points = -2 => "Worth watching"
    assert rating["points"] == -2
    assert rating["label"] == "Worth watching"
    assert "margin fell" in rating["why"]


def test_overall_rating_flags_strong_for_improving_case():
    import pandas as pd

    df = pd.DataFrame(
        {
            "year": [2023, 2024, 2025],
            "revenue_m": [100.0, 115.0, 135.0],
            "cogs_m": [55.0, 58.0, 60.0],
            "operating_expenses_m": [25.0, 25.0, 25.0],
            "reported_operating_profit_m": [20.0, 32.0, 50.0],
        }
    )
    ym = metrics_mod.compute_year_metrics(df, None)
    summary = metrics_mod.summarize_period(ym)
    rating = reports.overall_rating(summary)
    assert rating["points"] >= 3
    assert rating["label"] == "Doing well"
    assert "margin improved" in rating["why"]


def test_plain_english_handles_improving_margin():
    import pandas as pd

    df = pd.DataFrame(
        {
            "year": [2023, 2024, 2025],
            "revenue_m": [100.0, 110.0, 130.0],
            "cogs_m": [55.0, 58.0, 60.0],
            "operating_expenses_m": [25.0, 25.0, 25.0],
            "reported_operating_profit_m": [20.0, 27.0, 45.0],
        }
    )
    ym = metrics_mod.compute_year_metrics(df, None)
    summary = metrics_mod.summarize_period(ym)
    text = reports.plain_english_overview(ym, summary)

    assert "good sign" in text
    assert "worth flagging" not in text
