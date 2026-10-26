"""
Everything an uploaded file must pass BEFORE it is ever encrypted or
written to disk. This module is deliberately framework-agnostic (no
FastAPI imports) so it can be unit-tested directly and re-used
unchanged if the web layer ever changes.

Design principle: WHITELIST, not blacklist. We enumerate the exact
extensions we accept rather than trying to enumerate every dangerous
one (.exe, .sh, .php, .js, .dll, .bat, ...) — a blacklist is always
one entry behind whatever attack technique is newest. Anything not
explicitly whitelisted is rejected by default.
"""
import io
import os
import zipfile
from dataclasses import dataclass

import magic

from app.core.config import settings


class FileValidationError(Exception):
    """Raised for any rejected upload. The message is safe to show
    to the end user directly — it never includes internal paths,
    stack traces, or raw exception text."""
    pass


@dataclass(frozen=True)
class ValidatedUpload:
    display_filename: str   # sanitized, safe to store/show — NEVER used to build a filesystem path
    extension: str           # normalized, lowercase, e.g. ".pdf"
    detected_mime: str
    size_bytes: int


# Office Open XML formats (.docx/.pptx/.xlsx) are ZIP containers, so
# libmagic alone only ever reports "application/zip" for them — it can't
# tell a Word doc from a renamed .apk or a plain empty zip. We close that
# gap by additionally requiring a specific internal file to be present,
# which is exactly the doc each format is required by spec to contain.
_SIMPLE_TYPES = {
    ".pdf": {"application/pdf"},
    ".txt": {"text/plain"},
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
}
_OOXML_TYPES = {
    ".docx": "word/document.xml",
    ".pptx": "ppt/presentation.xml",
    ".xlsx": "xl/workbook.xml",
}
_OOXML_ACCEPTABLE_MIMES = {
    "application/zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

ALLOWED_EXTENSIONS = set(_SIMPLE_TYPES) | set(_OOXML_TYPES)


def _sanitize_filename(raw_name: str) -> str:
    """
    Never trust the filename the client sent. This does NOT need to be
    perfect because the file is never saved under this name anyway (see
    File.stored_filename, a random UUID) — but the sanitized value is
    shown back to the user in the UI, so it must not carry path
    components, null bytes, or control characters.
    """
    if "\x00" in raw_name:
        raise FileValidationError("Filename is invalid.")

    # os.path.basename strips any directory component, e.g.
    # "../../etc/passwd.pdf" -> "passwd.pdf" — neutralizes path
    # traversal attempts embedded in the filename itself.
    name = os.path.basename(raw_name).strip().strip(".")

    if not name:
        raise FileValidationError("Filename is invalid.")
    if len(name) > 255:
        raise FileValidationError("Filename is too long.")
    if any(ord(ch) < 32 for ch in name):
        raise FileValidationError("Filename contains invalid characters.")

    return name


def _extension_of(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return ext


def _validate_ooxml_content(extension: str, file_bytes: bytes) -> None:
    """Confirms the zip actually contains the marker file that the
    claimed OOXML format is required to have. A generic zip, a zip
    with a different marker (wrong Office format), or a corrupt zip
    all fail here."""
    marker = _OOXML_TYPES[extension]
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            names = zf.namelist()
    except zipfile.BadZipFile:
        raise FileValidationError("File content does not match its extension.")

    if marker not in names:
        raise FileValidationError("File content does not match its extension.")


def validate_upload(raw_filename: str, file_bytes: bytes) -> ValidatedUpload:
    """
    Runs every check from the project's file-upload-security
    requirements in one place: size, extension whitelist, filename
    sanitization, and REAL content-type verification (not the
    Content-Type header the client claims, which is trivial to fake —
    we sniff the actual bytes).
    """
    if len(file_bytes) == 0:
        raise FileValidationError("File is empty.")

    if len(file_bytes) > settings.max_upload_size_bytes:
        limit_mb = settings.max_upload_size_bytes // (1024 * 1024)
        raise FileValidationError(f"File exceeds the {limit_mb}MB size limit.")

    display_filename = _sanitize_filename(raw_filename)
    extension = _extension_of(display_filename)

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise FileValidationError(f"File type '{extension or 'unknown'}' is not allowed. Allowed types: {allowed}")

    detected_mime = magic.from_buffer(file_bytes, mime=True)

    if extension in _SIMPLE_TYPES:
        if detected_mime not in _SIMPLE_TYPES[extension]:
            # This is exactly the case that catches a renamed executable
            # (MZ header) submitted as "resume.pdf", or any other
            # extension/content mismatch — the single most important
            # check in this module.
            raise FileValidationError("File content does not match its extension.")
    else:  # OOXML
        if detected_mime not in _OOXML_ACCEPTABLE_MIMES:
            raise FileValidationError("File content does not match its extension.")
        _validate_ooxml_content(extension, file_bytes)

    return ValidatedUpload(
        display_filename=display_filename,
        extension=extension,
        detected_mime=detected_mime,
        size_bytes=len(file_bytes),
    )
