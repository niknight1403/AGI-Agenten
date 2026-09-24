import asyncio
from lib.agents.skill_agent import SkillAgent
from lib.design.future_glass import createStyles, CYAN
from lib.utils.metrics import calculate_agi_metrics


def test_skill_lifecycle():
    skill = SkillAgent()
    out = skill.create_skill("addiere", "print(2 + 3)")
    assert out["ok"]
    result = asyncio.run(skill.run_skill("addiere"))
    assert result["success"] and result["stdout"].strip() == "5"
    assert "addiere" in skill.list_skills()["skills"]


def test_unsafe_skill_rejected():
    skill = SkillAgent()
    out = skill.create_skill("boese", "import os")
    assert not out["ok"] and "verbotenes Modul" in out["error"]


def test_unknown_skill():
    skill = SkillAgent()
    out = asyncio.run(skill.run_skill("nix"))
    assert not out["ok"]


def test_createstyles_merges_defaults():
    styles = createStyles(wide={"background": "rgba(0, 0, 0, 0.8)"})
    assert styles["wide"]["background"] == "rgba(0, 0, 0, 0.8)"
    assert styles["accent_color"] == CYAN
    assert "blur" in styles


def test_metrics_rising_trend():
    hist = [{"cycle": 1, "score": 0.3}, {"cycle": 2, "score": 0.5}, {"cycle": 3, "score": 0.9}]
    m = calculate_agi_metrics(hist)
    assert m["cycles"] == 3 and m["avg_score"] == 0.57
    assert m["trend"] == "steigend" and m["best_cycle"] == 3


def test_metrics_empty():
    m = calculate_agi_metrics([])
    assert m["cycles"] == 0 and m["avg_score"] is None
