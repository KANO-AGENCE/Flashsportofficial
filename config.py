from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "postgresql://arthurdamas@localhost/flashsport_tri"
    upload_dir: Path = Path("./uploads")
    yolo_model_path: str = "yolov8n.pt"
    yolo_confidence: float = 0.35
    quality_blur_threshold: float = 40.0
    quality_blur_good: float = 200.0
    score_threshold_bon: float = 0.55
    score_threshold_incertain: float = 0.3
    openai_api_key: str = ""
    jwt_secret: str = "flashsport-local-secret-change-in-prod"
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"

    class Config:
        env_file = ".env"


settings = Settings()
