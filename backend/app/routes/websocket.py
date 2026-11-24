import asyncio
import base64
import json
import logging
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.database import get_session_local
from app.services.speech_service import SpeechRecognitionService
from app.services.audio_processor import AudioProcessor
from app.schemas.transcription import TranscriptionCreate
from app.services import transcription_service as svc
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Max audio buffer = 10 seconds of 16kHz mono int16 = 320,000 bytes
# This caps Whisper inference to ~15s even on slow CPU
MAX_PCM_BYTES = settings.AUDIO_SAMPLE_RATE * 2 * 10  # 10 seconds


async def _send(ws: WebSocket, msg: dict):
    try:
        await ws.send_json(msg)
    except Exception:
        pass


@router.websocket("/ws/transcribe")
async def websocket_transcribe(ws: WebSocket):
    await ws.accept()
    logger.info("WebSocket client connected")

    webm_buffer = bytearray()
    raw_pcm_buffer = bytearray()
    recording = False
    paused = False
    start_time = 0.0
    last_transcribe_time = 0.0
    latest_text = ""
    detected_lang = "Hinglish"
    is_transcribing = False

    speech = SpeechRecognitionService.get_instance()

    async def do_transcribe():
        nonlocal latest_text, detected_lang, is_transcribing, last_transcribe_time
        if is_transcribing:
            return
        is_transcribing = True
        try:
            pcm = None
            if len(webm_buffer) > 1000:
                pcm = await asyncio.to_thread(
                    AudioProcessor.webm_to_pcm_float32, bytes(webm_buffer), settings.AUDIO_SAMPLE_RATE
                )
            elif len(raw_pcm_buffer) > 3200:
                pcm = AudioProcessor.pcm16_to_float32(bytes(raw_pcm_buffer))

            if pcm is not None and len(pcm) >= settings.AUDIO_SAMPLE_RATE:
                # Only transcribe the LAST 10 seconds to keep inference fast
                max_samples = settings.AUDIO_SAMPLE_RATE * 10
                if len(pcm) > max_samples:
                    pcm = pcm[-max_samples:]

                result = await speech.transcribe(pcm, settings.AUDIO_SAMPLE_RATE)
                text = result.get("text", "").strip()
                lang = result.get("language", "Hinglish")
                if text:
                    latest_text = text
                    detected_lang = lang or "Hinglish"
                    await _send(ws, {
                        "type": "partial_transcription",
                        "data": {
                            "text": latest_text,
                            "language": detected_lang,
                            "is_final": False,
                        },
                    })
            last_transcribe_time = time.time()
        except Exception as e:
            logger.error("Transcription error: %s", e)
        finally:
            is_transcribing = False

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type", "")

            if msg_type == "start_recording":
                recording = True
                paused = False
                webm_buffer.clear()
                raw_pcm_buffer.clear()
                latest_text = ""
                detected_lang = "Hinglish"
                start_time = time.time()
                last_transcribe_time = time.time()
                await _send(ws, {"type": "recording_started", "data": {}})

            elif msg_type == "audio_chunk":
                if paused or not recording:
                    if not recording:
                        recording = True
                        start_time = time.time()
                        last_transcribe_time = time.time()
                    elif paused:
                        continue

                audio_b64 = msg.get("data", {}).get("audio", "")
                if not audio_b64:
                    continue
                try:
                    chunk = base64.b64decode(audio_b64)
                except Exception:
                    continue

                fmt = AudioProcessor.detect_format(chunk)
                if fmt == "webm" or len(webm_buffer) > 0:
                    webm_buffer.extend(chunk)
                else:
                    raw_pcm_buffer.extend(chunk)
                    # Cap raw PCM buffer to last 10 seconds
                    if len(raw_pcm_buffer) > MAX_PCM_BYTES:
                        raw_pcm_buffer = raw_pcm_buffer[-MAX_PCM_BYTES:]

                # Transcribe every 2 seconds (give CPU breathing room)
                now = time.time()
                if now - last_transcribe_time >= 2.0 and not is_transcribing:
                    asyncio.create_task(do_transcribe())

            elif msg_type == "stop_recording":
                recording = False
                duration = time.time() - start_time if start_time else 0.0
                final_text = latest_text

                # One final transcription if we have no text yet
                if not final_text:
                    try:
                        pcm = None
                        if len(webm_buffer) > 1000:
                            pcm = await asyncio.to_thread(
                                AudioProcessor.webm_to_pcm_float32, bytes(webm_buffer), settings.AUDIO_SAMPLE_RATE
                            )
                        elif len(raw_pcm_buffer) > 3200:
                            pcm = AudioProcessor.pcm16_to_float32(bytes(raw_pcm_buffer))
                        if pcm is not None and len(pcm) > 1600:
                            max_samples = settings.AUDIO_SAMPLE_RATE * 10
                            if len(pcm) > max_samples:
                                pcm = pcm[-max_samples:]
                            result = await speech.transcribe(pcm, settings.AUDIO_SAMPLE_RATE)
                            final_text = result.get("text", "").strip()
                    except Exception as e:
                        logger.error("Final transcription error: %s", e)

                word_count = len(final_text.split()) if final_text else 0

                # Save to database
                saved_id = ""
                try:
                    db = get_session_local()()
                    t = svc.create_transcription(
                        db,
                        TranscriptionCreate(
                            title="Recording " + time.strftime("%Y-%m-%d %H:%M"),
                            transcription_text=final_text,
                            language_detected=detected_lang,
                            duration_seconds=round(duration, 1),
                        ),
                    )
                    saved_id = t.id
                    db.close()
                    logger.info("Saved transcription %s (%d words)", saved_id, word_count)
                except Exception as e:
                    logger.error("DB save failed: %s", e)

                await _send(ws, {
                    "type": "final_transcription",
                    "data": {
                        "id": saved_id,
                        "text": final_text,
                        "duration": round(duration, 1),
                        "language": detected_lang,
                        "word_count": word_count,
                    },
                })

                # Clear buffers
                webm_buffer.clear()
                raw_pcm_buffer.clear()

            elif msg_type == "pause_recording":
                paused = True
                await _send(ws, {"type": "recording_paused", "data": {}})

            elif msg_type == "resume_recording":
                paused = False
                await _send(ws, {"type": "recording_resumed", "data": {}})

            elif msg_type == "ping":
                await _send(ws, {"type": "pong", "data": {}})

    except (WebSocketDisconnect, RuntimeError):
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error("WebSocket error: %s", e)
