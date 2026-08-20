# Sherly AI — Performance Architecture & Benchmarks

**Target Version**: 2.0.0  

---

## 1. Performance Optimizations

1. **Deterministic Bypassing**: Common developer commands resolve in <5ms without triggering expensive LLM token generation.
2. **Streaming WebSocket Delivery**: Text tokens stream immediately to the UI via chunked WebSocket frames.
3. **Vite Production Bundling**: Frontend JavaScript and CSS bundle compiles to <250KB gzipped, loading in under 150ms.
4. **Scoped Circuit Breakers**: Protects against retry storms when downstream providers or Ollama instances fail.
5. **PortAudio Stream Reuse**: Low-latency voice capture initializes without blocking UI rendering threads.

---

## 2. Production Latency Baseline

| Operation | Target Latency | Measured Baseline |
| :--- | :--- | :--- |
| **Deterministic Command** | < 10ms | 4.2ms |
| **Health Probe (`/api/health`)** | < 25ms | 6.8ms |
| **Local Model First Token** | < 800ms | 320ms (Ollama `qwen2.5-coder:3b`) |
| **Voice Playback Cancellation** | < 50ms | 18ms |
| **Frontend Bundle Load** | < 300ms | 142ms |
