# Voxcribe – Real-Time Speech to Text

A web application for real-time multilingual speech-to-text transcription. Speak naturally through your microphone and see your words transcribed live — with support for English, Hindi, and Hindi-English code-switching (Hinglish).

## Features

- **Real-time transcription** — audio streams via WebSocket; text appears as you speak
- **Multilingual** — English, Hindi, and mixed Hindi-English (Hinglish) with auto language detection
- **Self-hosted AI** — Faster-Whisper (large-v3-turbo) runs locally, no paid API needed
- **Voice Activity Detection** — skips silence, processes only speech
- **Full CRUD** — create, view, edit, delete transcriptions stored in PostgreSQL
- **Dashboard** — statistics on total recordings, duration, word count, and language distribution
- **Docker-ready** — one command to spin up the entire stack

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Lucide icons, React Query |
| Backend | Python 3.11, FastAPI, WebSockets, SQLAlchemy, Pydantic, Alembic |
| Speech AI | Faster-Whisper (large-v3-turbo), VAD filter, FFmpeg |
| Database | PostgreSQL 16 |
| Deploy | Docker, Docker Compose |

## Architecture

```
Browser (mic) ──WebSocket──▶ FastAPI ──▶ Faster-Whisper
     ◀── partial text ◀──────┘               │
                                              ▼
                                         PostgreSQL
```

1. Browser captures audio via MediaRecorder (WebM/Opus)
2. Audio chunks are base64-encoded and sent over WebSocket every ~1 second
3. Backend converts WebM→PCM via FFmpeg, buffers chunks
4. When enough audio accumulates (~3 seconds), Faster-Whisper transcribes it
5. Partial transcription is sent back to the browser immediately
6. On stop, final consolidated text is saved to PostgreSQL

## Quick Start

### Option A: Docker Compose (recommended)

```bash
cp .env.example .env
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option B: Local Development

**Prerequisites:** Python 3.11+, Node.js 20+, PostgreSQL, FFmpeg

#### 1. Database

```bash
# Start PostgreSQL (or use an existing instance)
docker run -d --name voxcribe-db -p 5432:5432 \
  -e POSTGRES_DB=voxcribe -e POSTGRES_PASSWORD=postgres \
  postgres:16-alpine
```

#### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
alembic upgrade head
python run.py
```

Backend runs at http://localhost:8000

#### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173 (proxies API and WS to backend)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/voxcribe` | PostgreSQL connection string |
| `WHISPER_MODEL` | `large-v3-turbo` | Faster-Whisper model name |
| `WHISPER_DEVICE` | `cpu` | `cpu` or `cuda` |
| `WHISPER_COMPUTE_TYPE` | `int8` | `int8`, `float16`, `float32` |
| `AUDIO_CHUNK_DURATION` | `3.0` | Seconds of audio per transcription chunk |
| `AUDIO_OVERLAP_DURATION` | `0.5` | Overlap between chunks (reduces missed words) |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Allowed CORS origins |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check + model status |
| `GET` | `/api/transcriptions/` | List transcriptions (paginated) |
| `GET` | `/api/transcriptions/{id}` | Get single transcription |
| `POST` | `/api/transcriptions/` | Create transcription |
| `PUT` | `/api/transcriptions/{id}` | Update transcription |
| `DELETE` | `/api/transcriptions/{id}` | Delete transcription |
| `GET` | `/api/transcriptions/stats/dashboard` | Dashboard statistics |
| `WS` | `/ws/transcribe` | Real-time audio streaming |

### WebSocket Protocol

**Client → Server:**
```json
{"type": "start_recording"}
{"type": "audio_chunk", "data": {"audio": "<base64>"}}
{"type": "pause_recording"}
{"type": "resume_recording"}
{"type": "stop_recording"}
```

**Server → Client:**
```json
{"type": "recording_started", "data": {}}
{"type": "partial_transcription", "data": {"text": "...", "language": "hi", "is_final": false}}
{"type": "final_transcription", "data": {"id": "...", "text": "...", "duration": 12.5, "language": "hi", "word_count": 20}}
{"type": "error", "data": {"message": "..."}}
```

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

## Project Structure

```
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run.py
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 001_initial_migration.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── transcription.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── transcription.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── speech_service.py
│   │   │   ├── audio_processor.py
│   │   │   └── transcription_service.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── transcriptions.py
│   │       └── websocket.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_api.py
│       └── test_audio.py
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── lib/
        │   ├── utils.ts
        │   └── api.ts
        ├── hooks/
        │   ├── useWebSocket.ts
        │   ├── useAudioRecorder.ts
        │   └── useTranscriptions.ts
        ├── components/
        │   ├── Layout.tsx
        │   └── ui/
        │       ├── button.tsx
        │       ├── input.tsx
        │       ├── textarea.tsx
        │       ├── card.tsx
        │       ├── badge.tsx
        │       └── alert-dialog.tsx
        └── pages/
            ├── RecordPage.tsx
            ├── HistoryPage.tsx
            ├── TranscriptionDetailPage.tsx
            └── DashboardPage.tsx
```

## Model Selection Guide

| Model | Size | Speed (CPU) | Quality | Recommendation |
|-------|------|-------------|---------|----------------|
| `tiny` | 75 MB | Very fast | Low | Testing only |
| `base` | 142 MB | Fast | Fair | Low-resource machines |
| `small` | 466 MB | Moderate | Good | Decent balance |
| `medium` | 1.5 GB | Slow | Very good | Good for Hindi |
| `large-v3-turbo` | 1.6 GB | Moderate | Excellent | **Recommended** |
| `large-v3` | 3.1 GB | Slow | Best | GPU recommended |

## Known Limitations

- **First model load** takes 30-120 seconds depending on model size (cached after)
- **CPU inference** is slower than GPU — expect 2-5 second latency per chunk on CPU
- **WebM→PCM conversion** requires FFmpeg installed on the backend
- Whisper processes chunks, not individual tokens — text appears in bursts, not word-by-word
- Code-switching accuracy depends on model size (large-v3-turbo recommended)

## License

MIT
