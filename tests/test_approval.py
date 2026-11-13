import pytest

from consultai.review import IllegalTransitionError, ReviewDecision, Run
from consultai.schemas import RunState


def test_blocked_run_cannot_be_approved():
    run = Run(run_id="r1")
    run.set_validation_outcome(has_blocking_errors=True)
    assert run.state == RunState.BLOCKED_INPUT
    decision = ReviewDecision("Alex", "manager", "approve", "looks fine")
    with pytest.raises(IllegalTransitionError):
        run.record_decision(decision)


def test_run_with_no_ai_draft_cannot_be_approved():
    run = Run(run_id="r2")
    run.set_validation_outcome(has_blocking_errors=False)
    assert run.state == RunState.CALCULATIONS_READY
    decision = ReviewDecision("Alex", "manager", "approve", "looks fine")
    with pytest.raises(IllegalTransitionError):
        run.record_decision(decision)


def test_associate_cannot_approve_only_manager_can():
    run = Run(run_id="r3")
    run.set_validation_outcome(has_blocking_errors=False)
    run.mark_ai_draft_ready()
    assert run.state == RunState.DRAFT_REVIEW_REQUIRED

    with pytest.raises(IllegalTransitionError):
        run.record_decision(ReviewDecision("Jamie", "associate", "approve", "verified sources"))

    run.record_decision(ReviewDecision("Morgan", "manager", "approve", "verified and approved"))
    assert run.state == RunState.APPROVED_INTERNAL


def test_ai_draft_cannot_be_marked_ready_if_blocked():
    run = Run(run_id="r4")
    run.set_validation_outcome(has_blocking_errors=True)
    with pytest.raises(IllegalTransitionError):
        run.mark_ai_draft_ready()


def test_manager_can_reject_draft():
    run = Run(run_id="r5")
    run.set_validation_outcome(has_blocking_errors=False)
    run.mark_ai_draft_ready()
    run.record_decision(ReviewDecision("Morgan", "manager", "reject", "unsupported claim"))
    assert run.state == RunState.REJECTED


def test_return_for_correction_then_new_linked_run():
    run = Run(run_id="r6")
    run.set_validation_outcome(has_blocking_errors=True)
    run.record_decision(ReviewDecision("Jamie", "associate", "return_for_correction", "bad source data"))
    assert run.state == RunState.RETURNED_FOR_CORRECTION

    corrected_run = Run(run_id="r6-corrected", parent_run_id="r6")
    corrected_run.set_validation_outcome(has_blocking_errors=False)
    assert corrected_run.parent_run_id == "r6"
    assert corrected_run.state == RunState.CALCULATIONS_READY
