import asyncio
from lib.agents.free_llm_agent import FreeLLMAgent


def test_offline_fallback_is_deterministic():
    agent = FreeLLMAgent()
    r1 = asyncio.run(agent.generate_response("Hypothese erstellen"))
    r2 = asyncio.run(agent.generate_response("Hypothese erstellen"))
    assert r1 == r2 and r1.startswith("OFFLINE-HYPOTHESE")


def test_no_keys_means_offline(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    agent = FreeLLMAgent()
    out = asyncio.run(agent.process({"prompt": "Test"}))
    assert out["provider"] == "offline" and out["response"]


def test_available_providers(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "x")
    agent = FreeLLMAgent()
    assert agent.available_providers() == ["groq"]
