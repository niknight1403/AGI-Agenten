from .base import BaseAgent
class EvaluationAgent(BaseAgent):
    name = "evaluation"
    def evaluate(self, result, criteria=None):
        if result.get("success") is False:
            return {"score": 0.0, "passed": False, "reasons": ["Execution failed", "No valid output", "Not approved"]}
        response = str(result.get("response", "")).strip()
        keywords = [str(k).lower() for k in (criteria or {}).get("keywords", [])]
        matched = sum(k in response.lower() for k in keywords)
        score = round((0.4 if response else 0) + (0.4 * matched / len(keywords) if keywords else (0.4 if response else 0)) + (0.2 if len(response) >= 10 else (0.1 if response else 0)), 3)
        return {"score": score, "passed": score >= 0.6, "reasons": ["Response presence", "Keyword coverage", "Response length"]}
    async def process(self, payload):
        return self.evaluate(payload.get("result", {}), payload.get("criteria", {}))
