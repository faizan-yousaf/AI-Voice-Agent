import os
import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from livekit import api as lk_api
from elevenlabs import ElevenLabs
from livekit import rtc

load_dotenv()

app = FastAPI(title="Voice AI Conversational Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
LIVEKIT_URL = os.getenv("LIVEKIT_URL")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are a friendly travel assistant.")

# LiveKit AccessToken issuance
# The frontend expects GET /token?identity=<>&room=<>
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi import Request

@app.get("/token")
async def get_token(identity: str, room: str):
    if not (LIVEKIT_API_KEY and LIVEKIT_API_SECRET and LIVEKIT_URL):
        raise HTTPException(status_code=500, detail="LiveKit configuration missing")
    at = lk_api.AccessToken(identity=identity)
    at.add_grants(lk_api.VideoGrants(room_join=True, room=room))
    token = at.to_jwt(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
    return JSONResponse({"token": token, "url": LIVEKIT_URL})

# Session lifecycle models
class StartSessionRequest(BaseModel):
    system_prompt: Optional[str] = None
    room: str
    identity: str

class StopSessionRequest(BaseModel):
    room: str
    identity: str

@app.post("/start_session")
async def start_session(req: StartSessionRequest):
    # Persist the session system prompt; for demo, store in-memory per room/identity
    # In production, use a DB or cache store.
    session_prompts[(req.room, req.identity)] = req.system_prompt or SYSTEM_PROMPT
    # Initialize server-side participant connection and audio publisher registry
    key = (req.room, req.identity)
    if key not in _publishers:
        _publishers[key] = {}
    return {"status": "ok"}

@app.post("/stop_session")
async def stop_session(req: StopSessionRequest):
    session_prompts.pop((req.room, req.identity), None)
    # Cleanup publisher if exists
    _publishers.pop((req.room, req.identity), None)
    return {"status": "ok"}

# In-memory store for prompts
session_prompts: dict[tuple[str, str], str] = {}
# In-memory registry of server publishers per (room, identity)
_publishers: dict[tuple[str, str], dict] = {}

# WS /stream: bi-directional audio streaming coordination
# NOTE: Real audio streaming with LiveKit usually uses SFU connections directly.
# Here WS is used to exchange control messages (transcripts, thinking state) between frontend and backend.
@app.websocket("/stream")
async def stream_ws(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            # Expected messages: { type: "user_transcript", text: "...", room: "...", identity: "..." }
            msg_type = data.get("type")
            if msg_type == "user_transcript":
                text = data.get("text", "")
                room = data.get("room")
                identity = data.get("identity")
                system_prompt = session_prompts.get((room, identity), SYSTEM_PROMPT)
                # Notify frontend that AI is thinking
                await ws.send_json({"type": "thinking", "thinking": True})
                # Run pipeline
                response_text = await run_pipeline(text, system_prompt, room, identity)
                await ws.send_json({"type": "thinking", "thinking": False})
                # Send agent transcript message
                await ws.send_json({"type": "transcript", "speaker": "agent", "text": response_text})
                # TODO: Publish TTS audio to LiveKit room via server-side participant
            else:
                # Unknown control message
                pass
    except WebSocketDisconnect:
        pass

# --- Pipeline implementation stubs ---
async def run_pipeline(user_text: str, system_prompt: str, room: str, identity: str) -> str:
    """
    Turn-taking is controlled at the backend: this function is called only after user speech end is detected.
    It performs STT (already text here), LLM generation, then TTS publication to LiveKit.
    For now, returns a placeholder response.
    """
    # LLM
    ai_text = await llm_generate(system_prompt, user_text)
    # TTS publish (server-side to LiveKit)
    await tts_publish_to_livekit(ai_text, room=room, identity=identity)
    return ai_text

async def llm_generate(system_prompt: str, user_text: str) -> str:
    # Placeholder LLM: echo with prompt context
    # Replace this with OpenAI/Claude free-tier call.
    return f"[Assistant ({system_prompt})]: I heard you say '{user_text}'. Here's a helpful response."

async def tts_publish_to_livekit(text: str, room: str, identity: str):
    # Generate audio with ElevenLabs and publish into the LiveKit room via server SDK
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "")

    if not api_key:
        await asyncio.sleep(0.01)
        return

    client = ElevenLabs(api_key=api_key)

    # Connect server-side participant to LiveKit if not already connected for this (room, identity)
    key = (room, identity)
    publisher = _publishers.get(key)
    if not publisher:
        publisher = {}
        _publishers[key] = publisher
    if "room" not in publisher:
        lk_token = lk_api.AccessToken(identity=identity)
        lk_token.add_grants(lk_api.VideoGrants(room_join=True, room=room))
        jwt = lk_token.to_jwt(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        publisher_room = rtc.Room()
        await publisher_room.connect(LIVEKIT_URL, jwt)
        publisher["room"] = publisher_room
        # Create audio source and publish track
        source = rtc.AudioSource(48000, 1)
        track = rtc.LocalAudioTrack.create_audio_track("agent-tts", source)
        opts = rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        await publisher_room.local_participant.publish_track(track, opts)
        publisher["source"] = source

    source: rtc.AudioSource = publisher["source"]

    # Stream PCM S16LE at 24kHz; upsample to 48k for LiveKit
    stream = client.text_to_speech.convert_stream(
        text=text,
        voice_id=voice_id or None,
        model_id=os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
        output_format="pcm_24000",
        optimize_streaming_latency=3,
    )

    try:
        # Use standard library for upsampling to avoid extra dependencies
        from array import array
        async for chunk in stream:
            if not chunk:
                continue
            samples_24k = array('h')
            samples_24k.frombytes(chunk)
            samples_48k = array('h')
            # simple 2x upsampling by sample duplication
            for s in samples_24k:
                samples_48k.append(s)
                samples_48k.append(s)
            frame_size = 480
            byte_data = samples_48k.tobytes()
            # iterate in frames of 480 samples (10ms at 48kHz)
            bytes_per_sample = 2
            frame_bytes = frame_size * bytes_per_sample
            for i in range(0, len(byte_data), frame_bytes):
                frame_chunk = byte_data[i:i+frame_bytes]
                if len(frame_chunk) < frame_bytes:
                    break
                frame = rtc.AudioFrame(
                    data=frame_chunk,
                    sample_rate=48000,
                    num_channels=1,
                    samples_per_channel=frame_size,
                )
                await source.capture_frame(frame)
    except Exception:
        # fallback no-op
        await asyncio.sleep(0.01)