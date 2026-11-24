import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import init_db
from app.routes.transcriptions import router as transcriptions_router
from app.routes.websocket import router as ws_router
from app.services.speech_service import SpeechRecognitionService

settings = get_settings()
logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Voxcribe backend…")
    init_db()
    logger.info("Database initialised")
    # Load whisper model in background so the server starts fast
    svc = SpeechRecognitionService.get_instance()
    asyncio.create_task(svc.load_model(settings.WHISPER_MODEL, settings.WHISPER_DEVICE, settings.WHISPER_COMPUTE_TYPE))
    yield
    # Shutdown
    logger.info("Shutting down Voxcribe backend")


app = FastAPI(
    title="Voxcribe API",
    description="Real-Time Multilingual Speech-to-Text",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcriptions_router)
app.include_router(ws_router)


@app.get("/api/health")
def health():
    svc = SpeechRecognitionService.get_instance()
    return {"status": "ok", "model": svc.get_info()}


@app.get("/")
def root():
    return {"message": "Voxcribe API", "docs": "/docs"}
