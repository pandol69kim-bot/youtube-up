import shutil
import subprocess
import uuid
from pathlib import Path

from mutagen import File as MutagenFile
from PIL import Image, ImageDraw, ImageFont
from sqlmodel import Session, select

from app.config import get_settings
from app.models import Track


SUPPORTED_AUDIO = {".mp3", ".wav", ".flac", ".aac", ".m4a"}


def safe_filename(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"{uuid.uuid4().hex}{suffix}"


def audio_duration(path: Path) -> float:
    audio = MutagenFile(path)
    if audio and audio.info:
        return float(getattr(audio.info, "length", 0) or 0)
    return 0


def chapters_for_tracks(tracks: list[Track]) -> str:
    elapsed = 0
    lines: list[str] = []
    for track in tracks:
        minutes, seconds = divmod(int(elapsed), 60)
        hours, minutes = divmod(minutes, 60)
        stamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
        artist = f" - {track.artist}" if track.artist else ""
        lines.append(f"{stamp} {track.title}{artist}")
        elapsed += track.duration
    return "\n".join(lines)


def render_playlist_video(session: Session, playlist_id: int, background_color: str) -> tuple[Path, str]:
    settings = get_settings()
    tracks = session.exec(
        select(Track).where(Track.playlist_id == playlist_id).order_by(Track.sort_order, Track.id)
    ).all()
    if not tracks:
        raise ValueError("렌더링할 트랙이 없습니다.")
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg가 설치되어 있지 않습니다. 배포 전 환경에 ffmpeg를 설치하세요.")

    concat_file = settings.render_dir / f"{uuid.uuid4().hex}.txt"
    output_file = settings.render_dir / f"playlist-{playlist_id}-{uuid.uuid4().hex}.mp4"
    with concat_file.open("w", encoding="utf-8") as handle:
        for track in tracks:
            path = Path(track.file_path).resolve()
            handle.write(f"file '{path.as_posix()}'\n")

    color = background_color.lstrip("#")
    if len(color) != 6:
        color = "101827"
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x{color}:s=1920x1080:r=30",
        "-shortest",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(output_file),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    finally:
        concat_file.unlink(missing_ok=True)
    return output_file, chapters_for_tracks(list(tracks))


def generate_thumbnail(video_id: int, title: str, style: str) -> Path:
    settings = get_settings()
    palettes = {
        "midnight": ("#101827", "#e4f0ff", "#38bdf8"),
        "studio": ("#202124", "#fafafa", "#f59e0b"),
        "forest": ("#0f2a1d", "#f5fff7", "#86efac"),
    }
    bg, fg, accent = palettes.get(style, palettes["midnight"])
    image = Image.new("RGB", (1280, 720), bg)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 560, 1280, 720), fill=accent)
    font = ImageFont.load_default(size=72)
    small_font = ImageFont.load_default(size=34)
    wrapped = _wrap_text(title, 24)
    draw.multiline_text((80, 160), wrapped, fill=fg, font=font, spacing=18)
    draw.text((86, 594), "AUTO PLAYLIST", fill=bg, font=small_font)
    path = settings.thumbnail_dir / f"thumbnail-{video_id}-{uuid.uuid4().hex}.jpg"
    image.save(path, quality=92)
    return path


def _wrap_text(text: str, width: int) -> str:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines[:4]) or "Untitled Playlist"
