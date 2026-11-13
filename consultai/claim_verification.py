"""Cross-check AI-generated numeric/evidence claims against validated data.

Anything the AI asserts that cannot be matched to a known issue_id or evidence reference
gets flagged NEEDS HUMAN VERIFICATION rather than silently trusted.
"""

from __future__ import annotations

from dataclasses import dataclass

from .issue_detection import Issue


@dataclass
class VerifiedFinding:
    issue_id: str
    summary: str
    evidence_refs: list[str]
    status: str  # "VERIFIED" or "NEEDS HUMAN VERIFICATION"
    reason: str


def verify_findings(ai_findings: list[dict], known_issues: list[Issue]) -> list[VerifiedFinding]:
    known_ids = {issue.issue_id for issue in known_issues}
    verified: list[VerifiedFinding] = []

    for finding in ai_findings:
        issue_id = finding.get("issue_id", "")
        summary = finding.get("summary", "")
        evidence_refs = finding.get("evidence_refs", [])

        if issue_id in known_ids:
            verified.append(
                VerifiedFinding(
                    issue_id=issue_id,
                    summary=summary,
                    evidence_refs=evidence_refs,
                    status="VERIFIED",
                    reason=f"issue_id '{issue_id}' matches a code-detected candidate issue with evidence.",
                )
            )
        else:
            verified.append(
                VerifiedFinding(
                    issue_id=issue_id or "UNKNOWN",
                    summary=summary,
                    evidence_refs=evidence_refs,
                    status="NEEDS HUMAN VERIFICATION",
                    reason=(
                        f"issue_id '{issue_id}' does not match any code-detected candidate issue. "
                        "This claim is not independently verified against validated data."
                    ),
                )
            )

    return verified


def any_unverified(findings: list[VerifiedFinding]) -> bool:
    return any(f.status == "NEEDS HUMAN VERIFICATION" for f in findings)
