from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, col, select

from app.db import get_session
from app.models import Video, VideoStatus
from app.schemas import RenderRequest, VideoResponse
from app.services.media import render_playlist_video

router = APIRouter(prefix="/video", tags=["video"])

DONE_STATUSES = (VideoStatus.ready, VideoStatus.uploaded, VideoStatus.scheduled)


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


@router.get("/latest/{playlist_id}", response_model=VideoResponse)
def get_latest_video(playlist_id: int, session: Session = Depends(get_session)) -> Video:
    """플레이리스트의 가장 최근 완료된 영상을 반환한다."""
    video = session.exec(
        select(Video)
        .where(Video.playlist_id == playlist_id)
        .where(col(Video.status).in_(DONE_STATUSES))
        .order_by(col(Video.created_at).desc())
    ).first()
    if not video:
        raise HTTPException(status_code=404, detail="렌더링된 영상이 없습니다.")
    return video


@router.get("")
def list_videos(session: Session = Depends(get_session)) -> list[Video]:
    return list(session.exec(select(Video).order_by(col(Video.created_at).desc())).all())

