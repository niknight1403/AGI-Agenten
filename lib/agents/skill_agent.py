from .base import BaseAgent
from .code_execution_agent import CodeExecutionAgent, validate_code
class SkillAgent(BaseAgent):
    name = "skill"
    def __init__(self):
        self.skills = {}
        self.executor = CodeExecutionAgent()
    def create_skill(self, name, code):
        if not isinstance(name, str) or not name.isidentifier() or name.startswith("_"):
            return {"ok": False, "error": "Ungueltiger Skillname"}
        error = validate_code(code)
        if error:
            return {"ok": False, "error": error}
        self.skills[name] = code
        return {"ok": True, "name": name}
    def list_skills(self):
        return {"skills": sorted(self.skills)}
    async def run_skill(self, name):
        if name not in self.skills:
            return {"ok": False, "error": "unbekannter Skill"}
        return await self.executor.execute(self.skills[name])
    async def process(self, payload):
        if payload.get("action") == "create":
            return self.create_skill(payload.get("name"), payload.get("code"))
        return await self.run_skill(payload.get("name"))
