"""Threshold-based candidate issue detection + transparent weighted ranking.

Every issue is backed by a specific evidence reference (file/year/column) computed in
metrics.py. This module never invents numbers — it only compares numbers already computed
deterministically and labels the comparison as an OBSERVED fact, never a proven cause.

Scoring weights (documented, not hidden): impact 50%, evidence strength 30%,
relevance to the stated management goal 20%. Each sub-score is 1-5; the weighted score is
out of 5.0.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .metrics import YearMetrics, pct_change, pp_change

MARGIN_DETERIORATION_THRESHOLD_PP = 3.0
COST_RATIO_RISE_THRESHOLD_PP = 3.0
STAFFING_VS_VOLUME_GAP_THRESHOLD_PP = 5.0  # staff-hours growth% minus visits growth%
WAIT_TIME_INCREASE_THRESHOLD_PCT = 10.0


@dataclass
class EvidenceRef:
    file: str
    year: int | str
    column: str
    value: str


@dataclass
class Issue:
    issue_id: str
    title: str
    description: str
    label: str  # "OBSERVED" or "INFERENCE"
    evidence: list[EvidenceRef]
    impact_score: int
    evidence_score: int
    relevance_score: int

    @property
    def weighted_score(self) -> float:
        return self.impact_score * 0.5 + self.evidence_score * 0.3 + self.relevance_score * 0.2


def detect_issues(
    metrics: list[YearMetrics],
    finance_filename: str,
    ops_filename: str | None,
    goal_text: str | None = None,
) -> list[Issue]:
    """Return ranked candidate issues (highest weighted_score first). Caller takes top N."""
    issues: list[Issue] = []
    first, last = metrics[0], metrics[-1]
    goal_mentions_access = bool(goal_text) and any(
        kw in goal_text.lower() for kw in ["access", "wait", "patient"]
    )
    goal_mentions_margin = bool(goal_text) and "margin" in goal_text.lower()

    margin_change_pp = pp_change(first.operating_margin_pct, last.operating_margin_pct)
    if margin_change_pp <= -MARGIN_DETERIORATION_THRESHOLD_PP:
        issues.append(
            Issue(
                issue_id="OPERATING_MARGIN_DECLINE",
                title="Operating margin has deteriorated",
                description=(
                    f"Operating margin fell from {first.operating_margin_pct:.2f}% ({first.year}) to "
                    f"{last.operating_margin_pct:.2f}% ({last.year}), a decline of {abs(margin_change_pp):.2f} "
                    "percentage points."
                ),
                label="OBSERVED",
                evidence=[
                    EvidenceRef(finance_filename, first.year, "operating_margin_pct", f"{first.operating_margin_pct:.4f}"),
                    EvidenceRef(finance_filename, last.year, "operating_margin_pct", f"{last.operating_margin_pct:.4f}"),
                ],
                impact_score=5,
                evidence_score=5,
                relevance_score=5 if goal_mentions_margin else 4,
            )
        )

    cogs_change_pp = pp_change(first.cogs_share_pct, last.cogs_share_pct)
    if cogs_change_pp >= COST_RATIO_RISE_THRESHOLD_PP:
        issues.append(
            Issue(
                issue_id="COGS_SHARE_RISING",
                title="Cost of goods sold is consuming a growing share of revenue",
                description=(
                    f"COGS as a share of revenue rose from {first.cogs_share_pct:.2f}% ({first.year}) to "
                    f"{last.cogs_share_pct:.2f}% ({last.year}), up {cogs_change_pp:.2f} percentage points."
                ),
                label="OBSERVED",
                evidence=[
                    EvidenceRef(finance_filename, first.year, "cogs_share_pct", f"{first.cogs_share_pct:.4f}"),
                    EvidenceRef(finance_filename, last.year, "cogs_share_pct", f"{last.cogs_share_pct:.4f}"),
                ],
                impact_score=4,
                evidence_score=5,
                relevance_score=4 if goal_mentions_margin else 3,
            )
        )

    revenue_change = pct_change(first.revenue_m, last.revenue_m)
    profit_change = pct_change(first.operating_profit_m, last.operating_profit_m)
    if revenue_change is not None and profit_change is not None and revenue_change > 0 and profit_change < 0:
        issues.append(
            Issue(
                issue_id="REVENUE_PROFIT_DIVERGENCE",
                title="Revenue and operating profit are moving in opposite directions",
                description=(
                    f"Revenue grew {revenue_change:.2f}% from {first.year} to {last.year} while operating "
                    f"profit fell {abs(profit_change):.2f}% over the same period."
                ),
                label="OBSERVED",
                evidence=[
                    EvidenceRef(finance_filename, f"{first.year}-{last.year}", "revenue_m", f"{revenue_change:.2f}%"),
                    EvidenceRef(finance_filename, f"{first.year}-{last.year}", "operating_profit_m", f"{profit_change:.2f}%"),
                ],
                impact_score=5,
                evidence_score=5,
                relevance_score=5 if goal_mentions_margin else 4,
            )
        )

    if first.staff_hours is not None and last.staff_hours is not None and first.patient_visits and last.patient_visits:
        hours_growth = pct_change(first.staff_hours, last.staff_hours) or 0.0
        visits_growth = pct_change(first.patient_visits, last.patient_visits) or 0.0
        gap = hours_growth - visits_growth
        if gap >= STAFFING_VS_VOLUME_GAP_THRESHOLD_PP:
            issues.append(
                Issue(
                    issue_id="STAFF_HOURS_OUTPACING_VISITS",
                    title="Staff hours are growing faster than patient visits",
                    description=(
                        f"Staff hours grew {hours_growth:.2f}% while patient visits grew {visits_growth:.2f}% "
                        f"({first.year}-{last.year}), a gap of {gap:.2f} percentage points — a pattern "
                        "consistent with declining labor productivity, not a confirmed cause."
                    ),
                    label="OBSERVED",
                    evidence=[
                        EvidenceRef(ops_filename or "operations", f"{first.year}-{last.year}", "staff_hours", f"{hours_growth:.2f}%"),
                        EvidenceRef(ops_filename or "operations", f"{first.year}-{last.year}", "patient_visits", f"{visits_growth:.2f}%"),
                    ],
                    impact_score=3,
                    evidence_score=4,
                    relevance_score=4 if goal_mentions_access else 3,
                )
            )

    if first.average_wait_minutes is not None and last.average_wait_minutes is not None:
        wait_change = pct_change(first.average_wait_minutes, last.average_wait_minutes)
        if wait_change is not None and wait_change >= WAIT_TIME_INCREASE_THRESHOLD_PCT:
            issues.append(
                Issue(
                    issue_id="WAIT_TIME_RISING",
                    title="Average patient wait time is rising",
                    description=(
                        f"Average wait time rose from {first.average_wait_minutes:.1f} to "
                        f"{last.average_wait_minutes:.1f} minutes ({first.year}-{last.year}), up {wait_change:.2f}%. "
                        "This is a constraint to flag for any staffing-reduction proposal, not evidence of its cause."
                    ),
                    label="OBSERVED",
                    evidence=[
                        EvidenceRef(ops_filename or "operations", first.year, "average_wait_minutes", f"{first.average_wait_minutes:.1f}"),
                        EvidenceRef(ops_filename or "operations", last.year, "average_wait_minutes", f"{last.average_wait_minutes:.1f}"),
                    ],
                    impact_score=3,
                    evidence_score=5,
                    relevance_score=5 if goal_mentions_access else 3,
                )
            )

    issues.sort(key=lambda i: i.weighted_score, reverse=True)
    return issues


def top_n(issues: list[Issue], n: int = 3) -> list[Issue]:
    return issues[:n]
