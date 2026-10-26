"""
Kept deliberately separate from crypto_service: hashing and encryption
solve two DIFFERENT problems and mixing them into one module invites
mixing them up conceptually too.

    Encryption (AES-256-GCM) -> confidentiality: can an unauthorized
        party read the file?
    Hashing (SHA-256)        -> integrity: has the file changed since
        it was uploaded, even by one bit?

A hash is not a secret and needs no key — it's computed the same way
by anyone, which is exactly what makes it useful as a fingerprint to
compare against later (see Phase 6's verify-on-download logic).
"""
import hashlib


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
