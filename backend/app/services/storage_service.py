"""
Isolates all filesystem access for stored files in one place. Nothing
outside this module should know or care that files currently live on
local disk — if a future phase swaps this for S3, only this file changes.
"""
import os

from app.core.config import settings


def _ensure_storage_dir() -> str:
    path = os.path.abspath(settings.secure_storage_dir)
    os.makedirs(path, exist_ok=True)
    return path


def save_encrypted(stored_filename: str, ciphertext: bytes) -> str:
    """
    stored_filename is a random UUID with no extension and no user
    input — see file_validation_service / File.stored_filename. Writing
    under that name, inside a fixed base directory we control, is what
    makes path traversal irrelevant here: there is no user-controlled
    path component anywhere in this call.
    """
    base_dir = _ensure_storage_dir()
    full_path = os.path.join(base_dir, stored_filename)

    with open(full_path, "wb") as f:
        f.write(ciphertext)

    # Owner-read/write only (0600) — even another local user account on
    # the same machine can't read the encrypted blob directly. This is
    # defense-in-depth on top of encryption, not a replacement for it.
    os.chmod(full_path, 0o600)

    return full_path


def load_encrypted(storage_path: str) -> bytes:
    with open(storage_path, "rb") as f:
        return f.read()


def delete_encrypted(storage_path: str) -> None:
    if os.path.exists(storage_path):
        os.remove(storage_path)
