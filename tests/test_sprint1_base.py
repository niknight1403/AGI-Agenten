import asyncio
from lib.agents.base import BaseAgent


class Dummy(BaseAgent):
    name = "dummy"
    description = "Test-Agent"

    async def process(self, payload):
        return {"ok": True, "input": payload}


def test_base_agent_is_abstract():
    import pytest
    with pytest.raises(TypeError):
        BaseAgent()  # type: ignore[abstract]


def test_dummy_agent_process_and_describe():
    dummy = Dummy()
    result = asyncio.run(dummy.process({"task": "test"}))
    assert result == {"ok": True, "input": {"task": "test"}}
    info = dummy.describe()
    assert info["name"] == "dummy" and "Test-Agent" in info["description"]
