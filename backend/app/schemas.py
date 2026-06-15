from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from .models import UserRole, VideoStatus


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    email: str
    role: UserRole


class PlaylistCreate(BaseModel):
    title: str
    description: str = ""


class PlaylistUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class TrackUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    sort_order: Optional[int] = None
    lyrics: Optional[str] = None


class RenderRequest(BaseModel):
    playlist_id: int
    background_color: str = "#101827"
    cover_image_path: Optional[str] = None


class ThumbnailRequest(BaseModel):
    video_id: int
    title: str
    style: str = "midnight"


class YouTubeUploadRequest(BaseModel):
    video_id: int
    title: str
    description: str
    tags: list[str] = []
    privacy_status: str = "private"
    publish_at: Optional[datetime] = None


class VideoResponse(BaseModel):
    id: int
    playlist_id: int
    status: VideoStatus
    output_path: str
    youtube_video_id: str
    error_message: str
    chapters: str
    scheduled_at: Optional[datetime]
