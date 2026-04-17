from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "sqlite:///./flashsport.db"
    upload_dir: Path = Path("./uploads")
    yolo_model_path: str = "yolov8n.pt"
    yolo_confidence: float = 0.35
    quality_blur_threshold: float = 40.0
    quality_blur_good: float = 200.0
    score_threshold_bon: float = 0.55
    score_threshold_incertain: float = 0.3
    openai_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
