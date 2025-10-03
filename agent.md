# Product Requirements Document (PRD)  
**Project:** Web-based Voice AI Conversational Agent  
**Tech Stack:** FastAPI (Python), React, LiveKit (Web + Server SDKs)  

---

## 1. Overview  

The goal is to build a **web-based Voice AI Conversational Agent** that enables **real-time, natural voice conversations with an AI model**. The system should use **LiveKit** for real-time audio streaming, a **FastAPI backend** for orchestration, and a **React frontend** for the user interface.  

This agent will:  
- Begin with one **system prompt** (e.g., *“You are a friendly travel assistant”*).  
- Enable **real-time turn-taking** in conversations (no overlapping speech).  
- Use **STT → LLM → TTS pipeline** for seamless back-and-forth communication.  
- Provide a simple UI with conversation start/stop, transcript, and audio playback.  

---

## 2. Goals & Non-Goals  

### Goals  
- Deliver a minimal yet functional **voice-first AI agent**.  
- Real-time **voice streaming** with turn-taking logic.  
- Frontend and backend integration using **LiveKit**.  
- Support **one-time system prompt initialization**.  
- Leverage **free-tier AI services** (STT, LLM, TTS).  
- Completion in **72 hours**, aided by AI development tools (Cursor AI, Lovable, etc.).  

### Non-Goals  
- Rich UI/UX design (focus only on functional UI).  
- Support for multi-language or advanced NLP features.  
- Handling of multiple concurrent users beyond a single-session demo.  

---

## 3. System Architecture  

### 3.1 High-Level Flow  

1. **User speaks → Audio captured in browser (React + LiveKit Web SDK).**  
2. **Audio streamed to backend (FastAPI + LiveKit Server SDK).**  
3. **Pipeline:**  
   - STT transcribes audio → text  
   - Text sent to LLM → response generated  
   - Response converted to audio using TTS  
4. **Backend streams TTS audio back to frontend via LiveKit.**  
5. **Frontend plays AI’s audio response and displays transcripts.**  
6. **Turn-taking logic ensures natural back-and-forth flow.**  

---

## 4. Detailed Requirements  

### 4.1 Initialization & System Prompt  
- At session start: initialize one **system prompt** (configurable, e.g., *“You are a friendly travel assistant.”*).  
- This prompt must be stored and applied for the **entire session**.  
- After initialization → **voice-only conversation** (no typing input).  

### 4.2 Voice AI Pipeline  
- **STT (Speech-to-Text):**  
  - Options: Whisper API, Retell, or another free STT service.  
  - Output must be transcribed text of the user’s audio.  

- **LLM (Text Processing):**  
  - Options: GPT (OpenAI free tier), Claude, or equivalent.  
  - Takes STT text + system prompt context → generates AI response.  

- **TTS (Text-to-Speech):**  
  - Options: OpenAI TTS, ElevenLabs free tier, or any free API.  
  - Converts AI response into natural-sounding speech.  

- **Turn-Taking Logic:**  
  - Detect end of user speech (pause detection).  
  - Only then → trigger AI pipeline.  
  - Prevent overlapping speech (AI should wait until user finishes).  

### 4.3 Backend (FastAPI)  
- Must use **FastAPI** for API endpoints and pipeline orchestration.  
- Responsibilities:  
  - Manage session lifecycle (start/stop).  
  - Coordinate STT → LLM → TTS pipeline.  
  - Securely load environment variables/API keys (.env file).  
  - Expose REST/WebSocket endpoints for frontend:  
    - `POST /start_session` (initialize system prompt + LiveKit session).  
    - `POST /stop_session` (end session).  
    - `WS /stream` (bi-directional audio streaming with LiveKit).  
  - Handle turn-taking logic at backend to prevent overlap.  

### 4.4 Frontend (React)  
- Must use **React** with **LiveKit Web SDK**.  
- Features:  
  - **Start/Stop conversation button**.  
  - **Transcript display** (user + AI turns).  
  - **Live audio playback** of AI responses streamed from backend.  
- Minimal UI, no advanced styling required.  

---

## 5. Implementation Guidelines  

### 5.1 Tech Stack  
- **Frontend:** React, LiveKit Web SDK.  
- **Backend:** FastAPI, LiveKit Server SDK.  
- **STT:** Whisper API, Retell, or equivalent (free).  
- **LLM:** GPT / Claude (free tier).  
- **TTS:** OpenAI TTS / ElevenLabs free tier.  

### 5.2 Code Quality  
- Modular, clean, and documented.  
- Separate files for services (STT, LLM, TTS).  
- Secure API key handling (`.env`).  
- Add inline comments where necessary.  

### 5.3 UI Guidelines  
- Keep minimal, focused on core experience:  
  - Buttons for Start/Stop.  
  - Transcript panel (scrollable).  
  - Live audio output.  

---

## 6. Deliverables  

1. **Working Application** with real-time voice conversation.  
2. **Source Code Repository**:  
   - `frontend/` (React + LiveKit Web SDK).  
   - `backend/` (FastAPI + LiveKit Server SDK).  
   - `.env.example` file with placeholders for API keys.  
   - `README.md` with setup + run instructions.  

3. **Demo Video (Loom):**  
   - Walkthrough of solution architecture.  
   - Live demo of conversation with AI.  
   - Highlight of turn-taking logic.  
   - Explanation of how AI coding tools were used.  

---

## 7. Timeline  

- **Day 1 (0–24h):**  
  - Setup project skeleton (frontend + backend).  
  - Integrate LiveKit SDKs.  
- **Day 2 (24–48h):**  
  - Implement STT → LLM → TTS pipeline.  
  - Add turn-taking logic.  
- **Day 3 (48–72h):**  
  - Finalize React UI.  
  - End-to-end testing.  
  - Record Loom demo video.  

---

## 8. Acceptance Criteria  

✅ Must use **LiveKit** (mandatory).  
✅ Must support **one system prompt** at initialization.  
✅ Must enable **real-time back-and-forth voice conversation**.  
✅ Must include **turn-taking algorithm** (no overlapping).  
✅ Must use **free-tier AI services** (STT, LLM, TTS).  
✅ Must include **working demo video**.  
✅ Must have **clean, modular code with documentation**.  
