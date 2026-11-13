"""Append-only JSONL audit log per run, plus a human-readable test-log exporter."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def audit_log_path(run_dir: str) -> Path:
    return Path(run_dir) / "audit_log.jsonl"


def append_event(run_dir: str, event_type: str, details: dict) -> dict:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "details": details,
    }
    path = audit_log_path(run_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
    return event


def load_events(run_dir: str) -> list[dict]:
    path = audit_log_path(run_dir)
    if not path.exists():
        return []
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def export_test_log(run_dir: str, destination: str) -> str:
    events = load_events(run_dir)
    lines = [f"# Audit / test log — run directory: {run_dir}", ""]
    for e in events:
        lines.append(f"- **{e['timestamp']}** `{e['event_type']}`: {json.dumps(e['details'])}")
    content = "\n".join(lines)
    Path(destination).write_text(content, encoding="utf-8")
    return content
