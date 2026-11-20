import json
from unittest.mock import MagicMock, patch

import pytest

from consultai import ai_client, client_communication


class _FakeFinding:
    def __init__(self, issue_id, summary, status):
        self.issue_id = issue_id
        self.summary = summary
        self.status = status


def _fake_response(body: dict):
    block = MagicMock()
    block.type = "text"
    block.text = json.dumps(body)
    resp = MagicMock()
    resp.content = [block]
    return resp


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    findings = [_FakeFinding("X", "summary", "VERIFIED")]
    with pytest.raises(ai_client.NoAPIKeyError):
        client_communication.draft_client_email("Acme", "question", findings)


def test_no_verified_findings_raises_without_calling_api(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    findings = [_FakeFinding("X", "summary", "NEEDS HUMAN VERIFICATION")]
    with pytest.raises(client_communication.DraftSchemaError, match="No VERIFIED"):
        client_communication.draft_client_email("Acme", "question", findings)


def test_valid_draft_round_trips(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    findings = [_FakeFinding("OPERATING_MARGIN_DECLINE", "Margin fell.", "VERIFIED")]
    body = {"subject": "Quick update on BlueRiver's financials", "body": "Hi team, ..."}
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(body)

    with patch("anthropic.Anthropic", return_value=fake_client):
        draft = client_communication.draft_client_email("BlueRiver", "How are we doing?", findings)
        assert draft.subject == "Quick update on BlueRiver's financials"
        assert draft.source_findings == ["OPERATING_MARGIN_DECLINE"]


def test_json_code_fence_is_stripped(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    findings = [_FakeFinding("X", "s", "VERIFIED")]
    body = {"subject": "s", "body": "b"}
    fenced = "```json\n" + json.dumps(body) + "\n```"
    block = MagicMock()
    block.type = "text"
    block.text = fenced
    resp = MagicMock()
    resp.content = [block]
    fake_client = MagicMock()
    fake_client.messages.create.return_value = resp

    with patch("anthropic.Anthropic", return_value=fake_client):
        draft = client_communication.draft_client_email("Acme", "q", findings)
        assert draft.subject == "s"
