from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.db import get_session
from app.main import app
from fastapi.testclient import TestClient


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_session():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = override_session
app.state.skip_init_db = True


def test_health() -> None:
    SQLModel.metadata.create_all(engine)
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_playlist() -> None:
    SQLModel.metadata.create_all(engine)
    with TestClient(app) as client:
        response = client.post("/playlists", json={"title": "Test Mix", "description": "Demo"})
    assert response.status_code == 200
    assert response.json()["title"] == "Test Mix"
