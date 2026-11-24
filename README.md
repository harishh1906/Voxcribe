# Voxcribe – Real-Time Multilingual Speech to Text (Hinglish, Hindi, English)

A modern, high-performance web application for real-time speech-to-text transcription. Speak naturally into your microphone and see your speech transcribed live into fluent **Hinglish**, **Hindi**, and **English** with sub-second latency.

Powered by **Faster-Whisper** and fine-tuned on the **Oriserve Whisper-Hindi2Hinglish** architecture for natural Indian conversational speech.

---

## Key Highlights

- **Direct Neural Transcription** — Pure end-to-end model inference without fragile heuristic filters or regex bloat.
- **Dedicated Hinglish Engine** — Powered by `whisper-hindi2hinglish-swift` (CTranslate2 INT8), transcribing conversational Hindi-English code-switching directly into Roman script (*"Aapka naam kya hai"*).
- **Sub-Second Streaming Latency** — Low-overhead WebSocket audio streaming with VAD (Voice Activity Detection) to skip silence instantly.
- **Ultra-Lightweight (~78 MB Model)** — Runs effortlessly on free-tier CPUs (Render, Railway, Hugging Face) using only ~120 MB RAM.
- **Full History & Persistence** — Save, view, search, edit, and export transcriptions backed by PostgreSQL or SQLite.
- **Interactive Analytics Dashboard** — Visual metrics on total recordings, speech duration, word counts, and language distribution.
- **Docker & Cloud Ready** — One-command local startup via Docker Compose, or instant cloud deployment.

---

## Tech Stack

| Component | Technology | Description |
|---|---|---|
| **Frontend** | React 18, TypeScript, Vite | Fast, responsive Single Page Application (SPA) |
| **UI & Styling** | Tailwind CSS, shadcn/ui, Lucide Icons | Clean modern recording interface with live waveform visualizer |
| **State Management**| TanStack React Query | Data caching and real-time CRUD synchronization |
| **Backend API** | FastAPI (Python 3.11), WebSockets | Asynchronous high-performance REST and WS streaming server |
| **Speech AI** | Faster-Whisper, CTranslate2, FFmpeg | Accelerated Whisper engine with INT8 quantization |
| **Model** | `whisper-hindi2hinglish-swift-ct2` | 78 MB INT8 model optimized for Indian accents & Hinglish |
| **Database** | PostgreSQL 16 (or SQLite) | Relational persistence with SQLAlchemy ORM |
| **Proxy / Server** | Nginx Alpine / Uvicorn | Reverse proxy for assets and WebSocket streaming |
| **Containerization**| Docker & Docker Compose | Multi-container setup for seamless local & cloud deployment |

---

## System Architecture

```
                  ┌─────────────────────────────────────────┐
                  │           Browser Client (React)        │
                  │   MediaRecorder (WebM/Opus Audio)       │
                  └──────────────┬──────────────────────────┘
                                 │ WebSocket Stream (Base64)
                                 ▼
                  ┌─────────────────────────────────────────┐
                  │              FastAPI Backend            │
                  │  1. AudioProcessor (FFmpeg WebM ➔ PCM)   │
                  │  2. Faster-Whisper (INT8 CTranslate2)   │
                  │  3. Real-Time Text Streaming            │
                  └──────────────┬──────────────────────────┘
                                 │
                         ┌───────┴────────┐
                         ▼                ▼
                  ┌──────────────┐ ┌──────────────┐
                  │  PostgreSQL  │ │ Whisper-     │
                  │  Database    │ │ Hinglish     │
                  └──────────────┘ └──────────────┘
```

---

## Quick Start (Local Setup)

### Prerequisites
- [Docker](https://www.docker.com/) and [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### 1. Clone the Repository
```bash
git clone https://github.com/harishh1906/Voxcribe.git
cd Voxcribe
```

### 2. Configure Environment
Copy the sample environment file:
```bash
cp .env.example .env
```

### 3. Run with Docker Compose
```bash
docker compose up -d --build
```

Access the application:
- **Frontend App:** [http://localhost:3000](http://localhost:3000)
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## Cloud Deployment (Render.com)

Voxcribe is optimized to run smoothly on the Render Free Tier (512 MB RAM):

### 1. Database (PostgreSQL)
* Create a free PostgreSQL instance on Render.
* Copy the **External Database URL**.

### 2. Backend (Web Service)
* Build from Docker: `Dockerfile` in the root or `backend/Dockerfile`.
* Set Environment Variables:
  ```env
  DATABASE_URL=postgresql://user:password@host/voxcribe
  WHISPER_MODEL=MSpider3/whisper-hindi2hinglish-swift-ct2
  WHISPER_LANGUAGE=en
  WHISPER_DEVICE=cpu
  WHISPER_COMPUTE_TYPE=int8
  WHISPER_BEAM_SIZE=1
  WHISPER_CPU_THREADS=2
  ```

### 3. Frontend (Static Site)
* Root Directory: `frontend`
* Build Command: `npm install && npm run build`
* Publish Directory: `dist`
* Environment Variables:
  ```env
  VITE_BACKEND_URL=https://<your-backend>.onrender.com
  ```
* Redirect & Rewrite Rules:
  * Source: `/*`
  * Destination: `/index.html`
  * Action: `Rewrite`

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/voxcribe` | PostgreSQL or SQLite connection string |
| `WHISPER_MODEL` | `MSpider3/whisper-hindi2hinglish-swift-ct2` | Model repo name or Whisper size (`base`, `small`) |
| `WHISPER_LANGUAGE` | `en` | Target script (`en` outputs Latin/Roman Hinglish) |
| `WHISPER_DEVICE` | `cpu` | Processing device (`cpu` or `cuda`) |
| `WHISPER_COMPUTE_TYPE` | `int8` | Quantization precision (`int8` for fast CPU) |
| `WHISPER_BEAM_SIZE` | `1` | Beam size (`1` for greedy/fastest real-time decoding) |
| `WHISPER_CPU_THREADS` | `2` | Number of physical CPU threads allocated |
| `AUDIO_SAMPLE_RATE` | `16000` | Target audio sample rate (16 kHz) |

---

## WebSocket Protocol (`/ws/transcribe`)

### Client Messages:
* `{"type": "start_recording"}` — Initializes recording session.
* `{"type": "audio_chunk", "data": {"audio": "<base64_webm>"}}` — Streams audio chunks.
* `{"type": "pause_recording"}` / `{"type": "resume_recording"}` — Temporarily pauses/resumes.
* `{"type": "stop_recording"}` — Stops recording and persists transcription to database.
* `{"type": "ping"}` — Heartbeat ping.

### Server Messages:
* `{"type": "recording_started", "data": {}}`
* `{"type": "partial_transcription", "data": {"text": "...", "language": "Hinglish", "is_final": false}}`
* `{"type": "final_transcription", "data": {"id": "<uuid>", "text": "...", "duration": 12.4, "word_count": 24}}`

---

## License

This project is open-source and available under the [MIT License](LICENSE).
