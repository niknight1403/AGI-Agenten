import asyncio
from lib.agents.code_execution_agent import CodeExecutionAgent


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
