"""Deterministic financial + operational metrics. Pure functions, no AI, no I/O.

All money values in USD millions unless explicitly converted to dollars (labor_cost_per_visit).
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class YearMetrics:
    year: int
    revenue_m: float
    cogs_m: float
    operating_expenses_m: float
    operating_profit_m: float
    gross_profit_m: float
    gross_margin_pct: float
    operating_margin_pct: float
    cogs_share_pct: float
    opex_share_pct: float
    patient_visits: int | None = None
    staff_hours: float | None = None
    labor_cost_m: float | None = None
    average_wait_minutes: float | None = None
    visits_per_staff_hour: float | None = None
    staff_hours_per_visit: float | None = None
    labor_cost_per_visit_dollars: float | None = None


def compute_year_metrics(finance_df: pd.DataFrame, ops_df: pd.DataFrame | None = None) -> list[YearMetrics]:
    """Compute per-year metrics, in year order, deterministically from validated data."""
    finance_df = finance_df.sort_values("year").reset_index(drop=True)
    ops_by_year = {}
    if ops_df is not None:
        ops_by_year = {int(r["year"]): r for _, r in ops_df.iterrows()}

    results: list[YearMetrics] = []
    for _, row in finance_df.iterrows():
        year = int(row["year"])
        revenue = float(row["revenue_m"])
        cogs = float(row["cogs_m"])
        opex = float(row["operating_expenses_m"])
        operating_profit = revenue - cogs - opex
        gross_profit = revenue - cogs
        gross_margin = (gross_profit / revenue * 100) if revenue else 0.0
        operating_margin = (operating_profit / revenue * 100) if revenue else 0.0
        cogs_share = (cogs / revenue * 100) if revenue else 0.0
        opex_share = (opex / revenue * 100) if revenue else 0.0

        ym = YearMetrics(
            year=year,
            revenue_m=revenue,
            cogs_m=cogs,
            operating_expenses_m=opex,
            operating_profit_m=operating_profit,
            gross_profit_m=gross_profit,
            gross_margin_pct=gross_margin,
            operating_margin_pct=operating_margin,
            cogs_share_pct=cogs_share,
            opex_share_pct=opex_share,
        )

        if year in ops_by_year:
            orow = ops_by_year[year]
            visits = float(orow["patient_visits"])
            hours = float(orow["staff_hours"])
            labor = float(orow["labor_cost_m"])
            wait = float(orow["average_wait_minutes"])
            ym.patient_visits = visits
            ym.staff_hours = hours
            ym.labor_cost_m = labor
            ym.average_wait_minutes = wait
            ym.visits_per_staff_hour = (visits / hours) if hours else None
            ym.staff_hours_per_visit = (hours / visits) if visits else None
            ym.labor_cost_per_visit_dollars = (labor * 1_000_000 / visits) if visits else None

        results.append(ym)

    return results


def pct_change(old: float, new: float) -> float | None:
    if old == 0:
        return None
    return (new - old) / old * 100


def pp_change(old_pct: float, new_pct: float) -> float:
    """Percentage-point change (not a percent change of a percent)."""
    return new_pct - old_pct


def summarize_period(metrics: list[YearMetrics]) -> dict:
    """Compare first vs last year in the series — the headline figures used in the briefing."""
    first, last = metrics[0], metrics[-1]
    out = {
        "start_year": first.year,
        "end_year": last.year,
        "revenue_change_pct": pct_change(first.revenue_m, last.revenue_m),
        "operating_profit_change_pct": pct_change(first.operating_profit_m, last.operating_profit_m),
        "operating_margin_start_pct": first.operating_margin_pct,
        "operating_margin_end_pct": last.operating_margin_pct,
        "operating_margin_change_pp": pp_change(first.operating_margin_pct, last.operating_margin_pct),
        "cogs_share_start_pct": first.cogs_share_pct,
        "cogs_share_end_pct": last.cogs_share_pct,
        "cogs_share_change_pp": pp_change(first.cogs_share_pct, last.cogs_share_pct),
    }
    if first.staff_hours_per_visit is not None and last.staff_hours_per_visit is not None:
        out["staff_hours_per_visit_change_pct"] = pct_change(first.staff_hours_per_visit, last.staff_hours_per_visit)
    if first.average_wait_minutes is not None and last.average_wait_minutes is not None:
        out["average_wait_minutes_change_pct"] = pct_change(first.average_wait_minutes, last.average_wait_minutes)
    return out
