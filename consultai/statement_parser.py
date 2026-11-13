"""AI-assisted extraction of finance.csv-shaped figures from an arbitrary, pasted income
statement (any company, any format/wording).

This is explicitly an EXTRACTION aid, not an analysis step: the model's job is only to read
numbers off a statement and normalize units, never to interpret, calculate, or judge them.
Its output is always shown to the user as an editable draft and must still pass the same
deterministic reconciliation check (validation.py) as any other finance file before it can be
used — so a misread figure gets caught, not silently trusted.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from .ai_client import DEFAULT_MODEL, AICallError, AIResponseSchemaError, NoAPIKeyError, strip_json_code_fence

EXTRACTION_SYSTEM_PROMPT = """You extract structured financial figures from a pasted income
statement (also called a statement of operations or P&L). The input may come from a 10-K, an
annual report, or a financial data website, in any layout or wording.

RULES:
1. Extract ONLY what is explicitly present in the text. Never invent, estimate, or infer a
   number that is not shown. If a required figure for a year is missing, omit that year rather
   than guessing.
2. Normalize every dollar figure to USD MILLIONS, converting from thousands/billions/raw
   dollars as needed based on what the statement states.
3. Map line items as follows:
   - revenue_m: total revenue / net revenue / net sales / total sales
   - cogs_m: cost of revenue / cost of goods sold / cost of sales / direct operating costs
   - operating_expenses_m: all other operating expenses (SG&A, depreciation & amortization,
     other operating costs) EXCLUDING cost of revenue — sum them if the statement lists
     several such lines, so that revenue - cogs_m - operating_expenses_m equals the
     statement's own reported operating income/profit for that year, as closely as the
     source data allows.
   - reported_operating_profit_m: the statement's own reported operating income/operating
     profit line for that year (not net income, not EBITDA).
4. If the arithmetic does not cleanly reconcile from the source statement, still report the
   figures as given and note the discrepancy in "extraction_notes" — do not force a
   reconciliation by fabricating a number.
5. Respond with ONLY a single valid JSON object, no prose outside it:

{
  "company_name": str or null,
  "years": [
    {"year": int, "revenue_m": number, "cogs_m": number, "operating_expenses_m": number, "reported_operating_profit_m": number}
  ],
  "extraction_notes": [str]
}
"""


class ExtractionSchemaError(Exception):
    pass


@dataclass
class ExtractedStatement:
    company_name: str | None
    years: list[dict] = field(default_factory=list)
    extraction_notes: list[str] = field(default_factory=list)
    model: str = ""


def extract_income_statement(raw_text: str) -> ExtractedStatement:
    """Send pasted income-statement text to the model and return a structured, UNVERIFIED draft.

    Raises NoAPIKeyError / AICallError / ExtractionSchemaError on failure — never returns
    fabricated figures.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise NoAPIKeyError("ANTHROPIC_API_KEY is not set. No extraction call was made.")

    if not raw_text or not raw_text.strip():
        raise ExtractionSchemaError("No income statement text was provided to extract from.")

    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)

    try:
        import anthropic
    except ImportError as e:
        raise AICallError("The 'anthropic' package is not installed.") from e

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Income statement text to extract from:\n\n{raw_text}"}],
        )
    except Exception as e:  # noqa: BLE001
        raise AICallError(f"Anthropic API call failed: {e}") from e

    text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text").strip()
    text = strip_json_code_fence(text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ExtractionSchemaError(f"Extraction response was not valid JSON: {e}\nRaw: {text[:500]}") from e

    if "years" not in data or not isinstance(data["years"], list):
        raise ExtractionSchemaError("Extraction response missing a 'years' list.")

    if len(data["years"]) == 0:
        notes = "; ".join(data.get("extraction_notes", [])) or "no reason given"
        raise ExtractionSchemaError(
            f"The AI could not find any usable income statement figures in what you provided "
            f"(model's notes: {notes}). Try a different source, make sure you pasted the actual "
            f"numbers (not just a page title or navigation text), or paste the figures manually."
        )

    required = {"year", "revenue_m", "cogs_m", "operating_expenses_m", "reported_operating_profit_m"}
    for row in data["years"]:
        missing = required - set(row.keys())
        if missing:
            raise ExtractionSchemaError(f"Extracted year row missing fields: {missing}")

    return ExtractedStatement(
        company_name=data.get("company_name"),
        years=data["years"],
        extraction_notes=data.get("extraction_notes", []),
        model=model,
    )
