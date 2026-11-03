import asyncio
import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent-loop"))
from agent_loop import AgentLoopEngine
from lib.agents.free_llm_agent import FreeLLMAgent


def test_provider_failure_falls_back_and_cools_down(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "fake")
    agent = FreeLLMAgent(cooldown_seconds=60)
    calls = []
    def fail(provider, prompt):
        calls.append(provider)
        raise OSError("rate limited")
    monkeypatch.setattr(agent, "_request", fail)
    first = asyncio.run(agent.process({"prompt": "test"}))
    second = asyncio.run(agent.process({"prompt": "test"}))
    assert first["provider"] == second["provider"] == "offline"
    assert len(calls) == 1
    assert first["fallback"] is True
    assert agent.available_providers() == []


def test_provider_failover_to_second_configured(monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "fake")
    monkeypatch.setenv("TOGETHER_API_KEY", "fake")
    agent = FreeLLMAgent()
    def invoke(provider, prompt):
        if provider == "groq":
            raise OSError("429")
        return "real response"
    monkeypatch.setattr(agent, "_request", invoke)
    result = asyncio.run(agent.process({"prompt": "x"}))
    assert result["provider"] == "together" and not result["fallback"]


@pytest.mark.parametrize("url", [
    "https://localhost:11434", "http://localhost.evil:11434",
    "http://localhost:11434@evil.example", "http://localhost:11434/api",
    "http://127.0.0.1:11434/?token=x"
])
def test_ollama_rejects_untrusted_origin(monkeypatch, url):
    monkeypatch.setenv("OLLAMA_BASE_URL", url)
    with pytest.raises(ValueError):
        FreeLLMAgent._ollama_url()


def test_ollama_accepts_local_origin(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    assert FreeLLMAgent._ollama_url().endswith("/api/generate")


def test_state_is_saved_and_has_provenance(tmp_path, monkeypatch):
    for name in ("OLLAMA_BASE_URL", "GROQ_API_KEY", "TOGETHER_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    path = tmp_path / "state.json"
    engine = AgentLoopEngine(state_file=str(path))
    out = asyncio.run(engine.run_cycle())
    data = json.loads(path.read_text())
    assert out["offline_fallback"] is True
    assert data["history"][-1]["provider"] == "offline"
    assert not list(tmp_path.glob(".agi-state-*.json"))


def test_invalid_state_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"cycle":0,"history":"wrong"}')
    with pytest.raises(ValueError):
        AgentLoopEngine(state_file=str(path))


def test_invalid_cycles_rejected(tmp_path):
    engine = AgentLoopEngine(state_file=str(tmp_path / "state.json"))
    with pytest.raises(ValueError):
        asyncio.run(engine.run(0))
