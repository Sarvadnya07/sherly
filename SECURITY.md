# Security Policy

At Sherly AI, the security and integrity of the developer's local environment is our highest priority. By design, Sherly operates locally and minimizes cloud exposure, but we take potential vulnerabilities seriously.

## 🛡️ Supported Versions

Only the latest release of Sherly is officially supported for security updates. 

| Version | Supported          |
| ------- | ------------------ |
| 1.15.x  | :white_check_mark: |
| 1.14.x  | :x:                |
| < 1.14  | :x:                |

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability within Sherly AI, please DO NOT open a public issue. 

Instead, report it privately to the core team:
- **Email:** security@sherly.ai *(Placeholder - update with real contact)*
- Please include:
  - A summary of the vulnerability
  - Steps to reproduce
  - Potential impact (e.g., bypasses safety layer, executes unauthorized shell command)

We aim to acknowledge receipt of the vulnerability within 48 hours and provide a timeline for a patch.

## 🏗️ Security Architecture Overview

Sherly is built with a defense-in-depth approach to prevent AI agents from running amok on your machine.

1. **Regex/Semantic Firewall:** Incoming prompts (voice or text) are scanned for known jailbreak patterns before reaching the LLM.
2. **Action Classification:** Every intent is scored. Operations that modify files or execute shell commands are escalated to `CONFIRM` (requiring user approval) or blocked entirely (`DANGEROUS`).
3. **Shell Protection:** Shell execution is done using `shell=False` and parsed via `shlex.split()` to prevent command injection.
4. **Secret Redaction:** Logs and agent contexts are scrubbed of API keys and common secret patterns before processing.
5. **Git-Style Previews:** All file modifications are staged as diffs for manual review prior to being written.
6. **Atomic Reversibility:** File states are backed up prior to any write, ensuring that AI-induced damage can be instantly undone (`undo` command).

## 🧑‍💻 Best Practices for Users

- **Run in a Sandbox:** For highest security, enable Docker-based sandboxing for Sherly's command execution.
- **Review Previews Carefully:** Always read the added/removed lines in the UI before typing `approve`.
- **Keep Models Local:** Rely on Ollama for local execution to prevent sensitive code from leaving your machine.
