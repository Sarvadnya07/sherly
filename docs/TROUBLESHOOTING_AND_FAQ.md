# Sherly AI — Troubleshooting, Diagnostics & FAQ

**Target System**: Desktop HUD, Voice Hardware, Local Inference, WebSocket Connectivity  
**Version**: 2.0.0  

---

## 1. Fast Diagnostic Matrix

```text
┌──────────────────────────────────────┬───────────────────────────────┬────────────────────────────────────────────────────────┐
│ Symptom / Error Message              │ Probable Cause                │ Recommended Remediation                                │
├──────────────────────────────────────┼───────────────────────────────┼────────────────────────────────────────────────────────┤
│ "Ollama Not Running"                 │ Ollama daemon stopped         │ Run `ollama serve` in a background terminal.           │
│ "PVPORCUPINE_ACCESS_KEY Unset"       │ Missing wake-word key         │ Add key to `.env` or use `Ctrl + Shift + L` hotkey.    │
│ "Microphone Initialization Failed"   │ OS privacy permissions blocked│ Enable Desktop App Microphone access in Windows/macOS. │
│ "Action Ticket Expired (120s TTL)"   │ Human approval timeout        │ Re-run command to generate a fresh approval ID.        │
│ "File Modified Externally Conflict"  │ SHA256 base hash mismatch     │ Refresh diff preview to re-base against new file state.│
│ "SSRF Target Blocked: 169.254.169..."│ Cloud metadata query attempt  │ Expected security behavior (Network firewall active).  │
│ "WebSocket Disconnected 1006"        │ Backend server restarted      │ Client auto-reconnects with exponential backoff.       │
└──────────────────────────────────────┴───────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 2. Audio & Microphone Hardware Debugging

If voice input is not registering:

1. **Query Available Audio Input Devices**:
   ```python
   import sounddevice as sd
   print(sd.query_devices())
   ```
2. **Verify Default OS Microphone**:
   - On Windows: *Settings > System > Sound > Input*. Ensure the correct microphone is set as the default device.
   - On macOS: *System Settings > Privacy & Security > Microphone*. Verify terminal/app permissions.

---

## 3. Ollama VRAM & GPU Diagnostics

1. **Verify Ollama Model List & Connectivity**:
   ```bash
   curl http://127.0.0.1:11434/api/tags
   ```
2. **Check GPU VRAM Allocation**:
   - On NVIDIA GPUs: Run `nvidia-smi` to inspect active VRAM usage.
   - If VRAM is constrained: Pull lighter quantized models (`qwen2.5-coder:1.5b` or `deepseek-coder:1.3b`).
   - The built-in Idle VRAM Unloader automatically releases GPU memory after 120s of inactivity.

---

## 4. SQLite Memory Optimization & Reset

Sherly stores persistent conversation turns and actions in `sherly_memory.db` with WAL mode enabled.

To inspect or vacuum the database:
```bash
sqlite3 sherly_memory.db "PRAGMA journal_mode; PRAGMA integrity_check;"
```

To perform a clean state reset:
```bash
# Safe reset: delete local memory and let Sherly recreate clean schema on startup
rm sherly_memory.db
```
