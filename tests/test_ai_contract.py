"""These tests never make a real network call. They verify the fail-closed contract:
missing key -> explicit error, bad JSON -> explicit error, never fabricated content.
Real end-to-end API tests are run manually per the brief, with a real key, by the student.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from consultai import ai_client


def test_missing_api_key_raises_and_makes_no_call(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ai_client.NoAPIKeyError):
        ai_client.generate_briefing({}, [], "memo text", "question")


def test_invalid_json_response_raises_schema_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")

    fake_block = MagicMock()
    fake_block.type = "text"
    fake_block.text = "not valid json at all"
    fake_response = MagicMock()
    fake_response.content = [fake_block]

    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response

    with patch("anthropic.Anthropic", return_value=fake_client):
        with pytest.raises(ai_client.AIResponseSchemaError):
            ai_client.generate_briefing({}, [], "memo text", "question")


def test_response_missing_required_key_raises_schema_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")
    import json

    fake_block = MagicMock()
    fake_block.type = "text"
    fake_block.text = json.dumps({"top_findings": []})  # missing other required keys
    fake_response = MagicMock()
    fake_response.content = [fake_block]

    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response

    with patch("anthropic.Anthropic", return_value=fake_client):
        with pytest.raises(ai_client.AIResponseSchemaError):
            ai_client.generate_briefing({}, [], "memo text", "question")


def test_too_many_top_findings_raises_schema_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")
    import json

    body = {
        "top_findings": [{"issue_id": f"X{i}", "summary": "s", "evidence_refs": []} for i in range(4)],
        "evidence_references": [],
        "why_important": "",
        "hypotheses": [],
        "proposed_investigations": [],
        "strategic_options": [],
        "limitations": [],
        "source_conflicts": [],
    }
    fake_block = MagicMock()
    fake_block.type = "text"
    fake_block.text = json.dumps(body)
    fake_response = MagicMock()
    fake_response.content = [fake_block]

    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response

    with patch("anthropic.Anthropic", return_value=fake_client):
        with pytest.raises(ai_client.AIResponseSchemaError):
            ai_client.generate_briefing({}, [], "memo text", "question")


def test_json_wrapped_in_markdown_code_fence_is_still_parsed(monkeypatch):
    """Regression test: models sometimes wrap JSON in ```json ... ``` despite instructions
    not to. This must not be treated as a schema error."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")
    import json as json_mod

    body = {
        "top_findings": [{"issue_id": "X", "summary": "s", "evidence_refs": []}],
        "evidence_references": [],
        "why_important": "",
        "hypotheses": [],
        "proposed_investigations": [],
        "strategic_options": [],
        "limitations": [],
        "source_conflicts": [],
    }
    fenced_text = "```json\n" + json_mod.dumps(body) + "\n```"
    fake_block = MagicMock()
    fake_block.type = "text"
    fake_block.text = fenced_text
    fake_response = MagicMock()
    fake_response.content = [fake_block]

    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response

    with patch("anthropic.Anthropic", return_value=fake_client):
        result = ai_client.generate_briefing({}, [], "memo text", "question")
        assert result.top_findings[0]["issue_id"] == "X"


def test_valid_response_passes_and_is_structured(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-test")
    import json

    body = {
        "top_findings": [{"issue_id": "OPERATING_MARGIN_DECLINE", "summary": "s", "evidence_refs": ["ref1"]}],
        "evidence_references": ["ref1"],
        "why_important": "because margin fell",
        "hypotheses": ["unverified: rising COGS"],
        "proposed_investigations": ["check supplier contracts"],
        "strategic_options": ["renegotiate contracts"],
        "limitations": ["synthetic data"],
        "source_conflicts": [],
    }
    fake_block = MagicMock()
    fake_block.type = "text"
    fake_block.text = json.dumps(body)
    fake_response = MagicMock()
    fake_response.content = [fake_block]

    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response

    with patch("anthropic.Anthropic", return_value=fake_client):
        result = ai_client.generate_briefing({"x": 1}, [], "memo text", "question")
        assert result.top_findings[0]["issue_id"] == "OPERATING_MARGIN_DECLINE"


def test_claim_verification_flags_unmatched_issue_id():
    from consultai.claim_verification import verify_findings
    from consultai.issue_detection import Issue

    known = [Issue("KNOWN_ID", "t", "d", "OBSERVED", [], 5, 5, 5)]
    ai_findings = [
        {"issue_id": "KNOWN_ID", "summary": "ok", "evidence_refs": []},
        {"issue_id": "MADE_UP_ID", "summary": "fabricated", "evidence_refs": []},
    ]
    verified = verify_findings(ai_findings, known)
    assert verified[0].status == "VERIFIED"
    assert verified[1].status == "NEEDS HUMAN VERIFICATION"
