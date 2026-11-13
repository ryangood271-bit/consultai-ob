"""Mocked tests for the income-statement extraction helper. No real network call."""

import json
from unittest.mock import MagicMock, patch

import pytest

from consultai import ai_client, statement_parser


def _fake_response(body: dict):
    fake_block = MagicMock()
    fake_block.type = "text"
    fake_block.text = json.dumps(body)
    fake_response = MagicMock()
    fake_response.content = [fake_block]
    return fake_response


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ai_client.NoAPIKeyError):
        statement_parser.extract_income_statement("Revenue 100, COGS 50")


def test_empty_text_raises_without_calling_api(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    with pytest.raises(statement_parser.ExtractionSchemaError):
        statement_parser.extract_income_statement("   ")


def test_valid_extraction_round_trips(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    body = {
        "company_name": "Example Corp",
        "years": [
            {"year": 2023, "revenue_m": 100.0, "cogs_m": 55.0, "operating_expenses_m": 25.0, "reported_operating_profit_m": 20.0},
            {"year": 2024, "revenue_m": 115.0, "cogs_m": 67.0, "operating_expenses_m": 30.0, "reported_operating_profit_m": 18.0},
        ],
        "extraction_notes": ["All figures reported in millions in the source document."],
    }
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(body)

    with patch("anthropic.Anthropic", return_value=fake_client):
        result = statement_parser.extract_income_statement("Example Corp income statement ...")
        assert result.company_name == "Example Corp"
        assert len(result.years) == 2
        assert result.years[0]["revenue_m"] == 100.0


def test_empty_years_list_raises_clear_error_not_silent_empty_table(monkeypatch):
    """Regression test: an empty 'years' list used to silently produce a columnless
    DataFrame, which later failed validation with a confusing 'missing columns' error
    instead of telling the user the extraction itself found nothing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    body = {"company_name": "X", "years": [], "extraction_notes": ["Page contained no financial data."]}
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(body)

    with patch("anthropic.Anthropic", return_value=fake_client):
        with pytest.raises(statement_parser.ExtractionSchemaError, match="could not find any usable"):
            statement_parser.extract_income_statement("some unrelated text")


def test_missing_required_field_raises_schema_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    body = {"company_name": "X", "years": [{"year": 2023, "revenue_m": 100.0}], "extraction_notes": []}
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(body)

    with patch("anthropic.Anthropic", return_value=fake_client):
        with pytest.raises(statement_parser.ExtractionSchemaError):
            statement_parser.extract_income_statement("some text")


def test_extracted_draft_still_must_pass_real_validation(monkeypatch):
    """Even a 'successful' extraction is just a draft — the reconciliation check can still reject it."""
    import pandas as pd

    from consultai import validation

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    # Deliberately non-reconciling draft, as a sloppy extraction might produce.
    body = {
        "company_name": "X",
        "years": [
            {"year": 2023, "revenue_m": 100.0, "cogs_m": 55.0, "operating_expenses_m": 25.0, "reported_operating_profit_m": 999.0},
            {"year": 2024, "revenue_m": 115.0, "cogs_m": 67.0, "operating_expenses_m": 30.0, "reported_operating_profit_m": 18.0},
            {"year": 2025, "revenue_m": 130.0, "cogs_m": 82.0, "operating_expenses_m": 34.0, "reported_operating_profit_m": 14.0},
        ],
        "extraction_notes": [],
    }
    fake_client = MagicMock()
    fake_client.messages.create.return_value = _fake_response(body)

    with patch("anthropic.Anthropic", return_value=fake_client):
        result = statement_parser.extract_income_statement("some text")
        df = pd.DataFrame(result.years)
        vr = validation.validate_finance_df(df, "draft.csv")
        assert vr.is_blocked
        assert any(i.code == "FINANCE_PROFIT_MISMATCH" for i in vr.blocking)
