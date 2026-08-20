# Sherly Security Hardening Guide (Phase 13)

**Target Audience**: Developers, Sysadmins, and Security Auditors  
**Status**: PRODUCTION-HARDENED  

---

## 1. Local Environment Hygiene

1. **Environment Configuration**:
   - Store API keys in `.env` or local `config.json` (both excluded in `.gitignore`).
   - Never check live API keys into version control.
   - Use `.env.example` and `config.json.example` as configuration templates.
2. **File Permissions**:
   - Ensure `config.json` and `sherly_memory.db` are set to `600` (read/write only by owner) in multi-user POSIX environments.

---

## 2. Remote Access Configuration

When deploying Sherly in remote server mode:
1. Configure reverse proxy (e.g. Nginx, Caddy) with TLS / HTTPS certificates.
2. Provide a strong `SHERLY_API_KEY` environment variable.
3. Configure firewall to restrict API port access to authorized CIDR blocks or VPN tunnels.
