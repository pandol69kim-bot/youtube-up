export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type Playlist = {
  id: number;
  title: string;
  description: string;
};

export type Track = {
  id: number;
  playlist_id: number;
  title: string;
  artist: string;
  album: string;
  duration: number;
  sort_order: number;
};

export type Video = {
  id: number;
  playlist_id: number;
  status: "draft" | "rendering" | "ready" | "failed" | "uploaded" | "scheduled";
  output_path: string;
  youtube_video_id: string;
  error_message: string;
  chapters: string;
  scheduled_at: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof body.detail === "string" ? body.detail : "요청 처리 중 오류가 발생했습니다.");
  }
  return response.json() as Promise<T>;
}

export const api = {
  playlists: () => request<Playlist[]>("/playlists"),
  createPlaylist: (payload: { title: string; description: string }) =>
    request<Playlist>("/playlists", { method: "POST", body: JSON.stringify(payload) }),
  tracks: (playlistId: number) => request<Track[]>(`/tracks?playlist_id=${playlistId}`),
  uploadTracks: (playlistId: number, files: File[]) => {
    const form = new FormData();
    form.append("playlist_id", String(playlistId));
    files.forEach((file) => form.append("files", file));
    return request<Track[]>("/tracks/upload", { method: "POST", body: form });
  },
  updateTrack: (trackId: number, payload: Partial<Track>) =>
    request<Track>(`/tracks/${trackId}`, { method: "PUT", body: JSON.stringify(payload) }),
  latestVideo: (playlistId: number) =>
    request<Video>(`/video/latest/${playlistId}`),
  renderVideo: (playlistId: number, backgroundColor: string) =>
    request<Video>("/video/render", {
      method: "POST",
      body: JSON.stringify({ playlist_id: playlistId, background_color: backgroundColor }),
    }),
  generateThumbnail: (videoId: number, title: string, style: string) =>
    request<{ id: number; image_path: string }>("/thumbnail/generate", {
      method: "POST",
      body: JSON.stringify({ video_id: videoId, title, style }),
    }),
  uploadYoutube: (payload: {
    video_id: number;
    title: string;
    description: string;
    tags: string[];
    privacy_status: string;
    publish_at?: string | null;
  }) => request<Video>("/youtube/upload", { method: "POST", body: JSON.stringify(payload) }),
  stats: () => request<Record<string, unknown>>("/admin/stats"),
};
