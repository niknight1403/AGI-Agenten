from lib.agents.api_rotator_agent import APIRotatorAgent


def test_round_robin_rotation():
    rot = APIRotatorAgent(keys=["a", "b", "c"])
    assert [rot.get_next() for _ in range(4)] == ["a", "b", "c", "a"]


def test_failure_triggers_cooldown():
    rot = APIRotatorAgent(keys=["a", "b"], cooldown=60)
    rot.report_failure("a")
    assert rot.get_next() == "b"
    assert rot.get_next() == "b"  # a liegt auf Cooldown


def test_cooldown_expires():
    rot = APIRotatorAgent(keys=["a"], cooldown=0.01)
    rot.report_failure("a")
    assert rot.get_next() is None
    import time; time.sleep(0.02)
    assert rot.get_next() == "a"


def test_all_on_cooldown_returns_none():
    rot = APIRotatorAgent(keys=["a"], cooldown=60)
    rot.report_failure("a")
    assert rot.get_next() is None


def test_process_status_and_success():
    import asyncio
    rot = APIRotatorAgent(keys=["a"])
    out = asyncio.run(rot.process({"action": "status"}))
    assert out["ok"] and out["status"]["total"] == 1
    out = asyncio.run(rot.process({"action": "unbekannt"}))
    assert out["ok"] is False
