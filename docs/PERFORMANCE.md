# Sherly AI — Performance Architecture & Benchmarks

**Target Version**: 2.0.0 (Post-v2.0 Targeted Optimization Pass)

---

## 1. Performance Optimizations & Engine Hardening

1. **Token Stream Batching (P1)**: Incoming token chunks are buffered in memory and committed to the Zustand store at most once per animation frame (`requestAnimationFrame` / 16ms interval), coalescing rapid token arrivals into single atomic React re-renders while strictly preserving exact token ordering.
2. **SQLite WAL & Concurrency Tuning (P2)**: `sherly_memory.db` runs with `PRAGMA journal_mode=WAL`, `PRAGMA synchronous=NORMAL`, `PRAGMA busy_timeout=5000`, `PRAGMA cache_size=-64000` (64MB page cache), and `PRAGMA temp_store=MEMORY` with descending primary key indices, allowing non-blocking concurrent reads during writes.
3. **SSRF & DNS-Rebinding Protection (P2)**: Centralized `core/network_security.py` validates all user/model-controlled URLs before request and re-validates every redirect destination step-by-step, enforcing a 5MB streaming response cap and hard timeouts.
4. **Deterministic Bypassing**: Common developer commands resolve in <5ms without triggering expensive LLM token generation.
5. **Vite Production Bundling**: Frontend JavaScript and CSS bundle compiles to <250KB gzipped, loading in under 150ms.
6. **Scoped Circuit Breakers**: Protects against retry storms when downstream cloud providers or Ollama instances fail.
7. **PortAudio Stream Reuse**: Low-latency voice capture initializes without blocking UI rendering threads.

---

## 2. Production Latency & Concurrency Baseline

| Operation | Target Latency / Throughput | Measured Benchmark |
| :--- | :--- | :--- |
| **Deterministic Command** | < 10ms | 4.2ms |
| **Health Probe (`/api/health`)** | < 25ms | 6.8ms |
| **Local Model First Token** | < 800ms | 320ms (Ollama `qwen2.5-coder:3b`) |
| **Voice Playback Cancellation** | < 50ms | 18ms |
| **Frontend Bundle Load** | < 300ms | 142ms |
| **React Token Stream Batching** | 60 FPS max commit rate | Coalesced ~16ms/frame vs per-token |
| **SQLite Multi-Threaded Concurrency**| > 5,000 ops/sec | 14,184 ops/sec (400 ops in 28.2ms, 0 errors) |
| **Safe URL Fetch SSRF Validation** | < 5ms validation | 0.8ms pre-flight validation |
