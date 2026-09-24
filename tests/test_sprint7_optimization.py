import asyncio
from lib.agents.self_optimization import SelfOptimizationAgent


def test_empty_history_diversifies():
    opt = SelfOptimizationAgent()
    out = opt.analyze([])
    assert out["strategy"] == "diversify" and out["avg_score"] is None


def test_low_scores_trigger_refine():
    opt = SelfOptimizationAgent()
    out = opt.analyze([{"score": 0.2}, {"score": 0.3}])
    assert out["strategy"] == "refine" and out["avg_score"] == 0.25
    applied = opt.apply(out)
    assert "metrik" in applied["prompt_suffix"].lower() or "Metrik" in applied["prompt_suffix"]


def test_high_scores_keep():
    opt = SelfOptimizationAgent()
    out = opt.analyze([{"score": 0.9}, {"score": 0.85}])
    assert out["strategy"] == "keep"


def test_unknown_strategy_falls_back():
    opt = SelfOptimizationAgent()
    applied = opt.apply({"strategy": "quatsch"})
    assert applied["strategy"] == "keep"


def test_process_with_history():
    out = asyncio.run(SelfOptimizationAgent().process({"history": [{"score": 0.1}]}))
    assert out["strategy"] == "refine" and out["prompt_suffix"]
