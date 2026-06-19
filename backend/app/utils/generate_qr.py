import os
import qrcode
from ..config import settings


# ---------------------------
# Ensure /media/qr directory
# ---------------------------
def ensure_qr_dir() -> str:
    qr_dir = os.path.join(settings.MEDIA_ROOT, settings.QR_DIR)
    os.makedirs(qr_dir, exist_ok=True)
    return qr_dir


# ---------------------------
# Load .env safely
# ---------------------------
def get_env_or_default(name: str, default: str) -> str:
    """
    Safely returns an env variable.
    If not found → return default.
    Always strips trailing slash.
    """
    return (os.getenv(name) or default).rstrip("/")


# ---------------------------
# Frontend URL (Next.js)
# ---------------------------
def get_frontend_url() -> str:
    env = os.getenv("ENV", "dev")

    if env == "prod":
        return get_env_or_default("PROD_NEXTJS_URL", "https://example.com")

    # dev URL
    return get_env_or_default("DEV_NEXTJS_URL", "http://localhost:3000")


# ---------------------------
# Backend API URL for static media
# ---------------------------
def get_backend_static_url() -> str:
    env = os.getenv("ENV", "dev")

    if env == "prod":
        return get_env_or_default("PROD_BACKEND_URL", "https://api.example.com")

    return get_env_or_default("DEV_BACKEND_URL", "http://localhost:8000")


# ---------------------------
# Generate QR for a GatePass
# ---------------------------
def generate_qr_for_pass(gatepass_id: str) -> str:
    # sanitize filename
    safe_gid = gatepass_id.replace("/", "_").replace("\\", "_")

    # URL encoded in QR → Next.js opens gatepass page
    frontend_url = get_frontend_url()
    final_url = f"{frontend_url}/gatepass?gid={safe_gid}"

    # Ensure folders exist
    qr_dir = ensure_qr_dir()

    # File path
    filename = f"{safe_gid}.png"
    file_path = os.path.join(qr_dir, filename)

    # Generate QR and save
    img = qrcode.make(final_url)
    img.save(file_path)

    # URL returned to frontend so user can see QR image
    backend_url = get_backend_static_url()
    return f"{backend_url}/media/qr/{filename}"
