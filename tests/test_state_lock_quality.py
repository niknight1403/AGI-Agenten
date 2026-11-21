"""Regression tests for concurrent state writes and truthful quality gates."""
import asyncio
import json
import multiprocessing
import os
import sys
import fcntl

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
def test_cancelled_lock_waiter_releases_late_acquisition(tmp_path):
    path = str(tmp_path / "state.json")
    lock_path = path + ".lock"

    async def run():
        with open(lock_path, "a+b") as holder:
            fcntl.flock(holder.fileno(), fcntl.LOCK_EX)
            waiter = asyncio.create_task(AgentLoopEngine(state_file=path).run_cycle())
            await asyncio.sleep(0.05)
            waiter.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(waiter, timeout=1)
            fcntl.flock(holder.fileno(), fcntl.LOCK_UN)
        # A cancelled waiter must not leave the lock held by its worker thread.
        async with asyncio.timeout(3):
            async with AgentLoopEngine(state_file=path)._state_lock():
                pass

    asyncio.run(run())


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
