from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "postgresql://flashsport:flashsport_pwd@localhost/flashsport_tri"
    upload_dir: Path = Path("./uploads")

    # YOLO
    yolo_model_path: str = "yolov8n.pt"
    yolo_confidence: float = 0.35

    # Quality scoring
    quality_blur_threshold: float = 40.0
    quality_blur_good: float = 200.0
    score_threshold_bon: float = 0.55
    score_threshold_incertain: float = 0.3

    # Qwen / Ollama
    qwen_model: str = "qwen2.5vl:3b"
    ollama_url: str = "http://localhost:11434"

    # Processing mode: "local" (slow, safe) or "server" (GPU, fast)
    processing_mode: str = "local"
    yolo_enabled: bool = True
    qwen_enabled: bool = True
    ai_workers: int = 1

    # Advanced OCR (consensus mode) — set to True to enable
    advanced_ocr_enabled: bool = False

    # Advanced subject filtering — photographer's eye filter before OCR
    advanced_subject_filtering_enabled: bool = False
    subject_min_quality: float = 0.25  # Below this = not a usable subject

    # Auth
    jwt_secret: str = "flashsport-local-secret-change-in-prod"
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,http://flashsport.app,http://boutique.flashsport.app"

    class Config:
        env_file = ".env"


settings = Settings()
