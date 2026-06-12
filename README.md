# MP3 Playlist YouTube Automation

MP3/WAV/FLAC/AAC 파일을 업로드해 플레이리스트를 만들고, 영상 렌더링, 썸네일 생성, YouTube 업로드/예약 발행까지 한 흐름으로 처리하는 MVP입니다.

## 구성

- `frontend`: Next.js + React + Tailwind CSS
- `backend`: FastAPI + SQLite 개발 DB
- `docker-compose.yml`: PostgreSQL, Redis, 백엔드, 프론트엔드 개발 실행 예시
- 로컬 파일 저장소: `uploads/`, `renders/`, `thumbnails/`

## 빠른 실행

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
npm install
npm run dev
```

프론트엔드: http://127.0.0.1:3000  
백엔드 API 문서: http://127.0.0.1:8000/docs

## 배포 전 체크

- FFmpeg 설치 후 `ffmpeg -version` 확인
- `.env.example`을 복사해 `.env` 구성
- `YOUTUBE_UPLOAD_MODE=mock`에서 핵심 플로우 검증 후 실제 OAuth 자격증명 연결
- 로컬 기본 SQLite DB는 사용자 임시 폴더의 `mp3playlist4youtube/app.db`에 생성됨
- 운영 배포 시 SQLite 대신 PostgreSQL/RDS 사용

## 테스트

```powershell
cd backend
pytest
```

```powershell
cd frontend
npm run build
```
