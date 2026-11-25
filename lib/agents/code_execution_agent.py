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
MAX_OUTPUT_BYTES = 65536


async def _read_limited(stream, limit=MAX_OUTPUT_BYTES):
    """Read at most limit bytes and signal immediately when a stream exceeds it."""
    data = bytearray()
    while len(data) <= limit:
        chunk = await stream.read(min(8192, limit + 1 - len(data)))
        if not chunk:
            return bytes(data), False
        data.extend(chunk)
    return bytes(data[:limit]), True


async def _monitor_process(proc):
    stdout_task = asyncio.create_task(_read_limited(proc.stdout))
    stderr_task = asyncio.create_task(_read_limited(proc.stderr))
    wait_task = asyncio.create_task(proc.wait())
    readers = {stdout_task, stderr_task}
    try:
        while readers:
            done, _ = await asyncio.wait(readers | {wait_task},
                                         return_when=asyncio.FIRST_COMPLETED)
            for task in done & readers:
                readers.remove(task)
                if task.result()[1]:
                    proc.kill()
                    await wait_task
                    stdout, stderr = await asyncio.gather(stdout_task, stderr_task)
                    return "output_limit", stdout, stderr
            if wait_task in done:
                stdout, stderr = await asyncio.gather(stdout_task, stderr_task)
                return "complete", stdout, stderr
        await wait_task
        stdout, stderr = await asyncio.gather(stdout_task, stderr_task)
        return "complete", stdout, stderr
    except asyncio.CancelledError:
        for task in (*readers, wait_task):
            task.cancel()
        await asyncio.gather(*readers, wait_task, return_exceptions=True)
        raise


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
            monitor = asyncio.create_task(_monitor_process(proc))
            try:
                proc.stdin.write(code.encode())
                await proc.stdin.drain()
                proc.stdin.close()
                outcome, stdout, stderr = await asyncio.wait_for(monitor, timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                await asyncio.gather(monitor, return_exceptions=True)
                return {"success": False, "stdout": "", "stderr": "Timeout"}
            except asyncio.CancelledError:
                if proc.returncode is None:
                    proc.kill()
                await proc.wait()
                await asyncio.gather(monitor, return_exceptions=True)
                raise
            if outcome == "output_limit":
                await proc.wait()
                return {"success": False,
                        "stdout": stdout[0].decode(errors="replace"),
                        "stderr": "Output limit exceeded (65536 bytes per stream)"}
            return {"success": proc.returncode == 0,
                    "stdout": stdout[0].decode(errors="replace"),
                    "stderr": stderr[0].decode(errors="replace")}
    async def process(self, payload):
        return await self.execute(payload.get("code", ""), payload.get("timeout", 3))
