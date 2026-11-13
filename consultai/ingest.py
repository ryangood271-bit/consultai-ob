"""File ingestion: read uploads, hash them, and persist originals for the audit trail."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .schemas import MAX_FILE_SIZE_BYTES


class UnsupportedFileError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


@dataclass
class IngestedFile:
    original_name: str
    sha256: str
    size_bytes: int
    saved_path: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _check_size(data: bytes, original_name: str) -> None:
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(
            f"{original_name} is {len(data)} bytes, exceeding the {MAX_FILE_SIZE_BYTES} byte limit."
        )


def _check_extension(original_name: str, allowed: set[str]) -> str:
    ext = Path(original_name).suffix.lower()
    if ext not in allowed:
        raise UnsupportedFileError(
            f"{original_name} has extension '{ext}', which is not one of the allowed types: {sorted(allowed)}"
        )
    return ext


def save_raw_file(data: bytes, original_name: str, run_dir: str, allowed_extensions: set[str]) -> IngestedFile:
    """Validate extension/size, persist the original bytes, and return a hash record."""
    _check_extension(original_name, allowed_extensions)
    _check_size(data, original_name)
    raw_dir = Path(run_dir) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    saved_path = raw_dir / original_name
    with open(saved_path, "wb") as f:
        f.write(data)
    return IngestedFile(
        original_name=original_name,
        sha256=sha256_bytes(data),
        size_bytes=len(data),
        saved_path=str(saved_path),
    )


def read_tabular(data: bytes, original_name: str) -> pd.DataFrame:
    """Read CSV or XLSX bytes into a DataFrame. Raises UnsupportedFileError on failure."""
    ext = Path(original_name).suffix.lower()
    import io

    try:
        if ext == ".csv":
            return pd.read_csv(io.BytesIO(data))
        elif ext == ".xlsx":
            return pd.read_excel(io.BytesIO(data))
        else:
            raise UnsupportedFileError(f"Cannot read tabular data from extension '{ext}'.")
    except Exception as e:  # noqa: BLE001 - surface as a clear ingest error, not a crash
        raise UnsupportedFileError(f"Could not parse {original_name} as tabular data: {e}") from e


class MemoReadError(Exception):
    pass


def read_memo_text(data: bytes, original_name: str) -> str:
    """Read a .txt or text-extractable .pdf memo. No OCR; scanned PDFs raise MemoReadError."""
    ext = Path(original_name).suffix.lower()
    if ext == ".txt":
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as e:
            raise MemoReadError(f"{original_name} is not valid UTF-8 text.") from e
    elif ext == ".pdf":
        try:
            import io

            from pypdf import PdfReader
        except ImportError as e:
            raise MemoReadError(
                "pypdf is not installed; cannot read PDF memos. Install it or upload a .txt memo."
            ) from e
        try:
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:  # noqa: BLE001
            raise MemoReadError(f"Could not parse {original_name} as a PDF: {e}") from e
        if not text.strip():
            raise MemoReadError(
                f"{original_name} produced no extractable text (likely a scanned/image-based PDF, which is unsupported)."
            )
        return text
    else:
        raise UnsupportedFileError(f"Memo extension '{ext}' is not supported (use .txt or .pdf).")
