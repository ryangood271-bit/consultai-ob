"""Deterministic pre-AI validation. No model calls happen here — this is pure Python/pandas.

Blocking issues must stop the pipeline before any AI call. Warnings surface to the reviewer
but do not block calculations.
"""

from __future__ import annotations

import re

import pandas as pd

from .schemas import (
    FINANCE_COLUMNS,
    MIN_CONSECUTIVE_YEARS,
    OPERATIONS_COLUMNS,
    PROFIT_RECONCILIATION_TOLERANCE_M,
    Severity,
    ValidationIssue,
    ValidationResult,
)

SENSITIVE_PATTERNS = {
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "PHONE": re.compile(r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b"),
}


def validate_finance_df(df: pd.DataFrame, filename: str) -> ValidationResult:
    result = ValidationResult()

    missing_cols = [c for c in FINANCE_COLUMNS if c not in df.columns]
    if missing_cols:
        result.issues.append(
            ValidationIssue(
                Severity.BLOCKING,
                "FINANCE_MISSING_COLUMNS",
                f"Missing required columns: {missing_cols}",
                filename,
            )
        )
        return result  # can't check further without the columns

    for col in FINANCE_COLUMNS:
        non_numeric = df[~df[col].apply(lambda v: isinstance(v, (int, float)) and not pd.isna(v))]
        if not non_numeric.empty:
            for idx in non_numeric.index:
                result.issues.append(
                    ValidationIssue(
                        Severity.BLOCKING,
                        "FINANCE_NON_NUMERIC",
                        f"Non-numeric or missing value in column '{col}'",
                        filename,
                        row=str(idx),
                        column=col,
                        observed=str(df.loc[idx, col]),
                    )
                )

    if result.is_blocked:
        return result

    years = df["year"].astype(int).tolist()
    if len(years) != len(set(years)):
        dupes = sorted({y for y in years if years.count(y) > 1})
        result.issues.append(
            ValidationIssue(
                Severity.BLOCKING,
                "FINANCE_DUPLICATE_YEAR",
                f"Duplicate year(s) found: {dupes}",
                filename,
            )
        )

    sorted_years = sorted(set(years))
    if len(sorted_years) < MIN_CONSECUTIVE_YEARS:
        result.issues.append(
            ValidationIssue(
                Severity.BLOCKING,
                "FINANCE_TOO_FEW_YEARS",
                f"Need at least {MIN_CONSECUTIVE_YEARS} consecutive years, found {len(sorted_years)}.",
                filename,
            )
        )

    # Checked independently of the row-count check above: a file can simultaneously have
    # too few rows AND a gap in the sequence (e.g. only 2023 and 2025 present).
    if len(sorted_years) >= 2:
        expected_seq = list(range(sorted_years[0], sorted_years[-1] + 1))
        if sorted_years != expected_seq:
            missing = sorted(set(expected_seq) - set(sorted_years))
            result.issues.append(
                ValidationIssue(
                    Severity.BLOCKING,
                    "FINANCE_MISSING_YEAR_IN_SEQUENCE",
                    f"Years are not consecutive. Expected {expected_seq}, missing {missing}.",
                    filename,
                )
            )

    for idx, row in df.iterrows():
        if row["revenue_m"] < 0 or row["cogs_m"] < 0 or row["operating_expenses_m"] < 0:
            result.issues.append(
                ValidationIssue(
                    Severity.BLOCKING,
                    "FINANCE_NEGATIVE_VALUE",
                    "Revenue, COGS, and operating expenses must be non-negative (profit may legitimately be negative).",
                    filename,
                    row=str(idx),
                )
            )

        calculated = row["revenue_m"] - row["cogs_m"] - row["operating_expenses_m"]
        reported = row["reported_operating_profit_m"]
        diff = abs(calculated - reported)
        if diff > PROFIT_RECONCILIATION_TOLERANCE_M:
            result.issues.append(
                ValidationIssue(
                    Severity.BLOCKING,
                    "FINANCE_PROFIT_MISMATCH",
                    f"Reported operating profit does not reconcile with revenue - COGS - opex "
                    f"(difference {diff:.4f}m exceeds tolerance {PROFIT_RECONCILIATION_TOLERANCE_M}m).",
                    filename,
                    row=str(row["year"]),
                    column="reported_operating_profit_m",
                    expected=f"{calculated:.4f}",
                    observed=f"{reported:.4f}",
                )
            )

    return result


def validate_operations_df(ops_df: pd.DataFrame, finance_df: pd.DataFrame, filename: str) -> ValidationResult:
    result = ValidationResult()

    missing_cols = [c for c in OPERATIONS_COLUMNS if c not in ops_df.columns]
    if missing_cols:
        result.issues.append(
            ValidationIssue(
                Severity.BLOCKING,
                "OPS_MISSING_COLUMNS",
                f"Missing required columns: {missing_cols}",
                filename,
            )
        )
        return result

    for col in OPERATIONS_COLUMNS:
        non_numeric = ops_df[~ops_df[col].apply(lambda v: isinstance(v, (int, float)) and not pd.isna(v))]
        if not non_numeric.empty:
            for idx in non_numeric.index:
                result.issues.append(
                    ValidationIssue(
                        Severity.BLOCKING,
                        "OPS_NON_NUMERIC",
                        f"Non-numeric or missing value in column '{col}'",
                        filename,
                        row=str(idx),
                        column=col,
                    )
                )
    if result.is_blocked:
        return result

    for idx, row in ops_df.iterrows():
        if row["patient_visits"] <= 0 or row["staff_hours"] <= 0:
            result.issues.append(
                ValidationIssue(
                    Severity.BLOCKING,
                    "OPS_NON_POSITIVE",
                    "patient_visits and staff_hours must be positive.",
                    filename,
                    row=str(row["year"]),
                )
            )
        if row["labor_cost_m"] < 0 or row["average_wait_minutes"] < 0:
            result.issues.append(
                ValidationIssue(
                    Severity.BLOCKING,
                    "OPS_NEGATIVE_VALUE",
                    "labor_cost_m and average_wait_minutes must be non-negative.",
                    filename,
                    row=str(row["year"]),
                )
            )

    finance_by_year = finance_df.set_index("year")["operating_expenses_m"].to_dict()
    for idx, row in ops_df.iterrows():
        year = row["year"]
        if year in finance_by_year:
            opex = finance_by_year[year]
            labor = row["labor_cost_m"]
            if labor > opex:
                result.issues.append(
                    ValidationIssue(
                        Severity.BLOCKING,
                        "CROSS_DOC_LABOR_EXCEEDS_OPEX",
                        "labor_cost_m exceeds that year's operating_expenses_m, but labor is defined as a "
                        "subset of operating expenses — this is an internal inconsistency between files.",
                        filename,
                        row=str(year),
                        column="labor_cost_m",
                        expected=f"<= {opex}",
                        observed=str(labor),
                    )
                )

    return result


def scan_sensitive_data(text: str, filename: str) -> ValidationResult:
    """Warn (don't silently send) if memo text looks like it contains real identifying data."""
    result = ValidationResult()
    for label, pattern in SENSITIVE_PATTERNS.items():
        if pattern.search(text):
            result.issues.append(
                ValidationIssue(
                    Severity.BLOCKING,
                    "SENSITIVE_DATA_DETECTED",
                    f"Memo text matches a pattern that looks like {label}-shaped data. "
                    "Remove it before this content can be sent to an external AI API.",
                    filename,
                )
            )
    return result


def validate_memo_present(text: str | None, filename: str) -> ValidationResult:
    result = ValidationResult()
    if text is None or not text.strip():
        result.issues.append(
            ValidationIssue(
                Severity.BLOCKING,
                "MEMO_MISSING_OR_UNREADABLE",
                "A readable memo is required before AI interpretation can run. "
                "Numerical analysis can still proceed without it.",
                filename,
            )
        )
    return result
