import asyncio
import json
import pytest
from lib.agents.mcp_connector_agent import MCPConnectorAgent


@pytest.fixture
def config(tmp_path):
    cfg = {"tools": {"calc": {"description": "Rechnet"}, "echo": {"description": "Echo"}}}
    p = tmp_path / "mcp.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return str(p)


def test_load_registers_tools(config):
    mcp = MCPConnectorAgent()
    out = mcp.load(config)
    assert out["ok"] and out["loaded"] == 2 and "calc" in out["tools"]


def test_load_missing_file():
    mcp = MCPConnectorAgent()
    out = mcp.load("/gibts/nicht.json")
    assert not out["ok"] and "nicht gefunden" in out["error"]


def test_call_tool_with_handler(config):
    mcp = MCPConnectorAgent()
    mcp.load(config)
    mcp.register_handler("calc", lambda args: sum(args.get("values", [])))
    out = asyncio.run(mcp.call_tool("calc", {"values": [1, 2, 3]}))
    assert out["ok"] and out["result"] == 6


def test_unknown_tool_rejected(config):
    mcp = MCPConnectorAgent()
    mcp.load(config)
    out = asyncio.run(mcp.call_tool("nix"))
    assert not out["ok"] and "unbekanntes Tool" in out["error"]


def test_handler_missing(config):
    mcp = MCPConnectorAgent()
    mcp.load(config)
    out = asyncio.run(mcp.call_tool("echo", {"x": 1}))
    assert not out["ok"] and "kein Handler" in out["error"]
