import asyncio
from lib.agents.base import BaseAgent
from lib.agents.orchestrator import OrchestratorAgent


class Echo(BaseAgent):
    name = "echo"
    description = "gibt Payload zurueck"

    async def process(self, payload):
        return {"echo": payload}


def test_register_and_route():
    orch = OrchestratorAgent()
    agent = Echo()
    orch.register(agent, task_type="echo")
    assert orch.route("echo") is agent
    assert orch.route("unbekannt") is None


def test_process_routes_correctly():
    orch = OrchestratorAgent()
    orch.register(Echo(), task_type="echo")
    out = asyncio.run(orch.process({"task_type": "echo", "payload": {"x": 1}}))
    assert out["ok"] is True and out["agent"] == "echo"
    assert out["result"] == {"echo": {"x": 1}}


def test_process_unknown_task_type():
    orch = OrchestratorAgent()
    out = asyncio.run(orch.process({"task_type": "gibtsnicht"}))
    assert out["ok"] is False and "kein Agent" in out["error"]
