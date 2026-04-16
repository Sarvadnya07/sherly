## 2026-04-16 - Lazy load ML models
**Learning:** Initializing ML models like faster-whisper at module scope blocks the main thread on startup.
**Action:** Always lazy load expensive resources in performance-critical desktop apps.
