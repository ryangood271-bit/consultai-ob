"""Schema constants and shared types for ConsultAI.

Hard-coded column names, limits, and enums referenced by ingest/validation/metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


FINANCE_COLUMNS = [
    "year",
    "revenue_m",
    "cogs_m",
    "operating_expenses_m",
    "reported_operating_profit_m",
]

OPERATIONS_COLUMNS = [
    "year",
    "patient_visits",
    "staff_hours",
    "labor_cost_m",
    "average_wait_minutes",
]

ALLOWED_FINANCE_EXTENSIONS = {".csv", ".xlsx"}
ALLOWED_OPERATIONS_EXTENSIONS = {".csv", ".xlsx"}
ALLOWED_MEMO_EXTENSIONS = {".txt", ".pdf"}

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

PROFIT_RECONCILIATION_TOLERANCE_M = 0.1
MIN_CONSECUTIVE_YEARS = 3


class Severity(str, Enum):
    BLOCKING = "BLOCKING"
    WARNING = "WARNING"


class RunState(str, Enum):
    BLOCKED_INPUT = "BLOCKED_INPUT"
    CALCULATIONS_READY = "CALCULATIONS_READY"
    DRAFT_REVIEW_REQUIRED = "DRAFT_REVIEW_REQUIRED"
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION"
    REJECTED = "REJECTED"
    APPROVED_INTERNAL = "APPROVED_INTERNAL"


@dataclass
class ValidationIssue:
    severity: Severity
    code: str
    message: str
    file: str
    row: str | None = None
    column: str | None = None
    expected: str | None = None
    observed: str | None = None


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def blocking(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.BLOCKING]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def is_blocked(self) -> bool:
        return len(self.blocking) > 0

    def extend(self, other: "ValidationResult") -> None:
        self.issues.extend(other.issues)
