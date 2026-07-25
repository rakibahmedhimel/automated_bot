import hmac

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status
from openai import OpenAI
from sqlalchemy.orm import Session

from backend.app.core.config import (
    OPENAI_API_KEY,
    SLOTELY_SETTINGS_ENCRYPTION_KEY,
)
from backend.app.models.api_credential import ApiCredential


def _fernet() -> Fernet:
    if not SLOTELY_SETTINGS_ENCRYPTION_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Settings encryption key is not configured",
        )
    try:
        return Fernet(SLOTELY_SETTINGS_ENCRYPTION_KEY.encode())
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Settings encryption key is invalid",
        ) from exc


def encrypt_api_key(api_key: str) -> str:
    return _fernet().encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_api_key: str) -> str:
    try:
        return _fernet().decrypt(encrypted_api_key.encode()).decode()
    except InvalidToken as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stored API credential could not be decrypted",
        ) from exc


def mask_api_key(api_key: str) -> str:
    return f"{api_key[:3]}...{api_key[-4:]}"


def get_openai_credential(db: Session) -> ApiCredential | None:
    return (
        db.query(ApiCredential)
        .filter(
            ApiCredential.provider == "openai",
            ApiCredential.is_active.is_(True),
        )
        .first()
    )


def resolve_openai_api_key(db: Session) -> str:
    credential = get_openai_credential(db)
    if credential:
        return decrypt_api_key(credential.encrypted_api_key)
    if OPENAI_API_KEY:
        return OPENAI_API_KEY
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="OpenAI API key is not configured",
    )


def get_openai_client(db: Session) -> OpenAI:
    return OpenAI(api_key=resolve_openai_api_key(db))


def secrets_match(provided: str, expected: str) -> bool:
    return hmac.compare_digest(provided.encode(), expected.encode())
