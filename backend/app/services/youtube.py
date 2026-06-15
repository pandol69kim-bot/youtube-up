import uuid
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from app.config import get_settings
from app.schemas import YouTubeUploadRequest


def upload_video(request: YouTubeUploadRequest, output_path: str) -> tuple[str, str]:
    settings = get_settings()

    if settings.youtube_upload_mode == "mock":
        prefix = "scheduled" if request.publish_at else "uploaded"
        return f"mock-{prefix}-{uuid.uuid4().hex[:12]}", "mock"

    missing = [
        name
        for name, value in {
            "YOUTUBE_CLIENT_ID": settings.youtube_client_id,
            "YOUTUBE_CLIENT_SECRET": settings.youtube_client_secret,
            "YOUTUBE_REFRESH_TOKEN": settings.youtube_refresh_token,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"YouTube 업로드 설정이 부족합니다: {', '.join(missing)}")

    if not output_path or not Path(output_path).exists():
        raise RuntimeError(f"업로드할 영상 파일을 찾을 수 없습니다: {output_path}")

    youtube_id = _real_upload(request, output_path, settings)
    return youtube_id, "real"


def _build_client(settings):
    creds = Credentials(
        token=None,
        refresh_token=settings.youtube_refresh_token,
        client_id=settings.youtube_client_id,
        client_secret=settings.youtube_client_secret,
        token_uri="https://oauth2.googleapis.com/token",
    )
    if not creds.valid:
        creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def _real_upload(request: YouTubeUploadRequest, output_path: str, settings) -> str:
    youtube = _build_client(settings)

    privacy = request.privacy_status
    publish_at_iso = None
    if request.publish_at:
        # 예약 발행 시 YouTube 정책상 privacyStatus는 반드시 "private"
        privacy = "private"
        publish_at_iso = request.publish_at.isoformat()

    body = {
        "snippet": {
            "title": request.title,
            "description": request.description,
            "tags": request.tags,
            "categoryId": "10",  # Music
        },
        "status": {
            "privacyStatus": privacy,
            **({"publishAt": publish_at_iso} if publish_at_iso else {}),
        },
    }

    media = MediaFileUpload(
        output_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=4 * 1024 * 1024,  # 4MB chunk
    )

    insert_request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        _, response = insert_request.next_chunk()

    return response["id"]
