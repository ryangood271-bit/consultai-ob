"""Drafts a short, client-safe summary email from an APPROVED run's verified findings.

This is the "communicating with people" step of the job — but it only ever produces a DRAFT.
There is no send capability anywhere in this module or the app; a human must copy the text
into their own email client and decide whether to send it. It is also only reachable after a
run has already reached APPROVED_INTERNAL, so a human has already signed off on the underlying
findings before any client-facing language is even drafted.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from .ai_client import DEFAULT_MODEL, AICallError, AIResponseSchemaError, NoAPIKeyError, strip_json_code_fence

SYSTEM_PROMPT = """You draft a short, professional, CLIENT-FACING email summarizing a financial
analysis that has already been reviewed and approved internally.

CRITICAL RULES:
1. Use ONLY the VERIFIED findings you are given. Never mention unverified hypotheses, internal
   evidence references, issue IDs, file names, or AI-generated language. A client should never
   see the internal mechanics.
2. Keep hedged, professional tone. State only what was actually observed in the data as fact.
   Anything uncertain should be framed as "an area we'd like to discuss further," not asserted.
3. Do not propose specific strategic recommendations as final decisions -- frame them as topics
   for the upcoming conversation, since a human consultant still owns the actual client
   relationship and judgment call.
4. Keep it short: 120-180 words for the body. No markdown formatting, plain email prose.
5. Respond with ONLY a single valid JSON object, no prose outside it:

{"subject": str, "body": str}
"""


class DraftSchemaError(Exception):
    pass


@dataclass
class ClientEmailDraft:
    subject: str
    body: str
    model: str
    source_findings: list[str] = field(default_factory=list)


def draft_client_email(company_name: str, management_question: str, verified_findings: list) -> ClientEmailDraft:
    """verified_findings: list of VerifiedFinding objects; only VERIFIED ones are used."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise NoAPIKeyError("ANTHROPIC_API_KEY is not set. No draft was generated.")

    usable = [f for f in verified_findings if f.status == "VERIFIED"]
    if not usable:
        raise DraftSchemaError(
            "No VERIFIED findings are available to draft from. A client email can't be drafted "
            "from unverified claims."
        )

    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)

    try:
        import anthropic
    except ImportError as e:
        raise AICallError("The 'anthropic' package is not installed.") from e

    payload = {
        "company_name": company_name,
        "original_question": management_question,
        "verified_findings": [{"issue_id": f.issue_id, "summary": f.summary} for f in usable],
    }

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=model,
            max_tokens=700,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(payload, indent=2)}],
        )
    except Exception as e:  # noqa: BLE001
        raise AICallError(f"Anthropic API call failed: {e}") from e

    text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text").strip()
    text = strip_json_code_fence(text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise DraftSchemaError(f"Draft response was not valid JSON: {e}\nRaw: {text[:300]}") from e

    if "subject" not in data or "body" not in data:
        raise DraftSchemaError("Draft response missing 'subject' or 'body'.")

    return ClientEmailDraft(
        subject=data["subject"],
        body=data["body"],
        model=model,
        source_findings=[f.issue_id for f in usable],
    )
