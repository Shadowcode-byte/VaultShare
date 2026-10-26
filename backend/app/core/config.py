"""
Centralized configuration.

Security note: every secret (DB credentials, encryption key, session
secret) is read from the environment, never hard-coded. This file only
defines *how* to read them and sane non-secret defaults — it must never
contain a real key or password.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- Database ---
    database_url: str = "sqlite:///./vaultshare_dev.db"

    # --- Sessions ---
    session_cookie_name: str = "vaultshare_session"
    session_lifetime_minutes: int = 60
    session_secret: str = "CHANGE_ME_IN_ENV"  # overridden by .env in real use

    # --- File encryption (AES-256-GCM key, 32 raw bytes, base64-encoded in .env) ---
    file_encryption_key_b64: str = ""

    # --- Upload constraints ---
    max_upload_size_bytes: int = 15 * 1024 * 1024  # 15 MB
    allowed_extensions: tuple[str, ...] = (
        ".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".jpg", ".jpeg", ".png",
    )
    secure_storage_dir: str = "./secure_storage"

    # --- App ---
    env: str = "development"


settings = Settings()
