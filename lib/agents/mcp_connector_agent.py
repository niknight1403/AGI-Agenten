"""JSON metadata + explicit local handlers; not a remote MCP transport."""
import json
from .base import BaseAgent
class MCPConnectorAgent(BaseAgent):
    name = "mcp_connector"
    def __init__(self):
        self.tools = {}
        self.handlers = {}
    def load(self, path):
        try:
            with open(path, encoding="utf-8") as handle:
                cfg = json.load(handle)
            if not isinstance(cfg.get("tools"), dict):
                return {"ok": False, "error": "Ungueltige Tool-Konfiguration"}
            self.tools = cfg["tools"]
            return {"ok": True, "loaded": len(self.tools), "tools": list(self.tools)}
        except FileNotFoundError:
            return {"ok": False, "error": "Konfiguration nicht gefunden"}
        except (ValueError, OSError) as exc:
            return {"ok": False, "error": "Konfigurationsfehler: " + type(exc).__name__}
    def register_handler(self, name, handler):
        self.handlers[name] = handler
    async def call_tool(self, name, args=None):
        if name not in self.tools:
            return {"ok": False, "error": "unbekanntes Tool"}
        if name not in self.handlers:
            return {"ok": False, "error": "kein Handler registriert"}
        try:
            result = self.handlers[name](args or {})
            if hasattr(result, "__await__"):
                result = await result
            return {"ok": True, "result": result}
        except Exception as exc:
            return {"ok": False, "error": "Tool-Ausfuehrung fehlgeschlagen: " + type(exc).__name__}
    async def process(self, payload):
        return await self.call_tool(payload.get("name"), payload.get("args", {}))
