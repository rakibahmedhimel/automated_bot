from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.core.config import OPENAI_API_KEY, SLOTELY_SUPERADMIN_SECRET
from backend.app.core.database import get_db
from backend.app.models.api_credential import ApiCredential
from backend.app.schemas.superadmin import (
    OpenAIKeyUpdate,
    OpenAISettingResponse,
)
from backend.app.services.credential_service import (
    decrypt_api_key,
    encrypt_api_key,
    get_openai_credential,
    mask_api_key,
    secrets_match,
)

router = APIRouter(prefix="/superadmin/settings", tags=["Super admin"])


def require_superadmin(
    x_slotely_superadmin_key: str | None = Header(default=None),
):
    if not SLOTELY_SUPERADMIN_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Super-admin protection is not configured",
        )
    if not x_slotely_superadmin_key or not secrets_match(
        x_slotely_superadmin_key, SLOTELY_SUPERADMIN_SECRET
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid super-admin key",
        )


def _response(db: Session) -> OpenAISettingResponse:
    credential = get_openai_credential(db)
    if credential:
        key = decrypt_api_key(credential.encrypted_api_key)
        return OpenAISettingResponse(
            configured=True,
            masked_key=mask_api_key(key),
            updated_at=credential.updated_at,
        )
    return OpenAISettingResponse(
        configured=bool(OPENAI_API_KEY),
        masked_key=mask_api_key(OPENAI_API_KEY) if OPENAI_API_KEY else None,
        updated_at=None,
    )


@router.get(
    "/openai",
    response_model=OpenAISettingResponse,
    dependencies=[Depends(require_superadmin)],
)
def get_openai_setting(db: Session = Depends(get_db)):
    return _response(db)


@router.put(
    "/openai",
    response_model=OpenAISettingResponse,
    dependencies=[Depends(require_superadmin)],
)
def update_openai_setting(
    data: OpenAIKeyUpdate,
    db: Session = Depends(get_db),
):
    api_key = data.api_key.strip()
    if not api_key.startswith("sk-") or len(api_key) < 12:
        raise HTTPException(400, "Invalid OpenAI API key format")
    credential = (
        db.query(ApiCredential)
        .filter(ApiCredential.provider == "openai")
        .first()
    )
    if credential:
        credential.encrypted_api_key = encrypt_api_key(api_key)
        credential.is_active = True
    else:
        credential = ApiCredential(
            provider="openai",
            encrypted_api_key=encrypt_api_key(api_key),
            is_active=True,
        )
        db.add(credential)
    try:
        db.commit()
        db.refresh(credential)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(400, "Unable to update OpenAI setting") from exc
    return _response(db)


@router.delete(
    "/openai",
    response_model=OpenAISettingResponse,
    dependencies=[Depends(require_superadmin)],
)
def delete_openai_setting(db: Session = Depends(get_db)):
    credential = (
        db.query(ApiCredential)
        .filter(ApiCredential.provider == "openai")
        .first()
    )
    if credential:
        db.delete(credential)
        try:
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(400, "Unable to delete OpenAI setting") from exc
    return _response(db)
