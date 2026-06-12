from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Thumbnail, Video, VideoStatus
from app.schemas import RenderRequest, ThumbnailRequest, VideoResponse
from app.services.media import generate_thumbnail, render_playlist_video

router = APIRouter(prefix="/video", tags=["video"])


@router.post("/render", response_model=VideoResponse)
def render_video(payload: RenderRequest, session: Session = Depends(get_session)) -> Video:
    video = Video(playlist_id=payload.playlist_id, status=VideoStatus.rendering)
    session.add(video)
    session.commit()
    session.refresh(video)
    try:
        output_path, chapters = render_playlist_video(session, payload.playlist_id, payload.background_color)
        video.output_path = str(output_path)
        video.chapters = chapters
        video.status = VideoStatus.ready
        video.updated_at = datetime.utcnow()
    except Exception as exc:
        video.status = VideoStatus.failed
        video.error_message = str(exc)
        video.updated_at = datetime.utcnow()
    session.add(video)
    session.commit()
    session.refresh(video)
    return video


@router.get("/status/{video_id}", response_model=VideoResponse)
def get_video(video_id: int, session: Session = Depends(get_session)) -> Video:
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다.")
    return video


@router.get("")
def list_videos(session: Session = Depends(get_session)) -> list[Video]:
    return list(session.exec(select(Video).order_by(Video.created_at.desc())).all())


@router.post("/thumbnail")
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
