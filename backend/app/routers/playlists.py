from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Playlist
from app.schemas import PlaylistCreate, PlaylistUpdate

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.get("")
def list_playlists(session: Session = Depends(get_session)) -> list[Playlist]:
    return list(session.exec(select(Playlist).order_by(Playlist.created_at.desc())).all())


@router.post("")
def create_playlist(payload: PlaylistCreate, session: Session = Depends(get_session)) -> Playlist:
    playlist = Playlist(user_id=1, title=payload.title, description=payload.description)
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    return playlist


@router.put("/{playlist_id}")
def update_playlist(playlist_id: int, payload: PlaylistUpdate, session: Session = Depends(get_session)) -> Playlist:
    playlist = session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="플레이리스트를 찾을 수 없습니다.")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(playlist, key, value)
    session.add(playlist)
    session.commit()
    session.refresh(playlist)
    return playlist


@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: int, session: Session = Depends(get_session)) -> dict[str, bool]:
    playlist = session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="플레이리스트를 찾을 수 없습니다.")
    session.delete(playlist)
    session.commit()
    return {"ok": True}
