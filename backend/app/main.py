# backend/app/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

# Import routers
from .routes import (
    auth_routes,
    hr_routes,
    gate_routes,
    pass_routes,
    media_routes,
    qrroutes,
    notificationroutes,
)

app = FastAPI(title=settings.APP_NAME)


# CORS (you can restrict origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure media folders exist (photos + QR + PDFs)
os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_ROOT, settings.PHOTO_DIR), exist_ok=True)
os.makedirs(os.path.join(settings.MEDIA_ROOT, settings.QR_DIR), exist_ok=True)

# Register all routers
app.include_router(auth_routes.router)            # /auth/...
app.include_router(hr_routes.router)             # /hr/...
app.include_router(gate_routes.router)           # /gate/...
app.include_router(pass_routes.router)           # /pass/...
app.include_router(media_routes.router)          # /media/... (upload photo, print, etc)
app.include_router(qrroutes.router)             # /qr/{pass_number}
app.include_router(notificationroutes.router)  # /notifications/admin


@app.get("/")
async def root():
    return {"message": "Gate Pass Management API running (no authentication required)"}
