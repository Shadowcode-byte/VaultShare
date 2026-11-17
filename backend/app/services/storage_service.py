"""Encrypted blob storage. Local in development; private R2 in production.

The database column encrypted_storage_path contains either a local absolute
path (legacy/dev) or an r2:// object key. Never expose object storage publicly.
"""
import os
from functools import lru_cache

from app.core.config import settings


def _use_r2():
    return bool(settings.r2_bucket)


@lru_cache(maxsize=1)
def _r2_client():
    if not all((settings.r2_endpoint_url, settings.r2_access_key_id,
                settings.r2_secret_access_key, settings.r2_bucket)):
        raise RuntimeError("R2 configuration incomplete")
    import boto3
    from botocore.config import Config
    return boto3.client(
        "s3", endpoint_url=settings.r2_endpoint_url,
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto", config=Config(signature_version="s3v4"),
    )


def _ensure_storage_dir():
    path = os.path.abspath(settings.secure_storage_dir)
    os.makedirs(path, exist_ok=True)
    return path


def save_encrypted(stored_filename: str, ciphertext: bytes) -> str:
    # UUID-generated filenames only; never accept a user-supplied path.
    if not stored_filename or any(c not in "0123456789abcdef" for c in stored_filename):
        raise ValueError("Invalid storage identifier")
    if _use_r2():
        _r2_client().put_object(
            Bucket=settings.r2_bucket, Key=stored_filename,
            Body=ciphertext, ContentType="application/octet-stream",
        )
        return "r2://" + stored_filename
    full_path = os.path.join(_ensure_storage_dir(), stored_filename)
    with open(full_path, "wb") as f:
        f.write(ciphertext)
    os.chmod(full_path, 0o600)
    return full_path


def load_encrypted(storage_path: str) -> bytes:
    if storage_path.startswith("r2://"):
        key = storage_path[5:]
        return _r2_client().get_object(Bucket=settings.r2_bucket, Key=key)["Body"].read()
    with open(storage_path, "rb") as f:
        return f.read()


def delete_encrypted(storage_path: str) -> None:
    if storage_path.startswith("r2://"):
        _r2_client().delete_object(Bucket=settings.r2_bucket, Key=storage_path[5:])
    elif os.path.exists(storage_path):
        os.remove(storage_path)
