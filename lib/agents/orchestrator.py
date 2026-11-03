from .base import BaseAgent
class OrchestratorAgent(BaseAgent):
    name = "orchestrator"
    def __init__(self):
        self.registry = {}
    def register(self, agent, task_type):
        if not isinstance(agent, BaseAgent):
            raise TypeError("Not an agent")
        self.registry[task_type] = agent
    def route(self, task_type):
        return self.registry.get(task_type)
    async def process(self, payload):
        agent = self.route(payload.get("task_type"))
        if agent is None:
            return {"ok": False, "error": "kein Agent fuer Task-Typ"}
        try:
            return {"ok": True, "agent": agent.name, "result": await agent.process(payload.get("payload", {}))}
        except Exception as exc:
            return {"ok": False, "agent": agent.name, "error": type(exc).__name__}
