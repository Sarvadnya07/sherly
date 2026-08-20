# Sherly AI — Security Policy & Zero-Trust Architecture

## 1. Zero-Trust Security Philosophy

Sherly operates under an uncompromising zero-trust boundary:
- **Untrusted Inputs**: LLM generation, voice speech-to-text outputs, web scrape data, and frontend requests are treated as untrusted.
- **Server-Authoritative Policy Engine**: The risk classification (`SAFE`, `CONFIRM`, `DANGEROUS`, `BLOCKED`) is strictly computed on the backend server.
- **Defense in Depth**:
  1. *Command Sanitation*: Shell chaining (`&&`, `||`, `;`), subshells, and encoded PowerShell are blocked.
  2. *Path Traversal Protection*: Directory escaping (`../`) is strictly rejected.
  3. *Secret Redaction*: Keys matching `sk-...`, `Bearer ...`, and sensitive dictionary keys are masked before writing logs.
  4. *Immutable TTL Queue*: Pending actions expire after 120 seconds and can only be executed once.

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability in Sherly, please do not open a public issue. Email security reports directly to the maintainers or create a private GitHub Security Advisory.
