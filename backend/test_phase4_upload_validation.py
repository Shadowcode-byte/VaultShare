"""
Phase 4 test suite for file_validation_service. These are the tests
that matter most for the "Security Testing" chapter of the report —
each one is a specific attack technique against file upload, not just
a happy-path check. Run with: python test_phase4_upload_validation.py
"""
import io
import zipfile

from app.services.file_validation_service import validate_upload, FileValidationError
from app.core.config import settings


def make_ooxml(marker: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr(marker, "<root/>")
    return buf.getvalue()


def expect_rejected(label, filename, content, contains=None):
    try:
        validate_upload(filename, content)
        print(f"[FAIL] {label}: expected rejection but it was accepted")
        raise SystemExit(1)
    except FileValidationError as e:
        if contains and contains.lower() not in str(e).lower():
            print(f"[FAIL] {label}: rejected, but message '{e}' didn't mention '{contains}'")
            raise SystemExit(1)
        print(f"[PASS] {label}: rejected ({e})")


def expect_accepted(label, filename, content):
    result = validate_upload(filename, content)
    print(f"[PASS] {label}: accepted as {result.extension} / {result.detected_mime}, "
          f"display name '{result.display_filename}'")
    return result


def run():
    # --- Happy paths ---
    expect_accepted("valid PDF", "Project_Report.pdf", b"%PDF-1.4\n%%rest of a pdf...\n" + b"x" * 200)
    expect_accepted("valid TXT", "notes.txt", b"Just some plain text notes about the project.\n" * 5)
    expect_accepted("valid DOCX", "assignment.docx", make_ooxml("word/document.xml"))
    expect_accepted("valid PPTX", "slides.pptx", make_ooxml("ppt/presentation.xml"))
    expect_accepted("valid XLSX", "data.xlsx", make_ooxml("xl/workbook.xml"))
    expect_accepted("uppercase extension .PDF", "Report.PDF", b"%PDF-1.4\n" + b"x" * 200)

    # --- Extension whitelist ---
    expect_rejected("executable disguised with .exe", "virus.exe", b"MZ" + b"\x90" * 100, contains="not allowed")
    expect_rejected("no extension at all", "mysteryfile", b"some content here", contains="not allowed")
    expect_rejected("script file .php", "shell.php", b"<?php system($_GET['c']); ?>", contains="not allowed")

    # --- Content vs extension mismatch (the core defense) ---
    expect_rejected(
        "executable renamed to .pdf (double-extension-style attack)",
        "resume.pdf", b"MZ" + b"\x90" * 100,
        contains="does not match",
    )
    expect_rejected(
        "plain text renamed to .jpg",
        "photo.jpg", b"just plain text pretending to be an image" * 5,
        contains="does not match",
    )
    expect_rejected(
        "generic zip (no docx marker) renamed to .docx",
        "fake.docx", make_ooxml("some/other/file.xml"),
        contains="does not match",
    )
    expect_rejected(
        "corrupt zip renamed to .xlsx",
        "broken.xlsx", b"PK\x03\x04not really a valid zip",
        contains="does not match",
    )

    # --- Size limits ---
    expect_rejected("empty file", "empty.pdf", b"", contains="empty")
    oversized = b"%PDF-1.4\n" + b"A" * (settings.max_upload_size_bytes + 1)
    expect_rejected("oversized file", "huge.pdf", oversized, contains="size limit")

    # --- Filename sanitization / path traversal ---
    result = expect_accepted(
        "path traversal attempt in filename",
        "../../../../etc/passwd.pdf", b"%PDF-1.4\n" + b"x" * 200,
    )
    assert "/" not in result.display_filename and ".." not in result.display_filename, \
        "sanitized filename must not retain any path component"
    print(f"       -> sanitized to: '{result.display_filename}' (path components stripped)")

    expect_rejected("filename with null byte", "innocent.pdf\x00.exe", b"%PDF-1.4\n" + b"x" * 200,
                     contains="invalid")

    print("\nALL PHASE 4 FILE VALIDATION CHECKS PASSED")


if __name__ == "__main__":
    run()
