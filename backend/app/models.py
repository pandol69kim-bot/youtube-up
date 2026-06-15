from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class VideoStatus(str, Enum):
    draft = "draft"
    rendering = "rendering"
    ready = "ready"
    failed = "failed"
    uploaded = "uploaded"
    scheduled = "scheduled"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: UserRole = UserRole.user
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Playlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    title: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Track(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_id: int = Field(index=True)
    title: str
    artist: str = ""
    album: str = ""
    duration: float = 0
    file_path: str
    sort_order: int = 0
    lyrics: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Video(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_id: int = Field(index=True)
    youtube_video_id: str = ""
    status: VideoStatus = VideoStatus.draft
    output_path: str = ""
    error_message: str = ""
    chapters: str = ""
    scheduled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Thumbnail(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(index=True)
    image_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
