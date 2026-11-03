"""Regression tests for concurrent state writes and truthful quality gates."""
import asyncio
import json
import multiprocessing
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent-loop"))
from agent_loop import AgentLoopEngine


def _worker(path, cycles):
    # Run inside an independent process to exercise flock on a separate fd.
    for _ in range(cycles):
        asyncio.run(AgentLoopEngine(state_file=path).run_cycle())


def _no_providers(monkeypatch):
    for name in ("OLLAMA_BASE_URL", "GROQ_API_KEY", "TOGETHER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_offline_cannot_pass_quality_gate(tmp_path, monkeypatch):
    _no_providers(monkeypatch)
    engine = AgentLoopEngine(state_file=str(tmp_path / "state.json"))
    output = asyncio.run(engine.run_cycle())
    assert output["offline_fallback"] is True
    assert output["evaluation"]["passed"] is False
    assert "Offline placeholder" in " ".join(output["evaluation"]["reasons"])
    assert engine.state["history"][0]["passed"] is False


def test_async_concurrent_instances_preserve_all_cycles(tmp_path, monkeypatch):
    _no_providers(monkeypatch)
    path = str(tmp_path / "state.json")
    instances = [AgentLoopEngine(state_file=path) for _ in range(3)]
    async def run():
        return await asyncio.gather(*(instance.run_cycle() for instance in instances))
    results = asyncio.run(run())
    data = json.loads((tmp_path / "state.json").read_text())
    assert sorted(result["cycle"] for result in results) == [1, 2, 3]
    assert data["cycle"] == 4
    assert len(data["history"]) == 3


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX flock only")
def test_process_concurrency_preserves_all_cycles(tmp_path, monkeypatch):
    _no_providers(monkeypatch)
    path = str(tmp_path / "state.json")
    processes = [multiprocessing.Process(target=_worker, args=(path, 2))
                 for _ in range(2)]
    for proc in processes:
        proc.start()
    for proc in processes:
        proc.join(timeout=25)
        if proc.is_alive():
            proc.kill()
            proc.join()
            pytest.fail("worker deadlocked")
        assert proc.exitcode == 0
    state = json.loads((tmp_path / "state.json").read_text())
    assert state["cycle"] == 5
    assert [entry["cycle"] for entry in state["history"]] == [1, 2, 3, 4]
