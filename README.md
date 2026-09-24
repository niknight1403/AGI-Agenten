# AGI-Agenten

Modularer Multi-Agenten-Loop ("Plan -> Execute -> Evaluate -> Optimize") mit Fokus auf
kostenlose LLMs, API-Key-Rotation und MCP-Stil-Connectoren.

## Architektur

- `agent-loop/agent_loop.py` – Loop-Engine mit persistiertem Zustand (`state_memory.json`) und CLI
- `lib/agents/base.py` – `BaseAgent`-Schnittstelle (async `process()`)
- `lib/agents/orchestrator.py` – Registry und Task-Routing
- `lib/agents/free_llm_agent.py` – Provider-Kette (Ollama/Groq/Together) mit deterministischem Offline-Fallback
- `lib/agents/api_rotator_agent.py` – Round-Robin-Key-Rotation mit Cooldown
- `lib/agents/code_execution_agent.py` – subprocess-Sandbox mit Timeout + Modul-Denylist
- `lib/agents/evaluation.py` – heuristische Ergebnisbewertung (Score 0-1)
- `lib/agents/self_optimization_agent.py` – regelbasierte Prompt-Strategie je Score-Trend
- `lib/agents/mcp_connector_agent.py` – Tool-Connectoren aus JSON-Konfiguration
- `lib/agents/skill_agent.py` – gespeicherte, sicher geprüfte Code-Skills
- `lib/design/future_glass.py` – Design-Tokens, `lib/utils/metrics.py` – AGI-Metriken

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r agent-loop/requirements.txt
pytest tests/ -q          # Testsuite
```

## Nutzung

```bash
cd agent-loop
python3 agent_loop.py --cycles 3
```

Ohne API-Keys läuft die Engine im Offline-Fallback deterministisch durch.
Optionale Provider per Umgebungsvariable:

- `OLLAMA_BASE_URL=http://localhost:11434`
- `GROQ_API_KEY=...`
- `TOGETHER_API_KEY=...`

## Tests

`tests/` enthaelt 10 Sprint-Testmodule (41 Tests), inkl. End-to-End-Zyklustest.
