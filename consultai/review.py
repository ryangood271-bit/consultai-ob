"""Run state machine enforcing human-in-the-loop controls.

Hard rules enforced here, not just documented:
- A run with blocking validation errors can never reach APPROVED_INTERNAL.
- A run with no genuine AI draft (NO AI GENERATED) can never reach APPROVED_INTERNAL.
- Only a reviewer whose role is "manager" may approve or reject.
- The AI/system can never set a run to APPROVED_INTERNAL itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .schemas import RunState


class IllegalTransitionError(Exception):
    pass


@dataclass
class ReviewDecision:
    reviewer_name: str
    reviewer_role: str  # "associate" or "manager"
    decision: str  # "approve", "reject", "return_for_correction"
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Run:
    run_id: str
    state: RunState = RunState.BLOCKED_INPUT
    has_blocking_errors: bool = True
    has_genuine_ai_draft: bool = False
    parent_run_id: str | None = None
    decisions: list[ReviewDecision] = field(default_factory=list)

    def set_validation_outcome(self, has_blocking_errors: bool) -> None:
        self.has_blocking_errors = has_blocking_errors
        if has_blocking_errors:
            self.state = RunState.BLOCKED_INPUT
        else:
            self.state = RunState.CALCULATIONS_READY

    def mark_ai_draft_ready(self) -> None:
        if self.has_blocking_errors:
            raise IllegalTransitionError("Cannot produce an AI draft for a run with blocking input errors.")
        self.has_genuine_ai_draft = True
        self.state = RunState.DRAFT_REVIEW_REQUIRED

    def record_decision(self, decision: ReviewDecision) -> None:
        if decision.decision == "approve":
            self._approve(decision)
        elif decision.decision == "reject":
            self._reject(decision)
        elif decision.decision == "return_for_correction":
            self._return_for_correction(decision)
        else:
            raise IllegalTransitionError(f"Unknown decision type: {decision.decision}")
        self.decisions.append(decision)

    def _approve(self, decision: ReviewDecision) -> None:
        if decision.reviewer_role != "manager":
            raise IllegalTransitionError("Only a reviewer with role 'manager' may approve a run.")
        if self.has_blocking_errors:
            raise IllegalTransitionError("Cannot approve a run that has blocking input errors.")
        if not self.has_genuine_ai_draft:
            raise IllegalTransitionError("Cannot approve a run with no genuine AI draft (NO AI GENERATED).")
        if self.state != RunState.DRAFT_REVIEW_REQUIRED:
            raise IllegalTransitionError(f"Cannot approve a run in state {self.state}.")
        self.state = RunState.APPROVED_INTERNAL

    def _reject(self, decision: ReviewDecision) -> None:
        if decision.reviewer_role != "manager":
            raise IllegalTransitionError("Only a reviewer with role 'manager' may reject a run.")
        if self.state not in (RunState.DRAFT_REVIEW_REQUIRED,):
            raise IllegalTransitionError(f"Cannot reject a run in state {self.state}.")
        self.state = RunState.REJECTED

    def _return_for_correction(self, decision: ReviewDecision) -> None:
        if self.state not in (RunState.BLOCKED_INPUT, RunState.DRAFT_REVIEW_REQUIRED):
            raise IllegalTransitionError(f"Cannot return a run in state {self.state} for correction.")
        self.state = RunState.RETURNED_FOR_CORRECTION
