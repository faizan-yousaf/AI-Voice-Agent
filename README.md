# Web-based Voice AI Conversational Agent

This repository contains the implementation of a **real-time Voice AI Conversational Agent**, developed as per the PRD. It uses **React** for the frontend, **FastAPI** for the backend, and **LiveKit SDKs** to enable low-latency audio streaming, turn-taking, and natural back-and-forth voice conversations.

## 🚀 Tech Stack
- **Frontend**: React + Vite, LiveKit Web SDK  
- **Backend**: FastAPI, LiveKit Server SDK  
- **AI Services**:  
  - STT: Whisper API, Retell, or equivalent  
  - LLM: GPT, Claude, or equivalent  
  - TTS: OpenAI TTS, ElevenLabs, or equivalent  

## 📂 Monorepo Structure
```
frontend/   # React app
backend/    # FastAPI app
```

> ⚠️ Note: The current React project is located under `src/`. For PRD consistency, treat it as the `frontend/` directory.

---

## ⚙️ Backend Setup
1. Create and configure the environment file:
```bash
cp backend/.env.example backend/.env
```
Fill in the following keys:
- `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `LIVEKIT_URL`  
- `SYSTEM_PROMPT`  
- `OPENAI_API_KEY` (or alternative STT/TTS provider key)  

2. Install dependencies and start the backend:
```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### API Endpoints
- `GET /token?identity=<id>&room=<room>` → Returns `{ token, url }` for LiveKit join  
- `POST /start_session` → Initialize session with system prompt  
- `POST /stop_session` → End session  
- `WS /stream` → WebSocket control channel for transcripts & turn-taking (audio handled via LiveKit)  

---

## 💻 Frontend Setup
1. Create a `.env` file in the frontend root with:
```
VITE_BACKEND_URL=http://localhost:8000
```

2. Install dependencies and run:
```bash
npm install
npm run dev
```
Open the app at [http://localhost:8080](http://localhost:8080).

---

## 🔄 Turn-taking Logic
- **Frontend** detects when the user stops speaking using LiveKit voice activity.  
- **Transcripts** are sent to the backend over WebSocket.  
- **Backend** executes the pipeline: `STT → LLM → TTS` only after the user turn ends.  
- **AI Response** is synthesized and published as audio into the LiveKit room.  
- **Frontend** plays the remote audio stream for natural interaction.  

---

## 📝 Notes
- Replace placeholder LLM and TTS with any free-tier provider.  
- Ensure your LiveKit project is correctly configured.  
- For the demo (e.g., Loom recording), showcase:  
  - Start/stop conversation  
  - Transcript display (user + AI)  
  - Real-time voice conversation in action  
