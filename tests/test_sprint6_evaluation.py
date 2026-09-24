import asyncio
from lib.agents.evaluation import EvaluationAgent


def test_good_result_passes():
    ev = EvaluationAgent()
    out = ev.evaluate({"response": "Hypothesis: rotate API keys for cost reduction"},
                      criteria={"keywords": ["api", "keys"]})
    assert out["passed"] and out["score"] >= 0.6


def test_empty_result_fails():
    ev = EvaluationAgent()
    out = ev.evaluate({"response": "   "})
    assert not out["passed"] and out["score"] < 0.6


def test_failed_execution_scores_zero():
    ev = EvaluationAgent()
    out = ev.evaluate({"success": False})
    assert out["score"] == 0.0 and not out["passed"]


def test_reasons_documented():
    ev = EvaluationAgent()
    out = ev.evaluate({"response": "kurz"})
    assert isinstance(out["reasons"], list) and len(out["reasons"]) == 3


def test_process_interface():
    out = asyncio.run(EvaluationAgent().process({"result": {"response": "ok"}, "criteria": {}}))
    assert out["score"] > 0
