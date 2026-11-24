# Voxcribe – Real-Time Speech to Text

A modern, production-grade web application for real-time multilingual speech-to-text transcription. Speak naturally into your microphone and see your speech transcribed live with automatic language detection — supporting **English**, **Hindi**, and Hindi-English code-switching (**Hinglish**).

---

## Features

- **Real-Time Live Transcription** — Audio streams seamlessly via WebSocket using an incremental sliding window; partial text updates live on your screen.
- **Multilingual & Code-Switching** — Transcribes English, Hindi (Devanagari), and mixed Hindi-English (Hinglish) with automatic language detection.
- **Self-Hosted AI Engine** — Powered by [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) with INT8 CPU quantization and GPU support. No paid APIs or third-party cloud audio sharing required.
- **Anti-Hallucination & Noise Gate** — Built-in silence gating (RMS energy detection) and Whisper repetition filters to prevent hallucinations.
- **Full History & CRUD Management** — Store, view, search, edit titles/notes, and delete transcriptions backed by a relational database (PostgreSQL or SQLite).
- **Interactive Analytics Dashboard** — View metrics on total recordings, speech duration, word counts, and language breakdown charts.
- **Docker & Cloud Ready** — One-command deployment via Docker Compose or 1-click cloud deployment (Hugging Face Spaces, Render, Railway).

---

## Tech Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **Frontend** | React 18, TypeScript, Vite | Fast, responsive modern SPA |
| **UI & Styling** | Tailwind CSS, shadcn/ui, Lucide Icons | Clean modern UI with responsive recording interface |
| **State & API** | TanStack React Query | Cache management and seamless CRUD synchronization |
| **Backend API** | FastAPI (Python 3.11), WebSockets | Asynchronous high-performance REST and WS server |
| **Speech AI** | Faster-Whisper, CTranslate2, FFmpeg | Accelerated Whisper inference engine with INT8 / FP16 support |
| **Database** | PostgreSQL 16 (or SQLite) | Relational persistence with SQLAlchemy & Alembic migrations |
| **Web Proxy** | Nginx Alpine | Reverse proxy for frontend assets, REST API, and WebSocket streaming |
| **Orchestration**| Docker & Docker Compose | Containerized multi-service deployment |

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
                  │              Nginx Proxy                │
                  │    Port 3000 (HTTP) & /ws/ (WebSockets) │
                  └──────────────┬──────────────────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────────────────┐
                  │           FastAPI Backend               │
                  │  1. AudioProcessor (FFmpeg WebM ➔ PCM)   │
                  │  2. Noise Gate & Sliding Window         │
                  │  3. Faster-Whisper (INT8 / GPU)         │
                  └──────────────┬──────────────────────────┘
                                 │
                         ┌───────┴────────┐
                         ▼                ▼
                  ┌──────────────┐ ┌──────────────┐
                  │  PostgreSQL  │ │ Whisper Cache│
                  │  Database    │ │ Model Cache  │
                  └──────────────┘ └──────────────┘
```

---

## Quick Start (Local Deployment)

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
- **Frontend Web App:** [http://localhost:3000](http://localhost:3000)
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health & Model Status:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

To view backend logs:
```bash
docker compose logs -f backend
```

To stop all containers:
```bash
docker compose down
```

---

## Cloud Deployment Guide (Free Tiers)

Voxcribe is designed to deploy easily to free cloud platforms.

### Option 1: Hugging Face Spaces (Recommended — 100% Free with 16 GB RAM)
Hugging Face Spaces offers a completely free tier with **2 vCPUs and 16 GB RAM**, which handles Faster-Whisper `small` effortlessly.

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces) and click **Create new Space**.
2. Select **Docker** as the Space SDK (Blank).
3. Connect your GitHub repository `harishh1906/Voxcribe` or push the code directly.
4. Under **Settings > Variables and secrets**, add:
   ```env
   WHISPER_MODEL=small
   WHISPER_DEVICE=cpu
   WHISPER_COMPUTE_TYPE=int8
   WHISPER_BEAM_SIZE=3
   WHISPER_CPU_THREADS=2
   DATABASE_URL=sqlite:///./voxcribe.db
   ```
5. Hugging Face will automatically build and launch your application!

---

### Option 2: Render.com / Railway + Free Neon Postgres
1. Create a free serverless PostgreSQL database on [Neon.tech](https://neon.tech). Copy the connection string.
2. Deploy the backend as a Docker Web Service on **Railway** or **Render**.
3. Set the environment variables:
   ```env
   DATABASE_URL=postgresql://user:password@ep-xyz.neon.tech/voxcribe?sslmode=require
   WHISPER_MODEL=base
   WHISPER_DEVICE=cpu
   WHISPER_COMPUTE_TYPE=int8
   WHISPER_BEAM_SIZE=1
   WHISPER_CPU_THREADS=2
   ```

---

## Hardware Tuning & Model Selection Guide

Whisper model performance depends on your compute hardware:

| Model | Size | Speed (CPU) | Speed (NVIDIA GPU) | Multilingual & Hindi Accuracy | Recommended Hardware |
|---|---|---|---|---|---|
| **`tiny`** | ~75 MB | ⚡ Ultra Fast (>8x) | Instant | Low (drops mixed words) | Low-spec devices / quick tests |
| **`base`** | ~145 MB | ⚡ Fast (3x-5x) | Instant | Moderate (good for clear speech) | Standard laptops (i3 / i5) |
| **`small`** | ~466 MB | ⏱ Balanced (1x-2x) | 🚀 15x real-time | **High (best for Hindi & Hinglish)** | Multi-core desktop or GPU |
| **`medium`**| ~1.5 GB | 🐢 Slow (<0.5x) | 🚀 8x real-time | Excellent | NVIDIA GPU (>= 6GB VRAM) |
| **`large-v3`**| ~3.1 GB | 🛑 Unusable on CPU | 🚀 4x real-time | State of the art | NVIDIA GPU (>= 8GB VRAM) |

### Recommended Profiles in `.env`:

#### For Laptops & Low-Core CPUs (Speed Priority)
```env
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_BEAM_SIZE=1
WHISPER_CPU_THREADS=4
```

#### For High-Performance CPUs or balanced accuracy (Accuracy Priority)
```env
WHISPER_MODEL=small
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_BEAM_SIZE=3
WHISPER_CPU_THREADS=4
```

#### For NVIDIA GPU Machines (CUDA)
```env
WHISPER_MODEL=small
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
WHISPER_BEAM_SIZE=5
```

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/voxcribe` | PostgreSQL or SQLite connection string |
| `WHISPER_MODEL` | `small` | Faster-Whisper model (`tiny`, `base`, `small`, `medium`, `large-v3`) |
| `WHISPER_DEVICE` | `cpu` | Processing device (`cpu` or `cuda`) |
| `WHISPER_COMPUTE_TYPE` | `int8` | Weight precision (`int8` for CPU, `float16` for GPU) |
| `WHISPER_BEAM_SIZE` | `3` | Decoding beam size (`1` for greedy/fastest, `3-5` for accuracy) |
| `WHISPER_CPU_THREADS` | `4` | Number of physical CPU threads allocated to CTranslate2 |
| `AUDIO_SAMPLE_RATE` | `16000` | Target sample rate for Whisper inference (16 kHz) |
| `CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Allowed CORS origins for REST and WebSockets |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## API & WebSocket Specification

### REST Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check + current model load state |
| `GET` | `/api/transcriptions/` | List transcriptions (paginated, with search & filtering) |
| `POST` | `/api/transcriptions/` | Create a transcription entry |
| `GET` | `/api/transcriptions/{id}` | Get transcription details by UUID |
| `PUT` | `/api/transcriptions/{id}` | Update title or notes |
| `DELETE`| `/api/transcriptions/{id}` | Delete a transcription entry |
| `GET` | `/api/transcriptions/stats/dashboard` | Aggregated dashboard analytics |

### WebSocket Protocol (`/ws/transcribe`)

#### Client Message Types:
- `{"type": "start_recording"}` — Initializes a new session.
- `{"type": "audio_chunk", "data": {"audio": "<base64_webm>"}}` — Streams audio chunks.
- `{"type": "pause_recording"}` / `{"type": "resume_recording"}` — Temporarily pauses/resumes capture.
- `{"type": "stop_recording"}` — Triggers the final consolidation pass and database persistence.
- `{"type": "ping"}` — Keep-alive heartbeat (`{"type": "pong"}`).

#### Server Message Types:
- `{"type": "recording_started", "data": {}}`
- `{"type": "partial_transcription", "data": {"text": "...", "language": "hi", "is_final": false}}`
- `{"type": "final_transcription", "data": {"id": "<uuid>", "text": "...", "duration": 14.2, "language": "hi", "word_count": 28}}`
- `{"type": "error", "data": {"message": "..."}}`

---

## Running Automated Tests

Backend unit and integration tests use SQLite in-process:

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate # On Linux/macOS

pip install -r requirements.txt
pytest tests/ -v
```

All 14 core tests verify:
- REST CRUD operations & pagination
- Audio format detection & PCM conversion
- Model loading fallbacks and silence thresholding

---

## License

This project is licensed under the MIT License.
