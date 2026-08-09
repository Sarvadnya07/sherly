# Performance Optimizations

Sherly is designed to run efficiently on consumer-grade hardware. To achieve real-time voice interaction and responsive AI generation locally, several performance optimizations have been implemented.

## 🎙️ Voice Processing (faster-whisper)

- **Quantization:** We utilize the CTranslate2 backend of `faster-whisper`, which applies INT8 quantization by default. This drastically reduces the memory footprint of the STT model while maintaining high accuracy.
- **VAD (Voice Activity Detection):** Sherly filters out background noise and silence *before* passing audio to the transcription model, saving CPU cycles.

## 🧠 LLM Resource Management

Running a 7B or 8B parameter model locally consumes significant VRAM. Sherly manages this tightly:

1. **Lazy Loading:** Models are not loaded into memory until the deterministic router explicitly requires LLM fallback.
2. **Auto-Unload:** If Sherly is idle for a configurable period (default: 5 minutes), the `model_manager` will unload the model from VRAM, freeing up resources for your IDE, browser, or Docker containers.
3. **Locking Mechanism:** A singleton lock ensures that only one model generation request is processed at a time, preventing Out-Of-Memory (OOM) crashes caused by concurrent requests.

## ⚡ Context Management (ChromaDB)

- **Vector Search over Grep:** Instead of shoving the entire codebase into the LLM prompt (which blows up the context window and drastically slows down inference), Sherly uses ChromaDB to perform semantic search. 
- Only the top `N` most relevant code snippets are injected into the context, keeping the prompt small and generation times lightning fast.

## 🖥️ UI Responsiveness (PySide6)

- **Asynchronous Execution:** All voice processing, LLM generation, and heavy filesystem operations are offloaded to background threads. The PySide6 main event loop is never blocked, ensuring the UI remains buttery smooth.
- **Debounced Inputs:** The system debounces rapidly triggered voice/hotkey inputs to prevent queue stacking.
