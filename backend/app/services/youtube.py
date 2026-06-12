import uuid

from app.config import get_settings
from app.schemas import YouTubeUploadRequest


def upload_video(request: YouTubeUploadRequest) -> tuple[str, str]:
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
        raise RuntimeError(f"YouTube 실업로드 설정이 부족합니다: {', '.join(missing)}")

    raise NotImplementedError("실제 YouTube 업로드는 OAuth 승인 후 google-api-python-client 어댑터를 연결하세요.")
