"""Scenario simulator: pure mechanical what-if math. No AI, no forecast claims."""

from __future__ import annotations

from dataclasses import dataclass

from .metrics import YearMetrics


@dataclass
class ScenarioResult:
    baseline_year: int
    cogs_pct_change: float
    revenue_pct_change: float
    baseline_revenue_m: float
    baseline_cogs_m: float
    baseline_opex_m: float
    baseline_operating_profit_m: float
    baseline_operating_margin_pct: float
    new_revenue_m: float
    new_cogs_m: float
    new_operating_profit_m: float
    new_operating_margin_pct: float
    profit_delta_m: float
    assumptions: str = (
        "Illustrative mechanical scenario only — operating expenses, staffing, and all other "
        "variables are held constant. This is not a forecast and does not assess feasibility."
    )


def run_scenario(baseline: YearMetrics, cogs_pct_change: float, revenue_pct_change: float = 0.0) -> ScenarioResult:
    """Apply a % change to COGS (0-20 range expected) and optionally revenue (0-15 range), holding opex constant."""
    new_revenue = baseline.revenue_m * (1 + revenue_pct_change / 100)
    new_cogs = baseline.cogs_m * (1 - cogs_pct_change / 100)
    new_profit = new_revenue - new_cogs - baseline.operating_expenses_m
    new_margin = (new_profit / new_revenue * 100) if new_revenue else 0.0

    return ScenarioResult(
        baseline_year=baseline.year,
        cogs_pct_change=cogs_pct_change,
        revenue_pct_change=revenue_pct_change,
        baseline_revenue_m=baseline.revenue_m,
        baseline_cogs_m=baseline.cogs_m,
        baseline_opex_m=baseline.operating_expenses_m,
        baseline_operating_profit_m=baseline.operating_profit_m,
        baseline_operating_margin_pct=baseline.operating_margin_pct,
        new_revenue_m=new_revenue,
        new_cogs_m=new_cogs,
        new_operating_profit_m=new_profit,
        new_operating_margin_pct=new_margin,
        profit_delta_m=new_profit - baseline.operating_profit_m,
    )
