import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes_auth import router as auth_router
from app.api.routes_events import router as events_router
from app.api.routes_photos import router as photos_router
from app.api.routes_process import router as process_router
from app.api.routes_superadmin import router as superadmin_router
from app.api.routes_users import router as users_router
from app.api.routes_mailing import router as mailing_router
from app.api.routes_tri_overview import router as tri_overview_router
from app.api.routes_web import router as web_router
from app.api.routes_participants import router as participants_router
from app.api.routes_frames import router as frames_router
from app.api.routes_export import router as export_router
from app.db.database import Base, engine
from app.models.auth import User  # noqa: F401
from app.models.web import WebEvent, WebPhoto, Customer, Order, OrderItem, Product, WebEventProduct  # noqa: F401
from app.models.mailing import Mailing  # noqa: F401
from app.models.participant import Participant  # noqa: F401
from app.models.frame import Frame  # noqa: F401
from config import settings

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Warn about default JWT secret
if settings.jwt_secret == "flashsport-local-secret-change-in-prod":
    logging.getLogger(__name__).warning(
        "SECURITY: Using default JWT secret! Set JWT_SECRET env variable in production."
    )

# Create tables
Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Flashsport Tri",
    description="Plateforme de photographie evenementielle sportive",
    version="2.0.0",
)


@app.on_event("startup")
def preload_models():
    """Pre-load YOLO model in background so first processing is fast."""
    if not settings.yolo_enabled:
        return
    import threading
    def _load():
        try:
            from app.services.detection import get_model
            get_model()
            logging.getLogger(__name__).info("YOLO model pre-loaded")
        except Exception as e:
            logging.getLogger(__name__).warning(f"YOLO preload failed: {e}")
    threading.Thread(target=_load, daemon=True).start()


# Security headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# CORS — configurable via CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(superadmin_router)
app.include_router(events_router)
app.include_router(photos_router)
app.include_router(process_router)
app.include_router(mailing_router)
app.include_router(tri_overview_router)
app.include_router(web_router)
app.include_router(participants_router)
app.include_router(frames_router)
app.include_router(export_router)

# Serve Vue.js frontend (built) or fallback to old frontend
DIST_DIR = Path("frontend/dist")
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="vue-assets")

# Static files (uploads + legacy)
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")

# Thumbnails directory for web storefront
_thumb_dir = Path(settings.upload_dir) / "thumbnails"
_thumb_dir.mkdir(parents=True, exist_ok=True)

# Legacy static (keep while migrating)
if Path("frontend_legacy/static").exists():
    app.mount("/static", StaticFiles(directory="frontend_legacy/static"), name="static")


@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    # API paths should 404, not serve HTML
    if full_path.startswith("api/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404)
    vue_index = DIST_DIR / "index.html"
    if vue_index.exists():
        return FileResponse(str(vue_index))
    return FileResponse("frontend_legacy/index.html")
