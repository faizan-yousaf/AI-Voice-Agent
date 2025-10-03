import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'
import {
  Room,
  RoomEvent,
  RemoteParticipant,
  RemoteTrackPublication,
  RemoteAudioTrack,
  Track,
} from 'livekit-client'

interface TranscriptMsg {
  speaker: 'user' | 'agent'
  text: string
}

function App() {
  const backendUrl = useMemo(() => import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000', [])
  const [roomName, setRoomName] = useState('voice-room')
  const [identity, setIdentity] = useState('web-user')
  const [connected, setConnected] = useState(false)
  const [thinking, setThinking] = useState(false)
  const [transcripts, setTranscripts] = useState<TranscriptMsg[]>([])
  const [inputText, setInputText] = useState('')

  const livekitRoomRef = useRef<Room | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      wsRef.current?.close()
      livekitRoomRef.current?.disconnect()
    }
  }, [])

  async function connectLiveKit() {
    try {
      const res = await fetch(`${backendUrl}/token?identity=${encodeURIComponent(identity)}&room=${encodeURIComponent(roomName)}`)
      const data = await res.json()
      const { token, url } = data as { token: string; url: string }

      const room = new Room()
      room.on(RoomEvent.TrackSubscribed, (track, publication: RemoteTrackPublication, participant: RemoteParticipant) => {
        if (track.kind === Track.Kind.Audio) {
          const audioTrack = track as RemoteAudioTrack
          const el = audioTrack.attach()
          el.autoplay = true
          el.hidden = true
          document.body.appendChild(el)
        }
      })
      await room.connect(url, token)
      livekitRoomRef.current = room
      setConnected(true)
    } catch (e) {
      console.error('Failed to connect LiveKit:', e)
      alert('Failed to connect LiveKit. Check backend and env settings.')
    }
  }

  async function disconnectLiveKit() {
    try {
      livekitRoomRef.current?.disconnect()
      livekitRoomRef.current = null
      setConnected(false)
    } catch {}
  }

  async function startSession() {
    try {
      await fetch(`${backendUrl}/start_session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room: roomName, identity })
      })
      // open WS
      const ws = new WebSocket(`${backendUrl.replace('http', 'ws')}/stream`)
      ws.onopen = () => {
        wsRef.current = ws
      }
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data)
          if (msg.type === 'thinking') {
            setThinking(!!msg.thinking)
          } else if (msg.type === 'transcript') {
            setTranscripts((prev) => [...prev, { speaker: msg.speaker, text: msg.text }])
          }
        } catch (err) {
          console.warn('WS parse error', err)
        }
      }
      ws.onclose = () => {
        wsRef.current = null
      }
    } catch (e) {
      console.error('start_session failed:', e)
      alert('Failed to start session')
    }
  }

  async function stopSession() {
    try {
      await fetch(`${backendUrl}/stop_session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room: roomName, identity })
      })
    } catch {}
    wsRef.current?.close()
    wsRef.current = null
    setThinking(false)
  }

  function sendUserText() {
    const text = inputText.trim()
    if (!text) return
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      alert('Session not started or WS not open')
      return
    }
    // Add user transcript locally
    setTranscripts((prev) => [...prev, { speaker: 'user', text }])
    wsRef.current.send(JSON.stringify({ type: 'user_transcript', text, room: roomName, identity }))
    setInputText('')
  }

  return (
    <div className="container">
      <h1>Voice Agent</h1>

      <div className="row">
        <label>
          Room
          <input value={roomName} onChange={(e) => setRoomName(e.target.value)} />
        </label>
        <label>
          Identity
          <input value={identity} onChange={(e) => setIdentity(e.target.value)} />
        </label>
      </div>

      <div className="row">
        <button onClick={connectLiveKit} disabled={connected}>Connect</button>
        <button onClick={disconnectLiveKit} disabled={!connected}>Disconnect</button>
        <button onClick={startSession}>Start Session</button>
        <button onClick={stopSession}>Stop Session</button>
      </div>

      <div className="row">
        <input
          placeholder="Type something to say..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') sendUserText()
          }}
          style={{ flex: 1 }}
        />
        <button onClick={sendUserText}>Send</button>
      </div>

      <div className="status">
        <span>Connected: {connected ? 'Yes' : 'No'}</span>
        <span>Thinking: {thinking ? 'Yes...' : 'No'}</span>
      </div>

      <div className="transcripts">
        {transcripts.map((t, idx) => (
          <div key={idx} className={t.speaker === 'user' ? 'bubble user' : 'bubble agent'}>
            <strong>{t.speaker === 'user' ? 'You' : 'Agent'}:</strong> {t.text}
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
