from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, col, select

from app.config import get_settings
from app.db import get_session
from app.models import Video, VideoStatus
from app.schemas import RenderRequest, VideoResponse
from app.services.media import render_playlist_video, safe_filename

router = APIRouter(prefix="/video", tags=["video"])

DONE_STATUSES = (VideoStatus.ready, VideoStatus.uploaded, VideoStatus.scheduled)
SUPPORTED_IMAGE = {".jpg", ".jpeg", ".png", ".webp"}


@router.post("/cover-upload")
async def upload_cover(file: UploadFile = File(...)) -> dict[str, str]:
    suffix = (file.filename or "").rsplit(".", 1)[-1].lower()
    if f".{suffix}" not in SUPPORTED_IMAGE:
        raise HTTPException(status_code=400, detail=f"지원하지 않는 이미지 형식입니다: {file.filename}")
    settings = get_settings()
    target = settings.covers_dir / safe_filename(file.filename or f"cover.{suffix}")
    with target.open("wb") as handle:
        while chunk := await file.read(1024 * 1024):
            handle.write(chunk)
    return {"path": str(target)}


@router.post("/render", response_model=VideoResponse)
def render_video(payload: RenderRequest, session: Session = Depends(get_session)) -> Video:
    video = Video(playlist_id=payload.playlist_id, status=VideoStatus.rendering)
    session.add(video)
    session.commit()
    session.refresh(video)
    try:
        output_path, chapters = render_playlist_video(
            session, payload.playlist_id, payload.background_color, payload.cover_image_path
        )
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


@router.get("/latest/{playlist_id}", response_model=Optional[VideoResponse])
def get_latest_video(playlist_id: int, session: Session = Depends(get_session)) -> Video | None:
    """플레이리스트의 가장 최근 완료된 영상을 반환한다. 없으면 null."""
    return session.exec(
        select(Video)
        .where(Video.playlist_id == playlist_id)
        .where(col(Video.status).in_(DONE_STATUSES))
        .order_by(col(Video.created_at).desc())
    ).first()


@router.get("")
def list_videos(session: Session = Depends(get_session)) -> list[Video]:
    return list(session.exec(select(Video).order_by(col(Video.created_at).desc())).all())

