# Operational reliability

- The LLM cascade uses Ollama, Groq and Together **only when configured**.
- Provider failures are cooled down in memory with bounded exponential backoff (30–900s default).
- A fallback marked `provider=offline` and `fallback=true` is a placeholder, not a real generated hypothesis.
- Local Ollama origin is restricted to HTTP loopback, without URL credentials, query or non-root path.
- The loop persists state by write/fsync/atomic replace in the same directory, validates the state schema, and rejects nonpositive cycles.
- Persistence is single-process only; concurrent writers need a lock or DB transaction.
- Network availability, provider credentials, quotas, actual monthly cost, and real code-generation quality are **not verified** by mocked unit tests.
- No claim is made of strong process sandboxing, autonomous development or AGI capability.
