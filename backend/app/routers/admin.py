from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from app.db import get_session
from app.models import Playlist, Track, User, Video, VideoStatus

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def stats(session: Session = Depends(get_session)) -> dict:
    status_rows = session.exec(select(Video.status, func.count(Video.id)).group_by(Video.status)).all()
    return {
        "users": session.exec(select(func.count(User.id))).one(),
        "playlists": session.exec(select(func.count(Playlist.id))).one(),
        "tracks": session.exec(select(func.count(Track.id))).one(),
        "videos": session.exec(select(func.count(Video.id))).one(),
        "video_statuses": {status.value if isinstance(status, VideoStatus) else status: count for status, count in status_rows},
    }
