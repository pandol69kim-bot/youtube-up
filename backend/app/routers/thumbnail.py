from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models import Thumbnail, Video
from app.schemas import ThumbnailRequest
from app.services.media import generate_thumbnail

router = APIRouter(prefix="/thumbnail", tags=["thumbnail"])


@router.post("/generate")
def create_thumbnail(payload: ThumbnailRequest, session: Session = Depends(get_session)) -> Thumbnail:
    video = session.get(Video, payload.video_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다.")
    path = generate_thumbnail(payload.video_id, payload.title, payload.style)
    thumbnail = Thumbnail(video_id=payload.video_id, image_path=str(path))
    session.add(thumbnail)
    session.commit()
    session.refresh(thumbnail)
    return thumbnail
