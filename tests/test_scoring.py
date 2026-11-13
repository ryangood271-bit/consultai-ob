import pytest

from consultai.issue_detection import EvidenceRef, Issue


def test_weighted_score_formula():
    issue = Issue(
        issue_id="X",
        title="t",
        description="d",
        label="OBSERVED",
        evidence=[EvidenceRef("f.csv", 2025, "col", "1")],
        impact_score=5,
        evidence_score=4,
        relevance_score=3,
    )
    # 5*0.5 + 4*0.3 + 3*0.2 = 2.5 + 1.2 + 0.6 = 4.3
    assert issue.weighted_score == pytest.approx(4.3)


def test_weighted_score_ranges_1_to_5():
    issue = Issue("X", "t", "d", "OBSERVED", [], impact_score=1, evidence_score=1, relevance_score=1)
    assert issue.weighted_score == 1.0
    issue2 = Issue("X", "t", "d", "OBSERVED", [], impact_score=5, evidence_score=5, relevance_score=5)
    assert issue2.weighted_score == 5.0
