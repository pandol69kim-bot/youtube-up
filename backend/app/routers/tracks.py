from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session, select

from app.config import get_settings
from app.db import get_session
from app.models import Playlist, Track
from app.schemas import TrackUpdate
from app.services.media import SUPPORTED_AUDIO, audio_metadata, safe_filename

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("")
def list_tracks(playlist_id: int | None = None, session: Session = Depends(get_session)) -> list[Track]:
    query = select(Track).order_by(Track.sort_order, Track.id)
    if playlist_id:
        query = select(Track).where(Track.playlist_id == playlist_id).order_by(Track.sort_order, Track.id)
    return list(session.exec(query).all())


@router.post("/upload")
async def upload_tracks(
    playlist_id: int = Form(...),
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_session),
) -> list[Track]:
    playlist = session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="플레이리스트를 찾을 수 없습니다.")

    settings = get_settings()
    existing_count = len(session.exec(select(Track).where(Track.playlist_id == playlist_id)).all())
    created: list[Track] = []
    for index, upload in enumerate(files):
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in SUPPORTED_AUDIO:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 형식입니다: {upload.filename}")
        target = settings.upload_dir / safe_filename(upload.filename or "audio.mp3")
        with target.open("wb") as handle:
            while chunk := await upload.read(1024 * 1024):
                handle.write(chunk)
        fallback_title = Path(upload.filename or target.name).stem
        duration, title, artist, album = audio_metadata(target, fallback_title)
        track = Track(
            playlist_id=playlist_id,
            title=title,
            artist=artist,
            album=album,
            duration=duration,
            file_path=str(target),
            sort_order=existing_count + index,
        )
        session.add(track)
        created.append(track)
    session.commit()
    for track in created:
        session.refresh(track)
    return created


@router.put("/{track_id}")
def update_track(track_id: int, payload: TrackUpdate, session: Session = Depends(get_session)) -> Track:
    track = session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="트랙을 찾을 수 없습니다.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(track, key, value)
    session.add(track)
    session.commit()
    session.refresh(track)
    return track


@router.delete("/{track_id}")
def delete_track(track_id: int, session: Session = Depends(get_session)) -> dict[str, bool]:
    track = session.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="트랙을 찾을 수 없습니다.")
    Path(track.file_path).unlink(missing_ok=True)
    session.delete(track)
    session.commit()
    return {"ok": True}
