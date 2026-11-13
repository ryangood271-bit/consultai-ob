"""Runs the actual sample_data files through the real validation/metrics/issue_detection
pipeline (no Streamlit, no AI call) and prints real results. Not a substitute for the UI
walkthrough, but proves the core logic behaves correctly on the real fixtures.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from consultai import issue_detection, metrics as metrics_mod, validation

SAMPLE = Path(__file__).parent.parent / "sample_data"


def run_case(label, finance_csv, ops_csv, memo_txt):
    print(f"\n=== {label} ===")
    finance_df = pd.read_csv(SAMPLE / finance_csv)
    ops_df = pd.read_csv(SAMPLE / ops_csv)
    memo_text = (SAMPLE / memo_txt).read_text()

    vr = validation.validate_finance_df(finance_df, finance_csv)
    vr.extend(validation.validate_operations_df(ops_df, finance_df, ops_csv))
    vr.extend(validation.validate_memo_present(memo_text, memo_txt))
    vr.extend(validation.scan_sensitive_data(memo_text, memo_txt))

    print(f"Blocking errors: {len(vr.blocking)}")
    for i in vr.blocking:
        print(f"  BLOCKING [{i.code}] {i.message}")
    print(f"Warnings: {len(vr.warnings)}")

    if vr.is_blocked:
        print("RESULT: BLOCKED_INPUT — no metrics/issue detection run (matches app behavior).")
        return

    ym = metrics_mod.compute_year_metrics(finance_df, ops_df)
    summary = metrics_mod.summarize_period(ym)
    print(f"Operating margin: {ym[0].operating_margin_pct:.2f}% -> {ym[-1].operating_margin_pct:.2f}%")
    print(f"Revenue change: {summary['revenue_change_pct']:.2f}%  |  "
          f"Operating profit change: {summary['operating_profit_change_pct']:.2f}%")

    issues = issue_detection.detect_issues(ym, finance_csv, ops_csv, memo_text)
    top3 = issue_detection.top_n(issues, 3)
    print(f"Detected {len(issues)} candidate issue(s), top {len(top3)}:")
    for i in top3:
        print(f"  - [{i.weighted_score:.2f}] {i.title}")
    print("RESULT: CALCULATIONS_READY (would proceed to AI call in the app).")


if __name__ == "__main__":
    run_case("Test 1 — Normal case", "normal_finance.csv", "normal_operations.csv", "normal_ceo_memo.txt")
    run_case(
        "Test 2 — Adversarial case (profit mismatch + injection memo)",
        "adversarial_profit_mismatch.csv", "normal_operations.csv", "adversarial_ceo_memo.txt",
    )
