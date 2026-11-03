import time
from .base import BaseAgent
class APIRotatorAgent(BaseAgent):
    name = "api_rotator"
    def __init__(self, keys=None, cooldown=60):
        self.keys = list(keys or [])
        self.cooldown = cooldown
        self.deadlines = {}
        self.index = 0
    def get_next(self):
        for _ in range(len(self.keys)):
            key = self.keys[self.index % len(self.keys)]
            self.index += 1
            if time.monotonic() >= self.deadlines.get(key, 0):
                return key
        return None
    def report_failure(self, key):
        if key in self.keys:
            self.deadlines[key] = time.monotonic() + self.cooldown
    async def process(self, payload):
        action = payload.get("action", "next")
        if action == "status":
            return {"ok": True, "status": {"total": len(self.keys)}}
        if action == "next":
            key = self.get_next()
            return {"ok": key is not None, "key": key}
        if action == "failure":
            self.report_failure(payload.get("key"))
            return {"ok": True}
        return {"ok": False, "error": "unbekannte Aktion"}
