"use client";

import {
  CalendarClock,
  CheckCircle2,
  Clapperboard,
  FileAudio,
  Image as ImageIcon,
  Loader2,
  Plus,
  RefreshCw,
  Upload,
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
    }
  }

  async function refreshTracks(playlistId = selectedPlaylist?.id) {
    if (!playlistId) return;
    setTracks(await api.tracks(playlistId));
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

  async function updateTrack(track: Track, key: keyof Track, value: string) {
    const patch = { [key]: key === "sort_order" ? Number(value) : value };
    const updated = await api.updateTrack(track.id, patch);
    setTracks((items) => items.map((item) => (item.id === updated.id ? updated : item)));
  }

  async function renderVideo() {
    if (!selectedPlaylist) return;
    setBusy("render");
    try {
      const rendered = await api.renderVideo(selectedPlaylist.id, "#12372a");
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
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">트랙 편집</h2>
              <button onClick={renderVideo} disabled={!selectedPlaylist || tracks.length === 0 || busy === "render"} className="focus-ring inline-flex items-center gap-2 rounded-md bg-pine px-4 py-2 text-sm font-medium text-white disabled:opacity-45">
                {busy === "render" ? <Loader2 className="animate-spin" size={16} /> : <Clapperboard size={16} />}
                렌더링
              </button>
            </div>
            <div className="overflow-hidden rounded-md border border-line">
              <div className="grid grid-cols-[56px_1.2fr_1fr_1fr_92px] bg-[#ecebe3] px-3 py-2 text-xs font-semibold uppercase text-neutral-500">
                <span>순서</span><span>제목</span><span>아티스트</span><span>앨범</span><span>길이</span>
              </div>
              {tracks.map((track, index) => (
                <div key={track.id} className="grid grid-cols-[56px_1.2fr_1fr_1fr_92px] items-center gap-2 border-t border-line bg-white px-3 py-2 text-sm">
                  <input className="focus-ring w-full rounded border border-line px-2 py-1" value={track.sort_order} onChange={(event) => updateTrack(track, "sort_order", event.target.value)} aria-label={`track ${index + 1} order`} />
                  <input className="focus-ring w-full rounded border border-line px-2 py-1" value={track.title} onChange={(event) => updateTrack(track, "title", event.target.value)} aria-label={`track ${index + 1} title`} />
                  <input className="focus-ring w-full rounded border border-line px-2 py-1" value={track.artist} onChange={(event) => updateTrack(track, "artist", event.target.value)} aria-label={`track ${index + 1} artist`} />
                  <input className="focus-ring w-full rounded border border-line px-2 py-1" value={track.album} onChange={(event) => updateTrack(track, "album", event.target.value)} aria-label={`track ${index + 1} album`} />
                  <span className="text-right text-neutral-600">{formatDuration(track.duration)}</span>
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

function formatDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rest = Math.floor(seconds % 60);
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}

function fileName(path: string) {
  return path.split(/[\\/]/).pop() ?? "";
}
