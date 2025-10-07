from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or defaults."""

    database_url: str = Field(
        default="sqlite:///./via.db",
        description="SQLAlchemy compatible database URL.",
    )
    storage_root: Path = Field(
        default=Path(__file__).resolve().parents[2] / "storage",
        description="Root directory for all pipeline artefacts.",
    )
    upload_dir_name: str = Field(default="uploads")
    result_dir_name: str = Field(default="results")
    max_upload_size_mb: int = Field(default=1024)
    allow_youtube_downloads: bool = Field(default=True)
    openai_api_key: Optional[str] = Field(default=None)
    whisper_model: str = Field(default="base")
    yolov8_model: str = Field(default="yolov8n.pt")
    timeline_window: float = Field(
        default=4.0, description="Seconds around each transcript segment for merging detections."
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "VIA_"

    @validator("storage_root", pre=True)
    def _expand_storage_root(cls, value: Path | str) -> Path:
        path = Path(value).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def upload_dir(self) -> Path:
        path = self.storage_root / self.upload_dir_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def result_dir(self) -> Path:
        path = self.storage_root / self.result_dir_name
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
