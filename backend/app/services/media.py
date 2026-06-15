import shutil
import subprocess
import tempfile
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


def audio_metadata(path: Path, fallback_title: str) -> tuple[float, str, str, str]:
    """Returns (duration, title, artist, album) extracted from audio tags."""
    audio = MutagenFile(path, easy=True)
    duration = 0.0
    title = fallback_title
    artist = ""
    album = ""
    if audio is not None:
        if audio.info:
            duration = float(getattr(audio.info, "length", 0) or 0)
        if audio.tags:
            title = str(audio.tags.get("title", [fallback_title])[0])
            artist = str(audio.tags.get("artist", [""])[0])
            album = str(audio.tags.get("album", [""])[0])
    return duration, title, artist, album


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


def _ass_ts(seconds: float) -> str:
    cs = int(seconds * 100)
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _esc(text: str) -> str:
    return text.replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def _ffmpeg_ass_path(p: Path) -> str:
    """FFmpeg -vf ass=filename= 옵션용 경로. Windows에서 드라이브 문자 : 를 \\: 로 이스케이프한다."""
    s = str(p).replace("\\", "/").replace(":", "\\\\:")
    return s


def generate_ass(tracks: list[Track]) -> str:
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1920\n"
        "PlayResY: 1080\n"
        "WrapStyle: 1\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour,"
        " BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle,"
        " BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Title,Malgun Gothic,72,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,"
        "-1,0,0,0,100,100,2,0,1,4,2,8,80,80,80,1\n"
        "Style: Lyrics,Malgun Gothic,52,&H00FFFFFF,&H000000FF,&H00000000,&HA0000000,"
        "0,0,0,0,100,100,0,0,1,3,1,2,80,80,80,1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    )

    events: list[str] = []
    elapsed = 0.0
    for track in tracks:
        title_end = elapsed + min(4.0, track.duration)
        events.append(
            f"Dialogue: 0,{_ass_ts(elapsed)},{_ass_ts(title_end)},Title,,0,0,0,,{_esc(track.title)}"
        )
        if track.lyrics and track.lyrics.strip():
            lyric_lines = [l.strip() for l in track.lyrics.strip().splitlines() if l.strip()]
            n = len(lyric_lines)
            lyric_start = elapsed + 4.5
            lyric_end = elapsed + track.duration - 0.3
            remaining = lyric_end - lyric_start
            if remaining > 0 and n > 0:
                per_line = max(2.0, remaining / n)
                t = lyric_start
                for line in lyric_lines:
                    end_t = min(t + per_line, lyric_end)
                    if t < end_t:
                        events.append(
                            f"Dialogue: 0,{_ass_ts(t)},{_ass_ts(end_t)},Lyrics,,0,0,0,,{_esc(line)}"
                        )
                    t += per_line
        elapsed += track.duration

    return header + "\n" + "\n".join(events)


def render_playlist_video(
    session: Session,
    playlist_id: int,
    background_color: str,
    cover_image_path: str | None = None,
) -> tuple[Path, str]:
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

    # ASS 자막 파일 생성 (제목 + 가사)
    ass_file = Path(tempfile.gettempdir()) / f"{uuid.uuid4().hex}.ass"
    ass_file.write_text(generate_ass(list(tracks)), encoding="utf-8-sig")

    cover = Path(cover_image_path) if cover_image_path else None
    use_cover = cover is not None and cover.exists()
    ass_filter = f"ass=filename={_ffmpeg_ass_path(ass_file)}"

    if use_cover:
        vf = f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,{ass_filter}"
        command = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(cover),
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", vf,
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_file),
        ]
    else:
        color = background_color.lstrip("#")
        if len(color) != 6:
            color = "101827"
        command = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-f", "lavfi", "-i", f"color=c=0x{color}:s=1920x1080:r=30",
            "-map", "1:v", "-map", "0:a",
            "-shortest",
            "-c:a", "aac", "-b:a", "192k",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-vf", ass_filter,
            str(output_file),
        ]

    try:
        result = subprocess.run(
            command, check=True, capture_output=True,
            encoding="utf-8", errors="replace",
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr or ""
        raise RuntimeError(f"ffmpeg 렌더링 실패:\n{stderr[-3000:]}") from exc
    finally:
        concat_file.unlink(missing_ok=True)
        ass_file.unlink(missing_ok=True)
    return output_file, chapters_for_tracks(list(tracks))


_KOREAN_FONT_CANDIDATES = [
    "C:/Windows/Fonts/malgun.ttf",
    "C:/Windows/Fonts/HANDotum.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
]


def _load_font(size: int):
    for path in _KOREAN_FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


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
    font = _load_font(72)
    small_font = _load_font(34)
    wrapped = _wrap_text(title, 18)
    draw.multiline_text((80, 160), wrapped, fill=fg, font=font, spacing=18)
    draw.text((86, 594), "AUTO PLAYLIST", fill=bg, font=small_font)
    path = settings.thumbnail_dir / f"thumbnail-{video_id}-{uuid.uuid4().hex}.jpg"
    image.save(path, quality=92)
    return path


def _wrap_text(text: str, width: int) -> str:
    lines: list[str] = []
    current = ""
    for ch in text:
        if ch == " " and not current.endswith(" "):
            current += ch
        else:
            current += ch
        if len(current.rstrip()) >= width:
            lines.append(current.rstrip())
            current = ""
    if current.strip():
        lines.append(current.strip())
    return "\n".join(lines[:4]) or "Untitled Playlist"
