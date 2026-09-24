import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent-loop"))
from agent_loop import AgentLoopEngine
from lib.utils.metrics import calculate_agi_metrics


def test_full_cycle_end_to_end(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    state_file = str(tmp_path / "state.json")
    engine = AgentLoopEngine(state_file=state_file)
    out = asyncio.run(engine.run_cycle())
    assert out["cycle"] == 1
    assert out["hypothesis"].startswith("OFFLINE-HYPOTHESE")
    assert out["design_tokens"]["accent_color"] == "#00e5ff"
    assert out["evaluation"]["score"] > 0
    assert out["optimization"]["strategy"] in {"diversify", "refine", "keep"}
    saved = json.loads(open(state_file, encoding="utf-8").read())
    assert saved["cycle"] == 2 and len(saved["history"]) == 1


def test_multiple_cycles_improve_state(tmp_path, monkeypatch):
    for var in ("GROQ_API_KEY", "TOGETHER_API_KEY", "OLLAMA_BASE_URL"):
        monkeypatch.delenv(var, raising=False)
    state_file = str(tmp_path / "state.json")
    engine = AgentLoopEngine(state_file=state_file)
    asyncio.run(engine.run(cycles=3))
    metrics = calculate_agi_metrics(engine.state["history"])
    assert metrics["cycles"] == 3 and metrics["best_cycle"] in {1, 2, 3}
    assert engine.state["cycle"] == 4
