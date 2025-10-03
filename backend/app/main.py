import os
import asyncio
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from livekit import api as lk_api

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
    return {"status": "ok"}

@app.post("/stop_session")
async def stop_session(req: StopSessionRequest):
    session_prompts.pop((req.room, req.identity), None)
    return {"status": "ok"}

# In-memory store for prompts
session_prompts: dict[tuple[str, str], str] = {}

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
                response_text = await run_pipeline(text, system_prompt)
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
async def run_pipeline(user_text: str, system_prompt: str) -> str:
    """
    Turn-taking is controlled at the backend: this function is called only after user speech end is detected.
    It performs STT (already text here), LLM generation, then TTS publication to LiveKit.
    For now, returns a placeholder response.
    """
    # LLM
    ai_text = await llm_generate(system_prompt, user_text)
    # TTS publish (server-side to LiveKit)
    await tts_publish_to_livekit(ai_text)
    return ai_text

async def llm_generate(system_prompt: str, user_text: str) -> str:
    # Placeholder LLM: echo with prompt context
    # Replace this with OpenAI/Claude free-tier call.
    return f"[Assistant ({system_prompt})]: I heard you say '{user_text}'. Here's a helpful response."

async def tts_publish_to_livekit(text: str):
    # TODO: Generate audio with TTS provider and publish into the LiveKit room via server SDK
    await asyncio.sleep(0.01)