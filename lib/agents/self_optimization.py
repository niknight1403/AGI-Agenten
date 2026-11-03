from .base import BaseAgent
class SelfOptimizationAgent(BaseAgent):
    name = "self_optimization"
    def __init__(self):
        self.prompt_suffix = ""
    def analyze(self, history):
        scores = [float(x["score"]) for x in history if isinstance(x.get("score"), (int, float))]
        avg = round(sum(scores)/len(scores), 3) if scores else None
        return {"strategy": "diversify" if avg is None else ("refine" if avg < 0.6 else "keep"), "avg_score": avg}
    def apply(self, suggestion):
        strategy = suggestion.get("strategy", "keep")
        if strategy not in ("diversify", "refine", "keep"):
            strategy = "keep"
        self.prompt_suffix = {"diversify": " Erzeuge alternative Hypothesen.", "refine": " Nutze klare Metriken und pruefbare Ergebnisse.", "keep": ""}[strategy]
        return {"strategy": strategy, "prompt_suffix": self.prompt_suffix}
    async def process(self, payload):
        return self.apply(self.analyze(payload.get("history", [])))
