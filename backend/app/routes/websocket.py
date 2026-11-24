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


async def _send_json(ws: WebSocket, msg: dict):
    try:
        await ws.send_json(msg)
    except Exception:
        pass


@router.websocket("/ws/transcribe")
async def websocket_transcribe(ws: WebSocket):
    await ws.accept()
    logger.info("WebSocket client connected")

    # Per-connection session state
    webm_buffer = bytearray()          # full WebM for final transcription
    raw_pcm_buffer = bytearray()
    chunk_webm_buffer = bytearray()    # only new audio since last transcription
    text_segments: list[str] = []      # accumulated text segments
    recording = False
    paused = False
    start_time = 0.0
    detected_lang = ""
    last_transcribed_time = 0.0
    latest_text = ""
    is_transcribing = False
    chunk_counter = 0

    speech_svc = SpeechRecognitionService.get_instance()

    # Maximum chunk window in seconds to transcribe at a time (keep it small for speed)
    MAX_CHUNK_SECONDS = 3

    async def transcribe_current_chunk():
        """Transcribe only the latest ~5s chunk, not the full buffer."""
        nonlocal latest_text, detected_lang, is_transcribing, last_transcribed_time, chunk_counter
        if is_transcribing:
            return
        is_transcribing = True
        try:
            pcm_audio = None
            if len(chunk_webm_buffer) > 500:
                # Convert only the new chunk to PCM
                # We need the WebM header from the full buffer + the new data
                pcm_audio = await asyncio.to_thread(
                    AudioProcessor.webm_to_pcm_float32, bytes(webm_buffer), settings.AUDIO_SAMPLE_RATE
                )
                # Only take the last MAX_CHUNK_SECONDS of audio
                max_samples = int(MAX_CHUNK_SECONDS * settings.AUDIO_SAMPLE_RATE)
                if pcm_audio is not None and len(pcm_audio) > max_samples:
                    pcm_audio = pcm_audio[-max_samples:]
            elif len(raw_pcm_buffer) > 3200:
                pcm_audio = AudioProcessor.pcm16_to_float32(bytes(raw_pcm_buffer))
                max_samples = int(MAX_CHUNK_SECONDS * settings.AUDIO_SAMPLE_RATE)
                if len(pcm_audio) > max_samples:
                    pcm_audio = pcm_audio[-max_samples:]

            if pcm_audio is not None and len(pcm_audio) >= settings.AUDIO_SAMPLE_RATE:
                result = await speech_svc.transcribe(pcm_audio, settings.AUDIO_SAMPLE_RATE)
                text = result.get("text", "").strip()
                lang = result.get("language")
                if lang:
                    detected_lang = lang
                if text:
                    chunk_counter += 1
                    # Build running text: previous segments + current chunk
                    if chunk_counter <= 1:
                        latest_text = text
                    else:
                        # Replace the last chunk's text with new one
                        if len(text_segments) > 0:
                            text_segments[-1] = text
                        else:
                            text_segments.append(text)
                        latest_text = " ".join(text_segments)
                    await _send_json(ws, {
                        "type": "partial_transcription",
                        "data": {
                            "text": latest_text,
                            "language": detected_lang,
                            "is_final": False,
                        },
                    })

            # After transcribing, start a new segment every ~10 seconds
            elapsed = time.time() - start_time
            if chunk_counter > 0 and elapsed > len(text_segments) * 10 + 10:
                if latest_text:
                    # Lock in the current segment and start fresh
                    if len(text_segments) == 0 or text_segments[-1] != latest_text.split(" ")[-1]:
                        text_segments.append("")
                chunk_webm_buffer.clear()

            last_transcribed_time = time.time()
        except Exception as e:
            logger.error("Error in transcribe_current_chunk: %s", e)
        finally:
            is_transcribing = False

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await _send_json(ws, {"type": "error", "data": {"message": "Invalid JSON"}})
                continue

            msg_type = msg.get("type", "")

            if msg_type == "start_recording":
                recording = True
                paused = False
                webm_buffer.clear()
                raw_pcm_buffer.clear()
                chunk_webm_buffer.clear()
                text_segments.clear()
                latest_text = ""
                detected_lang = ""
                chunk_counter = 0
                start_time = time.time()
                last_transcribed_time = time.time()
                await _send_json(ws, {"type": "recording_started", "data": {}})

            elif msg_type == "audio_chunk":
                if not recording or paused:
                    continue
                audio_b64 = msg.get("data", {}).get("audio", "")
                if not audio_b64:
                    continue
                try:
                    chunk_raw = base64.b64decode(audio_b64)
                except Exception:
                    continue

                fmt = AudioProcessor.detect_format(chunk_raw)
                if fmt == "webm" or len(webm_buffer) > 0:
                    webm_buffer.extend(chunk_raw)
                    chunk_webm_buffer.extend(chunk_raw)
                else:
                    raw_pcm_buffer.extend(chunk_raw)

                # Incremental transcription: process every ~2.5 seconds
                now = time.time()
                if now - last_transcribed_time >= 2.5 and not is_transcribing:
                    asyncio.create_task(transcribe_current_chunk())

            elif msg_type == "stop_recording":
                recording = False
                duration = time.time() - start_time if start_time else 0.0

                # Final pass on the complete recording
                final_text = latest_text
                try:
                    pcm_audio = None
                    if len(webm_buffer) > 1000:
                        pcm_audio = await asyncio.to_thread(
                            AudioProcessor.webm_to_pcm_float32, bytes(webm_buffer), settings.AUDIO_SAMPLE_RATE
                        )
                    elif len(raw_pcm_buffer) > 3200:
                        pcm_audio = AudioProcessor.pcm16_to_float32(bytes(raw_pcm_buffer))

                    if pcm_audio is not None and len(pcm_audio) > 1600:
                        result = await speech_svc.transcribe(pcm_audio, settings.AUDIO_SAMPLE_RATE)
                        text = result.get("text", "").strip()
                        if text:
                            final_text = text
                        lang = result.get("language")
                        if lang:
                            detected_lang = lang
                except Exception as e:
                    logger.error("Final transcription error: %s", e)

                word_count = len(final_text.split()) if final_text else 0

                # Save record to database
                saved_id = ""
                try:
                    db = get_session_local()()
                    t = svc.create_transcription(
                        db,
                        TranscriptionCreate(
                            title="Recording " + time.strftime("%Y-%m-%d %H:%M"),
                            transcription_text=final_text,
                            language_detected=detected_lang or None,
                            duration_seconds=round(duration, 1),
                        ),
                    )
                    saved_id = t.id
                    db.close()
                    logger.info("Saved transcription %s (%d words)", saved_id, word_count)
                except Exception as e:
                    logger.error("Failed to persist transcription to database: %s", e)

                await _send_json(ws, {
                    "type": "final_transcription",
                    "data": {
                        "id": saved_id,
                        "text": final_text,
                        "duration": round(duration, 1),
                        "language": detected_lang,
                        "word_count": word_count,
                    },
                })

            elif msg_type == "pause_recording":
                paused = True
                await _send_json(ws, {"type": "recording_paused", "data": {}})

            elif msg_type == "resume_recording":
                paused = False
                await _send_json(ws, {"type": "recording_resumed", "data": {}})

            elif msg_type == "ping":
                await _send_json(ws, {"type": "pong", "data": {}})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error("WebSocket unhandled exception: %s", e)
        await _send_json(ws, {"type": "error", "data": {"message": str(e)}})
