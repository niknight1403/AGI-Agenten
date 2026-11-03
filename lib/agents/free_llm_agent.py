"""Cost-aware configured provider cascade. Free tiers are finite; offline is a placeholder."""
import asyncio
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from .base import BaseAgent


class FreeLLMAgent(BaseAgent):
    name = "free_llm"
    PROVIDERS = (("ollama", "OLLAMA_BASE_URL"), ("groq", "GROQ_API_KEY"),
                 ("together", "TOGETHER_API_KEY"))

    def __init__(self, cooldown_seconds=30):
        self.cooldown_seconds = cooldown_seconds
        self._unavailable_until = {}
        self._failures = {}

    def available_providers(self):
        now = time.monotonic()
        return [name for name, env in self.PROVIDERS
                if os.getenv(env) and now >= self._unavailable_until.get(name, 0)]

    @staticmethod
    def _ollama_url():
        configured = os.environ["OLLAMA_BASE_URL"]
        parsed = urllib.parse.urlsplit(configured)
        if (parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1", "::1")
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ("", "/")):
            raise ValueError("Ollama endpoint must be local HTTP origin")
        return configured.rstrip("/") + "/api/generate"

    def _request(self, provider, prompt):
        if provider == "ollama":
            url = self._ollama_url()
            body = {"model": os.getenv("OLLAMA_MODEL", "llama3.2"),
                    "prompt": prompt, "stream": False}
            headers = {"Content-Type": "application/json"}
        else:
            url, env, model = {
                "groq": ("https://api.groq.com/openai/v1/chat/completions",
                         "GROQ_API_KEY", "llama-3.1-8b-instant"),
                "together": ("https://api.together.xyz/v1/chat/completions",
                             "TOGETHER_API_KEY", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"),
            }[provider]
            body = {"model": os.getenv(provider.upper() + "_MODEL", model),
                    "messages": [{"role": "user", "content": prompt}], "max_tokens": 384}
            headers = {"Content-Type": "application/json",
                       "Authorization": "Bearer " + os.environ[env]}
        request = urllib.request.Request(url, json.dumps(body).encode(),
                                         headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read(1024 * 1024))
        return data["response"] if provider == "ollama" else data["choices"][0]["message"]["content"]

    def _mark_failure(self, provider):
        failures = self._failures.get(provider, 0) + 1
        self._failures[provider] = failures
        self._unavailable_until[provider] = time.monotonic() + min(
            self.cooldown_seconds * (2 ** min(failures - 1, 5)), 900)

    async def process(self, payload):
        prompt = str(payload.get("prompt", ""))[:10000]
        for provider in self.available_providers():
            try:
                output = await asyncio.wait_for(asyncio.to_thread(
                    self._request, provider, prompt), timeout=10)
                if isinstance(output, str) and output.strip():
                    self._failures.pop(provider, None)
                    self._unavailable_until.pop(provider, None)
                    return {"provider": provider, "response": output, "fallback": False}
                self._mark_failure(provider)
            except (OSError, ValueError, KeyError, IndexError, TypeError,
                    asyncio.TimeoutError, urllib.error.HTTPError):
                self._mark_failure(provider)
        return {"provider": "offline", "response": "OFFLINE-HYPOTHESE: " + prompt[:200],
                "fallback": True}

    async def generate_response(self, prompt):
        return (await self.process({"prompt": prompt}))["response"]
