"""
The ONLY module in the codebase that touches the raw encryption key or
calls AES-GCM directly. Everything else works with plaintext bytes
(before this module) or ciphertext bytes (after it) and never sees the
key itself.

Why AES-256-GCM specifically, over e.g. AES-CBC:
GCM is an AUTHENTICATED encryption mode — it produces a ciphertext plus
a 128-bit authentication tag in one step. That tag means decryption
doesn't just fail silently on tampered data; it throws immediately,
because the tag verification fails first. CBC alone gives you only
confidentiality — you'd need to bolt on a separate HMAC to get the same
tamper-detection GCM gives you for free. That's the practical
difference to lead with in a viva: "encryption != tamper-proof unless
the mode is authenticated."
"""
import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from app.core.config import settings


class CryptoConfigError(Exception):
    """Raised at import time if the encryption key is missing or the
    wrong length — fails loudly at startup rather than accepting
    uploads it can't actually protect."""
    pass


class DecryptionError(Exception):
    """Raised when ciphertext fails authentication — either the data
    was corrupted/tampered with, or it doesn't belong to the file
    record it's being decrypted against (see associated_data below)."""
    pass


def _load_key() -> bytes:
    raw = settings.file_encryption_key_b64
    if not raw:
        raise CryptoConfigError(
            "FILE_ENCRYPTION_KEY_B64 is not set. Generate one with "
            "`python3 scripts/generate_key.py` and put it in your .env file."
        )
    try:
        key = base64.b64decode(raw, validate=True)
    except Exception:
        raise CryptoConfigError("FILE_ENCRYPTION_KEY_B64 is not valid base64.")

    if len(key) != 32:
        raise CryptoConfigError(
            f"FILE_ENCRYPTION_KEY_B64 decodes to {len(key)} bytes; AES-256 requires exactly 32."
        )
    return key


_KEY = _load_key()


def encrypt_bytes(plaintext: bytes, associated_data: bytes) -> tuple[bytes, str]:
    """
    associated_data is authenticated but NOT encrypted — GCM's tag
    covers it too, so if the ciphertext for File A is ever swapped onto
    File B's database row (e.g. by an attacker with raw disk access, or
    by an application bug), decryption fails immediately rather than
    silently returning File A's plaintext under File B's identity. We
    bind each file's stored_filename in as associated_data specifically
    to catch this class of substitution attack.

    A fresh random nonce (96 bits, GCM's recommended size) is generated
    per call — nonces must NEVER repeat under the same key, or GCM's
    confidentiality guarantee breaks. os.urandom is a CSPRNG, so
    practically the reuse probability at this scale is negligible.
    """
    nonce = os.urandom(12)
    aesgcm = AESGCM(_KEY)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    return ciphertext, base64.b64encode(nonce).decode()


def decrypt_bytes(ciphertext: bytes, nonce_b64: str, associated_data: bytes) -> bytes:
    nonce = base64.b64decode(nonce_b64)
    aesgcm = AESGCM(_KEY)
    try:
        return aesgcm.decrypt(nonce, ciphertext, associated_data)
    except InvalidTag:
        raise DecryptionError(
            "Decryption failed: the file's authentication tag did not verify. "
            "The data may have been corrupted, tampered with, or does not match this record."
        )
