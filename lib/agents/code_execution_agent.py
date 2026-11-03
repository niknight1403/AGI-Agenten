"""Restricted demo executor. NOT a security boundary for hostile code.
Production hostile code requires a network-isolated container or VM with resource caps.
"""
import ast
import asyncio
import sys
import tempfile
from .base import BaseAgent
ALLOWED = (ast.Module, ast.Expr, ast.Call, ast.Name, ast.Load, ast.Constant, ast.BinOp,
           ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.UnaryOp,
           ast.USub, ast.UAdd, ast.Assign, ast.Store, ast.While, ast.Compare, ast.Lt,
           ast.Gt, ast.Eq, ast.NotEq, ast.Pass, ast.Break, ast.Raise, ast.List, ast.Tuple)
CALLS = {"print", "range", "len", "ValueError"}
def validate_code(code):
    try:
        tree = ast.parse(code)
    except (SyntaxError, TypeError) as exc:
        return "Syntaxfehler: " + str(exc)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for item in node.names:
                if item.name.split(".")[0] in {"os", "sys", "subprocess", "socket", "pathlib", "shutil"}:
                    return "verbotenes Modul: " + item.name.split(".")[0]
            return "Importe sind nicht erlaubt"
        if not isinstance(node, ALLOWED):
            return "Nicht erlaubte Syntax: " + type(node).__name__
        if isinstance(node, ast.Call) and (not isinstance(node.func, ast.Name) or node.func.id not in CALLS):
            return "Nicht erlaubter Funktionsaufruf"
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            return "Nicht erlaubter Bezeichner"
    return None
class CodeExecutionAgent(BaseAgent):
    name = "code_execution"
    async def execute(self, code, timeout=3):
        error = validate_code(code)
        if error:
            return {"success": False, "stdout": "", "stderr": error}
        if not isinstance(timeout, (int, float)) or not 0 < timeout <= 30:
            return {"success": False, "stdout": "", "stderr": "Ungueltiger Timeout"}
        runner = ('import builtins,sys\n'
                  'safe={k:getattr(builtins,k) for k in ("print","range","len","ValueError")}\n'
                  'exec(compile(sys.stdin.read(),"<task>","exec"),{"__builtins__":safe})\n')
        with tempfile.TemporaryDirectory(prefix="agi-exec-") as directory:
            proc = await asyncio.create_subprocess_exec(sys.executable, "-I", "-S", "-c", runner,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE, cwd=directory, env={"PYTHONIOENCODING": "utf-8"})
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(code.encode()), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return {"success": False, "stdout": "", "stderr": "Timeout"}
            return {"success": proc.returncode == 0, "stdout": stdout.decode(errors="replace")[:65536], "stderr": stderr.decode(errors="replace")[:65536]}
    async def process(self, payload):
        return await self.execute(payload.get("code", ""), payload.get("timeout", 3))
