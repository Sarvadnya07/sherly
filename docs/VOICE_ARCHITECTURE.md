# Sherly Voice Architecture & Realtime Experience (Phase 10)

**Target Surface**: `frontend/src/views/VoiceOverlayView.tsx` & Python Audio Layer  
**Classification**: Real-Time Low-Latency Voice Interface  
**Status**: ACTIVE & PRODUCTION-READY  

---

## 1. Architectural Principles

1. **Voice as an Input/Output Modality**: Voice converges directly onto the exact same canonical Assistant chat and capability pipeline as typed text. No second or shadow AI system is created for voice.
2. **Authority Split**:
   - **Python Backend**: Owns hardware microphone capture via `sounddevice`, transcription via `faster-whisper`, speech synthesis via `pyttsx3`, and device querying.
   - **React/Tauri Client**: Owns the Voice HUD, live transcript rendering, state pill presentation, and interactive controls.
3. **Canonical Voice State Machine**:
   - States: `IDLE`, `LISTENING`, `TRANSCRIBING`, `THINKING`, `TOOL_RUNNING`, `WAITING_FOR_APPROVAL`, `SPEAKING`, `STOPPING`, `STOPPED`, `CANCELLED`, `ERROR`.
   - Transitions are deterministic with monotonic timestamp ordering guards to prevent delayed events from overwriting newer states.
4. **Deterministic Cancellation & Cleanup**:
   - Programmatic cancellation (`stop_tts()`, `/api/voice/stop_speaking`, `Esc`) immediately terminates active audio playback and closes streams cleanly in `finally` blocks.
   - Zero leaked audio buffers or orphaned background worker threads.
5. **Safety Invariant**:
   - Voice commands that trigger sensitive tools (file deletion, terminal commands) strictly require explicit UI approval (`Enter` / Approve button). Spoken confirmation alone does not bypass security gates.

---

## 2. Voice Flow Sequence

```text
🎙 Microphone (sounddevice)
       ↓
STT Model (faster-whisper)
       ↓
Filtered Text (silence & noise floor checked)
       ↓
Canonical Assistant (POST /api/chat & sendChatMessage)
       ↓
Model Resolver & LLM (qwen2.5-coder:3b / auto)
       ↓
ToolRegistry / Policy / ActionManager (if tool required)
       ↓
Assistant Synthesis
       ↓
TTS Engine (pyttsx3)
       ↓
🔊 Speaker Playback
```

---

## 3. Keyboard Shortcuts

- `Ctrl + Shift + L`: Activate voice listening HUD
- `Enter`: Stop recording and submit transcription (when in listening mode)
- `Esc`: Stop speaking / Cancel active voice session
