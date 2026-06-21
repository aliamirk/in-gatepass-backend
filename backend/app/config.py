import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # IMPORTANT!

# Resolve logo path relative to this file so it works regardless of cwd
_DEFAULT_LOGO_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "logo.jpeg")
)


class Settings(BaseSettings):
    APP_NAME: str = "Gate Pass Management API"

    MONGO_URI: str = os.getenv(
        "MONGO_URI",
        "mongodb://localhost:27017/"
    )
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "in-gatepass_db")

    MEDIA_ROOT: str = os.getenv("MEDIA_ROOT", "media")
    PHOTO_DIR: str = "photos"
    QR_DIR: str = "qr"
    LOGO_PATH: str = _DEFAULT_LOGO_PATH  # override via LOGO_PATH env var on production
    ENV: str = os.getenv("ENV", "dev")
    DEV_NEXTJS_URL: str = os.getenv("DEV_NEXTJS_URL", "http://localhost:3000")
    PROD_NEXTJS_URL: str = os.getenv("PROD_NEXTJS_URL", "")
    DEV_BACKEND_URL: str = os.getenv("DEV_BACKEND_URL", "http://localhost:8000")
    PROD_BACKEND_URL: str = os.getenv("PROD_BACKEND_URL", "")

    class Config:
        env_file = ".env"


settings = Settings()
