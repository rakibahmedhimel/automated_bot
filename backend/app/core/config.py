import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLOTELY_SUPERADMIN_SECRET = os.getenv("SLOTELY_SUPERADMIN_SECRET")
SLOTELY_SETTINGS_ENCRYPTION_KEY = os.getenv(
    "SLOTELY_SETTINGS_ENCRYPTION_KEY"
)


def parse_allowed_origins(value: str | None) -> list[str]:
    origins = value or "http://localhost:5173"
    parsed = list(
        dict.fromkeys(
            origin.strip().rstrip("/")
            for origin in origins.split(",")
            if origin.strip().rstrip("/")
            and origin.strip().rstrip("/") != "*"
        )
    )
    return parsed or ["http://localhost:5173"]


ALLOWED_ORIGINS = parse_allowed_origins(os.getenv("ALLOWED_ORIGINS"))
