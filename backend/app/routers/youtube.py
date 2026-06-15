from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models import Video, VideoStatus
from app.schemas import YouTubeUploadRequest
from app.services.youtube import upload_video

router = APIRouter(prefix="/youtube", tags=["youtube"])


@router.post("/connect")
def connect() -> dict[str, str]:
    from app.config import get_settings
    settings = get_settings()
    mode = settings.youtube_upload_mode
    if mode == "real":
        return {"mode": "real", "message": "실제 YouTube 업로드 모드입니다."}
    return {"mode": "mock", "message": "Mock 모드입니다. .env의 YOUTUBE_UPLOAD_MODE=real 로 변경하면 실 업로드가 활성화됩니다."}


@router.post("/upload")
def upload(payload: YouTubeUploadRequest, session: Session = Depends(get_session)) -> Video:
    video = session.get(Video, payload.video_id)
    if not video:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다.")
    if video.status not in {VideoStatus.ready, VideoStatus.uploaded, VideoStatus.scheduled}:
        raise HTTPException(status_code=400, detail="업로드 가능한 영상 상태가 아닙니다.")
    try:
        youtube_id, _mode = upload_video(payload, video.output_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    video.youtube_video_id = youtube_id
    video.status = VideoStatus.scheduled if payload.publish_at else VideoStatus.uploaded
    video.scheduled_at = payload.publish_at
    video.updated_at = datetime.utcnow()
    session.add(video)
    session.commit()
    session.refresh(video)
    return video


@router.post("/publish")
def publish(payload: YouTubeUploadRequest, session: Session = Depends(get_session)) -> Video:
    return upload(payload, session)
