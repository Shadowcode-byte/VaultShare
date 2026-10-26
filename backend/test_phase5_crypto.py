"""
Run with: python test_phase5_crypto.py
"""
from app.services import crypto_service, hash_service


def run():
    plaintext = b"This is Kamal's confidential VaultShare test document." * 20

    # 1. Round trip
    ciphertext, nonce_b64 = crypto_service.encrypt_bytes(plaintext, associated_data=b"file-abc")
    recovered = crypto_service.decrypt_bytes(ciphertext, nonce_b64, associated_data=b"file-abc")
    assert recovered == plaintext
    print("[PASS] encrypt -> decrypt round trip returns identical plaintext")

    # 2. Ciphertext does not contain the plaintext anywhere (sanity check
    # that we're actually encrypting, not just base64-wrapping it)
    assert b"confidential" not in ciphertext
    print("[PASS] ciphertext does not contain readable plaintext")

    # 3. Two encryptions of the SAME plaintext produce DIFFERENT ciphertext
    # (because the nonce is random each time) — this matters because
    # identical ciphertexts for identical plaintexts would leak that two
    # files are the same without anyone needing to decrypt either.
    ciphertext2, nonce2_b64 = crypto_service.encrypt_bytes(plaintext, associated_data=b"file-abc")
    assert ciphertext != ciphertext2 and nonce_b64 != nonce2_b64
    print("[PASS] encrypting the same plaintext twice yields different ciphertext+nonce")

    # 4. Tampering with even one byte of ciphertext is detected
    tampered = bytearray(ciphertext)
    tampered[0] ^= 0xFF
    try:
        crypto_service.decrypt_bytes(bytes(tampered), nonce_b64, associated_data=b"file-abc")
        print("[FAIL] tampered ciphertext was accepted!")
        raise SystemExit(1)
    except crypto_service.DecryptionError:
        print("[PASS] single-byte ciphertext tampering is detected and rejected")

    # 5. Wrong nonce is detected
    _, other_nonce_b64 = crypto_service.encrypt_bytes(b"unrelated", associated_data=b"file-abc")
    try:
        crypto_service.decrypt_bytes(ciphertext, other_nonce_b64, associated_data=b"file-abc")
        print("[FAIL] wrong nonce was accepted!")
        raise SystemExit(1)
    except crypto_service.DecryptionError:
        print("[PASS] using the wrong nonce is detected and rejected")

    # 6. AAD substitution attack: take File A's real ciphertext+nonce and
    # try to decrypt it under File B's associated_data (simulating an
    # attacker who swapped which DB row points at which encrypted blob
    # on disk). Must fail even though ciphertext+nonce are both correct
    # and untampered.
    try:
        crypto_service.decrypt_bytes(ciphertext, nonce_b64, associated_data=b"file-DIFFERENT-record")
        print("[FAIL] ciphertext decrypted successfully under the WRONG file's associated_data!")
        raise SystemExit(1)
    except crypto_service.DecryptionError:
        print("[PASS] ciphertext bound to file-abc's AAD cannot be decrypted under a different file's identity")

    # 7. Hashing: same content -> same hash; different content -> different hash
    h1 = hash_service.compute_sha256(plaintext)
    h2 = hash_service.compute_sha256(plaintext)
    h3 = hash_service.compute_sha256(plaintext + b"x")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # hex-encoded SHA-256 is always 64 chars
    print("[PASS] SHA-256 is deterministic and sensitive to any content change")

    print("\nALL PHASE 5 CRYPTO CHECKS PASSED")


if __name__ == "__main__":
    run()
