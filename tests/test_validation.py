from consultai import validation


def test_normal_finance_has_no_blocking_errors(normal_finance_df):
    result = validation.validate_finance_df(normal_finance_df, "normal_finance.csv")
    assert not result.is_blocked, [i.message for i in result.blocking]


def test_normal_operations_has_no_blocking_errors(normal_finance_df, normal_operations_df):
    result = validation.validate_operations_df(normal_operations_df, normal_finance_df, "normal_operations.csv")
    assert not result.is_blocked, [i.message for i in result.blocking]


def test_profit_mismatch_is_blocking(normal_finance_df):
    df = normal_finance_df.copy()
    df.loc[df["year"] == 2025, "reported_operating_profit_m"] = 40.0
    result = validation.validate_finance_df(df, "adversarial_profit_mismatch.csv")
    assert result.is_blocked
    codes = [i.code for i in result.blocking]
    assert "FINANCE_PROFIT_MISMATCH" in codes


def test_profit_mismatch_within_tolerance_is_not_blocking(normal_finance_df):
    df = normal_finance_df.copy()
    # 14.0 -> 14.09 is within the 0.1m tolerance
    df.loc[df["year"] == 2025, "reported_operating_profit_m"] = 14.09
    result = validation.validate_finance_df(df, "finance.csv")
    assert not result.is_blocked


def test_missing_year_in_sequence_is_blocking(normal_finance_df):
    df = normal_finance_df[normal_finance_df["year"] != 2024].reset_index(drop=True)
    result = validation.validate_finance_df(df, "adversarial_missing_year.csv")
    assert result.is_blocked
    assert any(i.code == "FINANCE_MISSING_YEAR_IN_SEQUENCE" for i in result.blocking)


def test_too_few_years_is_blocking(normal_finance_df):
    df = normal_finance_df.iloc[:2].reset_index(drop=True)
    result = validation.validate_finance_df(df, "finance.csv")
    assert result.is_blocked
    assert any(i.code == "FINANCE_TOO_FEW_YEARS" for i in result.blocking)


def test_negative_revenue_is_blocking(normal_finance_df):
    df = normal_finance_df.copy()
    df.loc[0, "revenue_m"] = -5.0
    result = validation.validate_finance_df(df, "finance.csv")
    assert result.is_blocked
    assert any(i.code == "FINANCE_NEGATIVE_VALUE" for i in result.blocking)


def test_legitimate_negative_profit_is_not_blocked(normal_finance_df):
    df = normal_finance_df.copy()
    df.loc[df["year"] == 2025, ["cogs_m", "operating_expenses_m", "reported_operating_profit_m"]] = [82.0, 60.0, -12.0]
    result = validation.validate_finance_df(df, "finance.csv")
    assert not result.is_blocked


def test_labor_cost_exceeding_opex_is_blocking(normal_finance_df, normal_operations_df):
    ops = normal_operations_df.copy()
    ops.loc[ops["year"] == 2025, "labor_cost_m"] = 40.0  # opex for 2025 is 34
    result = validation.validate_operations_df(ops, normal_finance_df, "adversarial_operations_labor_mismatch.csv")
    assert result.is_blocked
    assert any(i.code == "CROSS_DOC_LABOR_EXCEEDS_OPEX" for i in result.blocking)


def test_sensitive_data_in_memo_is_blocking():
    text = "Patient contact: jane.doe@example.com for questions."
    result = validation.scan_sensitive_data(text, "memo.txt")
    assert result.is_blocked
    assert any(i.code == "SENSITIVE_DATA_DETECTED" for i in result.blocking)


def test_clean_memo_has_no_sensitive_data_flag():
    text = "Goal: restore operating margin to at least 15% without reducing patient access."
    result = validation.scan_sensitive_data(text, "memo.txt")
    assert not result.is_blocked


def test_missing_memo_is_blocking():
    result = validation.validate_memo_present(None, "memo.txt")
    assert result.is_blocked
    result2 = validation.validate_memo_present("   ", "memo.txt")
    assert result2.is_blocked
