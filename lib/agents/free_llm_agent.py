"""Bounded free-tier provider cascade; no claim of unlimited quota."""
import asyncio
import json
import os
import urllib.request
from .base import BaseAgent
class FreeLLMAgent(BaseAgent):
    name = "free_llm"
    def available_providers(self):
        return [name for name, env in [("ollama", "OLLAMA_BASE_URL"), ("groq", "GROQ_API_KEY"), ("together", "TOGETHER_API_KEY")] if os.getenv(env)]
    def _request(self, provider, prompt):
        if provider == "ollama":
            url = os.environ["OLLAMA_BASE_URL"].rstrip("/") + "/api/generate"
            if not (url.startswith("http://localhost:") or url.startswith("http://127.0.0.1:")):
                raise ValueError("Ollama endpoint must be localhost")
            body = {"model": os.getenv("OLLAMA_MODEL", "llama3.2"), "prompt": prompt, "stream": False}
            headers = {"Content-Type": "application/json"}
        else:
            url, env, model = {"groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY", "llama-3.1-8b-instant"), "together": ("https://api.together.xyz/v1/chat/completions", "TOGETHER_API_KEY", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")}[provider]
            body = {"model": os.getenv(provider.upper() + "_MODEL", model), "messages": [{"role": "user", "content": prompt}], "max_tokens": 384}
            headers = {"Content-Type": "application/json", "Authorization": "Bearer " + os.environ[env]}
        request = urllib.request.Request(url, json.dumps(body).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read(1024 * 1024))
        return data["response"] if provider == "ollama" else data["choices"][0]["message"]["content"]
    async def process(self, payload):
        prompt = str(payload.get("prompt", ""))[:10000]
        for provider in self.available_providers():
            try:
                output = await asyncio.wait_for(asyncio.to_thread(self._request, provider, prompt), timeout=10)
                if isinstance(output, str) and output.strip():
                    return {"provider": provider, "response": output}
            except (OSError, ValueError, KeyError, IndexError, TypeError, asyncio.TimeoutError):
                continue
        return {"provider": "offline", "response": "OFFLINE-HYPOTHESE: " + prompt[:200]}
    async def generate_response(self, prompt):
        return (await self.process({"prompt": prompt}))["response"]
