import urllib.parse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlmodel import Session, select

from app.db import get_session
from app.models import Playlist, Track
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


@router.get("/export-all.md")
def export_all_playlists_md(session: Session = Depends(get_session)) -> Response:
    playlists = list(session.exec(select(Playlist).order_by(Playlist.created_at.desc())).all())
    sections: list[str] = []
    for playlist in playlists:
        tracks = list(session.exec(
            select(Track).where(Track.playlist_id == playlist.id).order_by(Track.sort_order, Track.id)
        ).all())
        sections.append(_build_md(playlist, tracks))
    md = "\n\n---\n\n".join(sections)
    return Response(
        content=md.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''playlists-all.md"},
    )


@router.get("/{playlist_id}/export.md")
def export_playlist_md(playlist_id: int, session: Session = Depends(get_session)) -> Response:
    playlist = session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="플레이리스트를 찾을 수 없습니다.")
    tracks = list(session.exec(
        select(Track).where(Track.playlist_id == playlist_id).order_by(Track.sort_order, Track.id)
    ).all())
    md = _build_md(playlist, tracks)
    safe_name = urllib.parse.quote(f"{playlist.title}.md", safe="")
    return Response(
        content=md.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}"},
    )


def _build_md(playlist: Playlist, tracks: list[Track]) -> str:
    def fmt(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    total = sum(t.duration for t in tracks)
    lines: list[str] = []

    # 헤더
    lines.append(f"# {playlist.title}")
    if playlist.description:
        lines.append(f"\n> {playlist.description}")
    lines.append(f"\n**총 {len(tracks)}곡 · {fmt(total)}**\n")
    lines.append("---\n")

    # 수록곡 테이블
    lines.append("## 수록곡\n")
    lines.append("| # | 제목 | 아티스트 | 앨범 | 길이 |")
    lines.append("|---|------|----------|------|------|")
    for i, t in enumerate(tracks, 1):
        lines.append(f"| {i} | {t.title} | {t.artist or '-'} | {t.album or '-'} | {fmt(t.duration)} |")
    lines.append("")

    # 챕터 타임스탬프
    elapsed = 0.0
    chapter_lines: list[str] = []
    for t in tracks:
        artist = f" - {t.artist}" if t.artist else ""
        chapter_lines.append(f"{fmt(elapsed)} {t.title}{artist}")
        elapsed += t.duration

    if chapter_lines:
        lines.append("---\n")
        lines.append("## 챕터\n")
        lines.append("```")
        lines.extend(chapter_lines)
        lines.append("```\n")

    # 가사
    lyric_tracks = [t for t in tracks if t.lyrics and t.lyrics.strip()]
    if lyric_tracks:
        lines.append("---\n")
        lines.append("## 가사\n")
        for i, t in enumerate(lyric_tracks, 1):
            artist = f" - {t.artist}" if t.artist else ""
            idx = tracks.index(t) + 1
            lines.append(f"### {idx}. {t.title}{artist}\n")
            lines.append(t.lyrics.strip())
            lines.append("")

    return "\n".join(lines)


@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: int, session: Session = Depends(get_session)) -> dict[str, bool]:
    playlist = session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="플레이리스트를 찾을 수 없습니다.")
    session.delete(playlist)
    session.commit()
    return {"ok": True}
