"use client";

import {
  CalendarClock,
  CheckCircle2,
  Clapperboard,
  FileAudio,
  Image as ImageIcon,
  Loader2,
  Music2,
  Plus,
  RefreshCw,
  Upload,
  X,
  Youtube,
} from "lucide-react";
import { ChangeEvent, DragEvent, ReactNode, useEffect, useMemo, useState } from "react";
import { API_BASE, Playlist, Track, Video, api } from "./api";

const defaultDescription = "자동 생성된 플레이리스트입니다.\n\n챕터:\n";

export default function Home() {
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [selectedPlaylist, setSelectedPlaylist] = useState<Playlist | null>(null);
  const [tracks, setTracks] = useState<Track[]>([]);
  const [video, setVideo] = useState<Video | null>(null);
  const [thumbnailPath, setThumbnailPath] = useState("");
  const [title, setTitle] = useState("Late Night Focus Mix");
  const [description, setDescription] = useState(defaultDescription);
  const [tags, setTags] = useState("music, playlist, focus, study");
  const [privacy, setPrivacy] = useState("private");
  const [publishAt, setPublishAt] = useState("");
  const [bgColor, setBgColor] = useState("#101827");
  const [lyricsOpen, setLyricsOpen] = useState<Set<number>>(new Set());
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [coverPreview, setCoverPreview] = useState("");
  const [coverPath, setCoverPath] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  const [dragActive, setDragActive] = useState(false);

  const totalDuration = useMemo(() => tracks.reduce((sum, track) => sum + track.duration, 0), [tracks]);
  const canUpload = Boolean(video && ["ready", "uploaded", "scheduled"].includes(video.status));

  useEffect(() => {
    refreshPlaylists();
  }, []);

  async function refreshPlaylists() {
    const list = await api.playlists();
    setPlaylists(list);
    if (!selectedPlaylist && list[0]) {
      setSelectedPlaylist(list[0]);
      await refreshTracks(list[0].id);
    } else if (selectedPlaylist) {
      await refreshTracks(selectedPlaylist.id);
    }
  }

  async function refreshTracks(playlistId = selectedPlaylist?.id) {
    if (!playlistId) return;
    setTracks(await api.tracks(playlistId));
    try {
      const existing = await api.latestVideo(playlistId);
      if (existing) {
        setVideo(existing);
        setDescription(`${defaultDescription}${existing.chapters}`);
      } else {
        setVideo(null);
      }
    } catch {
      setVideo(null);
    }
  }

  async function createPlaylist() {
    setBusy("playlist");
    try {
      const playlist = await api.createPlaylist({ title, description });
      setSelectedPlaylist(playlist);
      setPlaylists([playlist, ...playlists]);
      setTracks([]);
      setMessage("플레이리스트가 생성되었습니다.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "플레이리스트 생성 실패");
    } finally {
      setBusy("");
    }
  }

  async function uploadFiles(files: File[]) {
    if (!selectedPlaylist || files.length === 0) return;
    setBusy("upload");
    try {
      await api.uploadTracks(selectedPlaylist.id, files);
      await refreshTracks(selectedPlaylist.id);
      setMessage(`${files.length}개 파일을 업로드했습니다.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "업로드 실패");
    } finally {
      setBusy("");
      setDragActive(false);
    }
  }

  function handleTrackChange(track: Track, key: keyof Track, value: string) {
    setTracks((items) =>
      items.map((item) =>
        item.id === track.id ? { ...item, [key]: key === "sort_order" ? Number(value) : value } : item
      )
    );
  }

  async function saveTrack(track: Track, key: keyof Track, value: string) {
    try {
      const patch = { [key]: key === "sort_order" ? Number(value) : value };
      const updated = await api.updateTrack(track.id, patch);
      setTracks((items) => items.map((item) => (item.id === updated.id ? updated : item)));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "트랙 수정 실패");
    }
  }

  function toggleLyrics(trackId: number) {
    setLyricsOpen((prev) => {
      const next = new Set(prev);
      next.has(trackId) ? next.delete(trackId) : next.add(trackId);
      return next;
    });
  }

  function onCoverChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setCoverFile(file);
    setCoverPreview(URL.createObjectURL(file));
    setCoverPath("");
  }

  function removeCover() {
    setCoverFile(null);
    setCoverPreview("");
    setCoverPath("");
  }

  async function renderVideo() {
    if (!selectedPlaylist) return;
    setBusy("render");
    try {
      let resolvedCoverPath = coverPath;
      if (coverFile && !coverPath) {
        const { path } = await api.coverUpload(coverFile);
        resolvedCoverPath = path;
        setCoverPath(path);
      }
      const rendered = await api.renderVideo(selectedPlaylist.id, bgColor, resolvedCoverPath || undefined);
      setVideo(rendered);
      setDescription(`${defaultDescription}${rendered.chapters}`);
      setMessage(rendered.status === "ready" ? "영상 렌더링이 완료되었습니다." : rendered.error_message);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "렌더링 실패");
    } finally {
      setBusy("");
    }
  }

  async function generateThumbnail() {
    if (!video) return;
    setBusy("thumbnail");
    try {
      const thumbnail = await api.generateThumbnail(video.id, title, "studio");
      setThumbnailPath(thumbnail.image_path);
      setMessage("썸네일을 생성했습니다.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "썸네일 생성 실패");
    } finally {
      setBusy("");
    }
  }

  async function uploadToYoutube() {
    if (!video) return;
    setBusy("youtube");
    try {
      const uploaded = await api.uploadYoutube({
        video_id: video.id,
        title,
        description,
        tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean),
        privacy_status: privacy,
        publish_at: publishAt ? new Date(publishAt).toISOString() : null,
      });
      setVideo(uploaded);
      setMessage(`YouTube ${uploaded.status === "scheduled" ? "예약" : "업로드"} 처리 완료: ${uploaded.youtube_video_id}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "YouTube 업로드 실패");
    } finally {
      setBusy("");
    }
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    uploadFiles(Array.from(event.dataTransfer.files));
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    uploadFiles(Array.from(event.target.files ?? []));
  }

  return (
    <main className="min-h-screen">
      <header className="border-b border-line bg-[#fbfaf5]">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal">MP3 Playlist Automation</h1>
            <p className="mt-1 text-sm text-neutral-600">업로드, 렌더링, 썸네일, YouTube 예약 발행까지 한 번에 관리합니다.</p>
          </div>
          <button onClick={refreshPlaylists} className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-md border border-line bg-white" title="새로고침">
            <RefreshCw size={18} />
          </button>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-5 px-6 py-6 lg:grid-cols-[260px_1fr_360px]">
        <aside className="rounded-md border border-line bg-[#fbfaf5] p-4 shadow-soft">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase text-neutral-500">Playlists</h2>
            <button onClick={createPlaylist} className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-md bg-pine text-white" title="플레이리스트 생성">
              {busy === "playlist" ? <Loader2 className="animate-spin" size={18} /> : <Plus size={18} />}
            </button>
          </div>
          <div className="space-y-2">
            {playlists.map((playlist) => (
              <button
                key={playlist.id}
                onClick={() => {
                  setSelectedPlaylist(playlist);
                  refreshTracks(playlist.id);
                }}
                className={`focus-ring w-full rounded-md border px-3 py-3 text-left text-sm ${
                  selectedPlaylist?.id === playlist.id ? "border-pine bg-[#e6efe8]" : "border-line bg-white"
                }`}
              >
                <span className="block font-medium">{playlist.title}</span>
                <span className="mt-1 block truncate text-xs text-neutral-500">{playlist.description || "설명 없음"}</span>
              </button>
            ))}
            {playlists.length === 0 && <p className="text-sm text-neutral-500">오른쪽 제목으로 첫 플레이리스트를 생성하세요.</p>}
          </div>
        </aside>

        <section className="space-y-5">
          <div className="rounded-md border border-line bg-[#fbfaf5] p-5 shadow-soft">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold">음원 업로드</h2>
                <p className="text-sm text-neutral-600">{tracks.length}곡 · {formatDuration(totalDuration)}</p>
              </div>
              <FileAudio className="text-pine" size={24} />
            </div>
            <label
              onDragEnter={() => setDragActive(true)}
              onDragLeave={() => setDragActive(false)}
              onDragOver={(event) => event.preventDefault()}
              onDrop={onDrop}
              className={`focus-ring flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed px-4 text-center ${
                dragActive ? "border-coral bg-[#fff2ed]" : "border-line bg-white"
              }`}
            >
              <Upload className="mb-3 text-coral" size={30} />
              <span className="font-medium">MP3/WAV/FLAC/AAC 파일을 드롭하거나 선택</span>
              <span className="mt-1 text-sm text-neutral-500">여러 파일 업로드와 대용량 스트리밍 저장을 지원합니다.</span>
              <input className="sr-only" type="file" multiple accept=".mp3,.wav,.flac,.aac,.m4a" onChange={onFileChange} />
            </label>
          </div>

          <div className="rounded-md border border-line bg-[#fbfaf5] p-5 shadow-soft">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold">커버 이미지</h2>
              <ImageIcon className="text-neutral-400" size={20} />
            </div>
            {coverPreview ? (
              <div className="relative">
                <img src={coverPreview} alt="cover preview" className="aspect-video w-full rounded-md border border-line object-cover" />
                <button onClick={removeCover} className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-white/80 shadow hover:bg-white" title="제거">
                  <X size={14} />
                </button>
              </div>
            ) : (
              <label className="focus-ring flex cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed border-line bg-white py-6 text-center text-sm text-neutral-500 hover:bg-[#f5f5f0]">
                <ImageIcon className="mb-2 text-neutral-300" size={28} />
                <span>JPG · PNG · WEBP</span>
                <span className="mt-1 text-xs">없으면 배경색으로 렌더링</span>
                <input className="sr-only" type="file" accept=".jpg,.jpeg,.png,.webp" onChange={onCoverChange} />
              </label>
            )}
          </div>

          <div className="rounded-md border border-line bg-[#fbfaf5] p-5 shadow-soft">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">트랙 편집</h2>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-1.5 text-xs text-neutral-500" title="배경색">
                  <span>배경</span>
                  <input type="color" value={bgColor} onChange={(e) => setBgColor(e.target.value)} className="h-7 w-10 cursor-pointer rounded border border-line bg-white p-0.5" />
                </label>
                <button onClick={renderVideo} disabled={!selectedPlaylist || tracks.length === 0 || busy === "render"} className="focus-ring inline-flex items-center gap-2 rounded-md bg-pine px-4 py-2 text-sm font-medium text-white disabled:opacity-45">
                  {busy === "render" ? <Loader2 className="animate-spin" size={16} /> : <Clapperboard size={16} />}
                  렌더링
                </button>
              </div>
            </div>
            <div className="overflow-hidden rounded-md border border-line">
              <div className="grid grid-cols-[56px_1.2fr_1fr_1fr_72px_36px] bg-[#ecebe3] px-3 py-2 text-xs font-semibold uppercase text-neutral-500">
                <span>순서</span><span>제목</span><span>아티스트</span><span>앨범</span><span>길이</span><span></span>
              </div>
              {tracks.map((track, index) => (
                <div key={track.id} className="border-t border-line bg-white">
                  <div className="grid grid-cols-[56px_1.2fr_1fr_1fr_72px_36px] items-center gap-2 px-3 py-2 text-sm">
                    <input className="focus-ring w-full rounded border border-line px-2 py-1" value={track.sort_order} onChange={(event) => handleTrackChange(track, "sort_order", event.target.value)} onBlur={(event) => saveTrack(track, "sort_order", event.target.value)} aria-label={`track ${index + 1} order`} />
                    <input className="focus-ring w-full rounded border border-line px-2 py-1" value={track.title} onChange={(event) => handleTrackChange(track, "title", event.target.value)} onBlur={(event) => saveTrack(track, "title", event.target.value)} aria-label={`track ${index + 1} title`} />
                    <input className="focus-ring w-full rounded border border-line px-2 py-1" value={track.artist} onChange={(event) => handleTrackChange(track, "artist", event.target.value)} onBlur={(event) => saveTrack(track, "artist", event.target.value)} aria-label={`track ${index + 1} artist`} />
                    <input className="focus-ring w-full rounded border border-line px-2 py-1" value={track.album} onChange={(event) => handleTrackChange(track, "album", event.target.value)} onBlur={(event) => saveTrack(track, "album", event.target.value)} aria-label={`track ${index + 1} album`} />
                    <span className="text-right text-neutral-600">{formatDuration(track.duration)}</span>
                    <button
                      onClick={() => toggleLyrics(track.id)}
                      title="가사 편집"
                      className={`focus-ring flex h-7 w-7 items-center justify-center rounded border ${lyricsOpen.has(track.id) ? "border-pine bg-[#e6efe8] text-pine" : "border-line text-neutral-400 hover:text-pine"}`}
                    >
                      <Music2 size={13} />
                    </button>
                  </div>
                  {lyricsOpen.has(track.id) && (
                    <div className="border-t border-dashed border-line px-3 pb-3 pt-2">
                      <p className="mb-1 text-xs font-medium text-neutral-500">가사 — 한 줄씩 입력, 재생 길이에 맞게 자동 분배</p>
                      <textarea
                        className="focus-ring h-32 w-full resize-y rounded border border-line px-3 py-2 text-sm"
                        placeholder={"첫 번째 줄 가사\n두 번째 줄 가사\n..."}
                        value={track.lyrics ?? ""}
                        onChange={(event) => handleTrackChange(track, "lyrics", event.target.value)}
                        onBlur={(event) => saveTrack(track, "lyrics", event.target.value)}
                      />
                    </div>
                  )}
                </div>
              ))}
              {tracks.length === 0 && <div className="bg-white px-4 py-8 text-center text-sm text-neutral-500">업로드된 트랙이 없습니다.</div>}
            </div>
          </div>
        </section>

        <aside className="space-y-5">
          <div className="rounded-md border border-line bg-[#fbfaf5] p-5 shadow-soft">
            <h2 className="mb-4 text-lg font-semibold">메타데이터</h2>
            <Field label="영상 제목">
              <input className="focus-ring w-full rounded-md border border-line px-3 py-2" value={title} onChange={(event) => setTitle(event.target.value)} />
            </Field>
            <Field label="설명">
              <textarea className="focus-ring h-40 w-full resize-none rounded-md border border-line px-3 py-2" value={description} onChange={(event) => setDescription(event.target.value)} />
            </Field>
            <Field label="태그">
              <input className="focus-ring w-full rounded-md border border-line px-3 py-2" value={tags} onChange={(event) => setTags(event.target.value)} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="공개범위">
                <select className="focus-ring w-full rounded-md border border-line px-3 py-2" value={privacy} onChange={(event) => setPrivacy(event.target.value)}>
                  <option value="private">Private</option>
                  <option value="unlisted">Unlisted</option>
                  <option value="public">Public</option>
                </select>
              </Field>
              <Field label="예약 시각">
                <input className="focus-ring w-full rounded-md border border-line px-3 py-2" type="datetime-local" value={publishAt} onChange={(event) => setPublishAt(event.target.value)} />
              </Field>
            </div>
          </div>

          <div className="rounded-md border border-line bg-[#fbfaf5] p-5 shadow-soft">
            <h2 className="mb-4 text-lg font-semibold">출력</h2>
            <StatusRow icon={<Clapperboard size={18} />} label="영상" value={video ? video.status : "대기"} />
            <StatusRow icon={<ImageIcon size={18} />} label="썸네일" value={thumbnailPath ? "ready" : "대기"} />
            <StatusRow icon={<Youtube size={18} />} label="YouTube" value={video?.youtube_video_id || "대기"} />
            {video?.output_path && (
              <a className="mt-3 block rounded-md border border-line bg-white px-3 py-2 text-sm text-sky" href={`${API_BASE}/files/renders/${fileName(video.output_path)}`} target="_blank">
                렌더 결과 열기
              </a>
            )}
            <YoutubeLinks videoId={video?.youtube_video_id} />
            {thumbnailPath && (
              <img className="mt-3 aspect-video w-full rounded-md border border-line object-cover" src={`${API_BASE}/files/thumbnails/${fileName(thumbnailPath)}`} alt="Generated thumbnail" />
            )}
            <div className="mt-4 grid grid-cols-2 gap-2">
              <button onClick={generateThumbnail} disabled={!video || busy === "thumbnail"} className="focus-ring inline-flex items-center justify-center gap-2 rounded-md bg-sky px-3 py-2 text-sm font-medium text-white disabled:opacity-45">
                {busy === "thumbnail" ? <Loader2 className="animate-spin" size={16} /> : <ImageIcon size={16} />}
                썸네일
              </button>
              <button onClick={uploadToYoutube} disabled={!canUpload || busy === "youtube"} className="focus-ring inline-flex items-center justify-center gap-2 rounded-md bg-coral px-3 py-2 text-sm font-medium text-white disabled:opacity-45">
                {publishAt ? <CalendarClock size={16} /> : <Youtube size={16} />}
                발행
              </button>
            </div>
          </div>

          {message && (
            <div className="rounded-md border border-line bg-white p-4 text-sm">
              <CheckCircle2 className="mb-2 text-pine" size={18} />
              {message}
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="mb-3 block text-sm">
      <span className="mb-1 block font-medium text-neutral-600">{label}</span>
      {children}
    </label>
  );
}

function StatusRow({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="mb-2 flex items-center justify-between rounded-md border border-line bg-white px-3 py-2 text-sm">
      <span className="flex items-center gap-2 text-neutral-600">{icon}{label}</span>
      <span className="max-w-40 truncate font-medium">{value}</span>
    </div>
  );
}

function YoutubeLinks({ videoId }: { videoId?: string }) {
  if (!videoId) return null;
  const isMock = videoId.startsWith("mock-");
  if (isMock) {
    return (
      <div className="mt-2 rounded-md border border-line bg-white px-3 py-2 text-xs text-neutral-400">
        Mock 모드 — 실제 YouTube 링크 없음 ({videoId})
      </div>
    );
  }
  return (
    <div className="mt-2 space-y-1">
      <a
        href={`https://studio.youtube.com/video/${videoId}/edit`}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm text-sky hover:bg-[#f0f9ff]"
      >
        <Youtube size={14} />
        YouTube Studio에서 상태 확인
      </a>
      <a
        href={`https://youtu.be/${videoId}`}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm text-neutral-600 hover:bg-[#f5f5f5]"
      >
        <Youtube size={14} />
        영상 미리보기 (youtu.be)
      </a>
    </div>
  );
}

function formatDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rest = Math.floor(seconds % 60);
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

function fileName(path: string) {
  return path.split(/[\\/]/).pop() ?? "";
}
