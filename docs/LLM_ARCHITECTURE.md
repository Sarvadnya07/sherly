# Sherly AI — Multi-Model & LLM Intelligence Architecture

**Specification Level:** Canonical Production Architecture (Phase 5)  
**Principle:** "One provider abstraction. Many models. One authoritative resolver. Strict policy & tool integration."  

---

## 1. Unified Multi-Model Provider Architecture

```
                          USER / API REQUEST
                                  │
                                  ▼
                         MODEL RESOLVER
            ┌─────────────────────┴─────────────────────┐
            │                                           │
         [AUTO]                                  [MANUAL / PINNED]
            │                                           │
    Capability Ranking                         User-Selected Model
            │                                           │
            └─────────────────────┬─────────────────────┘
                                  │
                                  ▼
                       PROVIDER ABSTRACTION
                                  │
      ┌──────────────┬────────────┴───────────┬──────────────┐
      │              │                        │              │
      ▼              ▼                        ▼              ▼
   OLLAMA         OPENAI                   GEMINI          GROQ
  (Local)     (GPT-4o-mini)            (1.5-Flash/Pro) (Llama-3/Qwen)
      │              │                        │              │
      └──────────────┼────────────────────────┴──────────────┘
                     │ (Circuit Breaker & Retries)
                     ▼
          STRUCTURED TOOL-CALLING & AGENT LOOP
                     │
                     ▼
              POLICY & APPROVAL GATE
                     │
                     ▼
             AUTHORIZED EXECUTION
```

---

## 2. Supported Providers & Adapters

1. **Ollama Provider (`OllamaProvider`)**:
   - Manages local models on `http://127.0.0.1:11434`.
   - Real-time model discovery and normalized metadata.
   - Circuit breaker (3 failures $\to$ open with 30s recovery).
   - Local VRAM idle unloader support.
2. **OpenAI Provider (`OpenAIProvider`)**:
   - Direct integration for `gpt-4o-mini` and `gpt-4o`.
   - Streaming, JSON structured outputs, tool calling.
3. **Google Gemini Provider (`GeminiProvider`)**:
   - Integration for `gemini-1.5-flash` and `gemini-1.5-pro`.
4. **Groq Provider (`GroqProvider`)**:
   - Ultra-fast cloud inference for `llama3-70b-8192`.

---

## 3. Reliability & Security Invariants

- **Circuit Breaker**: Each provider maintains a discrete `CircuitBreaker`. Transient failures trip the breaker, protecting the application without global lockouts.
- **Strict Manual Mode**: If the user explicitly pins a model, auto-detection will never override it.
- **Zero API Key Leakage**: Keys are stored securely in configuration/environment layers and never passed down to frontend telemetry.
- **Structured JSON Fallback**: For models lacking native function calling protocols, strict JSON prompting ensures predictable tool calls without regex prose execution.
