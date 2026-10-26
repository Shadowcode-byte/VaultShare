"""
Run once per environment (dev, staging, prod each get their OWN key —
never share one across environments):

    python3 scripts/generate_key.py

Paste the output into FILE_ENCRYPTION_KEY_B64 in your .env file.
This script prints the key and does nothing else — it never writes to
.env for you, so you don't accidentally overwrite an existing key that
already has files encrypted under it (doing so would make those files
permanently undecryptable).
"""
import base64
import secrets

if __name__ == "__main__":
    key = secrets.token_bytes(32)  # 32 raw bytes = 256-bit key for AES-256
    print(base64.b64encode(key).decode())
