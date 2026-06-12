from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import init_db
from app.routers import admin, auth, playlists, thumbnail, tracks, video, youtube

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not getattr(_app.state, "skip_init_db", False):
        init_db()
    yield


app = FastAPI(title="MP3 Playlist YouTube Automation", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
app.mount("/files/renders", StaticFiles(directory=settings.render_dir), name="renders")
app.mount("/files/thumbnails", StaticFiles(directory=settings.thumbnail_dir), name="thumbnails")

app.include_router(auth.router)
app.include_router(playlists.router)
app.include_router(tracks.router)
app.include_router(video.router)
app.include_router(thumbnail.router)
app.include_router(youtube.router)
app.include_router(admin.router)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
