from functools import lru_cache
from pathlib import Path
from tempfile import gettempdir

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_RUNTIME_ROOT = Path(gettempdir()) / "mp3playlist4youtube"


class Settings(BaseSettings):
    app_env: str = "development"
    backend_cors_origins: str = "http://127.0.0.1:3000,http://localhost:3000"
    database_url: str = f"sqlite:///{(LOCAL_RUNTIME_ROOT / 'app.db').as_posix()}"
    upload_dir: Path = PROJECT_ROOT / "uploads"
    render_dir: Path = PROJECT_ROOT / "renders"
    thumbnail_dir: Path = PROJECT_ROOT / "thumbnails"
    covers_dir: Path = PROJECT_ROOT / "covers"
    youtube_upload_mode: str = "mock"
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_refresh_token: str = ""
    jwt_secret: str = "change-me-before-production"

    model_config = SettingsConfigDict(env_file=str(PROJECT_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.render_dir.mkdir(parents=True, exist_ok=True)
    settings.thumbnail_dir.mkdir(parents=True, exist_ok=True)
    settings.covers_dir.mkdir(parents=True, exist_ok=True)
    LOCAL_RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data").mkdir(parents=True, exist_ok=True)
    return settings
