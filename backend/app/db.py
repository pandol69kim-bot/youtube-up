from collections.abc import Generator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _migrate()


def _migrate() -> None:
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE track ADD COLUMN lyrics TEXT NOT NULL DEFAULT ''"))
            conn.commit()
        except Exception:
            pass  # 이미 존재하면 무시


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
