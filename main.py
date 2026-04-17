import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_events import router as events_router
from app.api.routes_photos import router as photos_router
from app.api.routes_process import router as process_router
from app.db.database import Base, engine
from config import settings

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create tables
Base.metadata.create_all(bind=engine)

# Ensure upload directory exists
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Flashsport Tri",
    description="Tri automatique de photos sportives par dossard et qualite",
    version="1.0.0",
)

# CORS (local only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(events_router)
app.include_router(photos_router)
app.include_router(process_router)

# Static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/uploads", StaticFiles(directory=str(settings.upload_dir)), name="uploads")


@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")
