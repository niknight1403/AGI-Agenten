import asyncio
import pytest
from lib.agents.code_execution_agent import CodeExecutionAgent, MAX_OUTPUT_BYTES


def test_simple_execution():
    out = asyncio.run(CodeExecutionAgent().execute("print(40 + 2)"))
    assert out["success"] and out["stdout"].strip() == "42"


def test_syntax_error_is_caught():
    out = asyncio.run(CodeExecutionAgent().execute("def kaputt(:"))
    assert not out["success"] and "Syntaxfehler" in out["stderr"]


def test_denylist_blocks_os_import():
    out = asyncio.run(CodeExecutionAgent().execute("import os\nos.system('echo hi')"))
    assert not out["success"] and "verbotenes Modul: os" in out["stderr"]


def test_runtime_error_reports_stderr():
    out = asyncio.run(CodeExecutionAgent().execute("raise ValueError('boese')"))
    assert not out["success"] and "boese" in out["stderr"]


def test_timeout_kills_runaway_code():
    out = asyncio.run(CodeExecutionAgent().execute("while True: pass", timeout=1))
    assert not out["success"] and "Timeout" in out["stderr"]


def test_stdout_limit_terminates_runaway_output():
    code = 'print("x" * 70000)'
    out = asyncio.run(CodeExecutionAgent().execute(code, timeout=5))
    assert not out["success"]
    assert len(out["stdout"].encode()) <= MAX_OUTPUT_BYTES
    assert "Output limit exceeded" in out["stderr"]


def test_stderr_is_bounded_during_capture():
    code = 'raise ValueError("x" * 70000)'
    out = asyncio.run(CodeExecutionAgent().execute(code, timeout=5))
    assert not out["success"]
    assert out["stdout"] == ""
    assert "Output limit exceeded" in out["stderr"]


def test_cancellation_reaps_child_process(monkeypatch):
    original = asyncio.create_subprocess_exec
    children = []

    async def track_process(*args, **kwargs):
        proc = await original(*args, **kwargs)
        children.append(proc)
        return proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", track_process)

    async def run():
        task = asyncio.create_task(
            CodeExecutionAgent().execute("while True: pass", timeout=30))
        while not children:
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=2)
        assert children[0].returncode is not None

    asyncio.run(run())
