"""AGI-Agenten Loop-Engine: Plan -> Execute -> Evaluate -> Optimize."""
import argparse
import asyncio
import json
import logging
import os
import sys
import tempfile
import time
from typing import Any, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.agents.orchestrator import OrchestratorAgent
from lib.agents.code_execution_agent import CodeExecutionAgent
from lib.agents.evaluation import EvaluationAgent
from lib.agents.self_optimization import SelfOptimizationAgent
from lib.agents.free_llm_agent import FreeLLMAgent
from lib.agents.api_rotator_agent import APIRotatorAgent
from lib.agents.mcp_connector_agent import MCPConnectorAgent
from lib.agents.skill_agent import SkillAgent
from lib.design.future_glass import createStyles, CYAN
from lib.utils.metrics import calculate_agi_metrics
from lib.config import STATE_FILE

logging.basicConfig(filename="agent_loop.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("agent_loop")


class AgentLoopEngine:
    def __init__(self, state_file: str = None):
        self.state_file = state_file or STATE_FILE
        self.state = self._load_state()
        self.orchestrator = OrchestratorAgent()
        self.code_execution = CodeExecutionAgent()
        self.evaluation = EvaluationAgent()
        self.self_optimization = SelfOptimizationAgent()
        self.free_llm = FreeLLMAgent()
        self.api_rotator = APIRotatorAgent()
        self.mcp = MCPConnectorAgent()
        self.skill = SkillAgent()
        for agent, task_type in [(self.free_llm, "hypothesis"),
                                 (self.code_execution, "execute"),
                                 (self.evaluation, "evaluate"),
                                 (self.self_optimization, "optimize")]:
            self.orchestrator.register(agent, task_type=task_type)

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.state_file):
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if (not isinstance(data, dict) or type(data.get("cycle")) is not int
                    or data["cycle"] < 1 or not isinstance(data.get("history"), list)):
                raise ValueError("Invalid AGI state file schema")
            return data
        return {"cycle": 1, "history": []}

    def _save_state(self) -> None:
        directory = os.path.dirname(os.path.abspath(self.state_file))
        fd, temporary = tempfile.mkstemp(prefix=".agi-state-", suffix=".json", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temporary, self.state_file)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    async def run_plan_phase(self) -> Dict[str, Any]:
        prompt = ("Generiere eine Hypothese fuer AGI-Optimierung mit kostenlosen LLMs"
                  + self.self_optimization.prompt_suffix)
        routed = await self.orchestrator.process(
            {"task_type": "hypothesis", "payload": {"prompt": prompt}})
        if not routed.get("ok") or not isinstance(routed.get("result"), dict):
            raise RuntimeError("Hypothesis provider failed")
        hypothesis = routed["result"]["response"]
        logger.info("Plan-Phase Zyklus %s: %s", self.state["cycle"], hypothesis[:80])
        return {"hypothesis": hypothesis,
                "provider": routed["result"].get("provider"),
                "offline_fallback": routed["result"].get("fallback", False),
                "design_tokens": {
                    "background": createStyles(
                        wide={"background": "rgba(0, 0, 0, 0.8)"})["wide"]["background"],
                    "accent_color": CYAN}}

    async def run_execution_phase(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        # Explicit demonstration only; the hypothesis is NOT executable code.
        result = await self.code_execution.execute("print('Hypothese geprueft:', 40 + 2)")
        logger.info("Execution-Phase: success=%s", result["success"])
        return {"execution": result, "hypothesis": plan["hypothesis"]}

    async def run_evaluation_phase(self, execution: Dict[str, Any]) -> Dict[str, Any]:
        evaluation = self.evaluation.evaluate(
            {"response": execution["hypothesis"],
             "success": execution["execution"]["success"]},
            criteria={"keywords": ["hypothese", "agi"]})
        logger.info("Evaluation: score=%s passed=%s",
                    evaluation["score"], evaluation["passed"])
        return evaluation

    async def run_optimization_phase(self) -> Dict[str, Any]:
        suggestion = self.self_optimization.analyze(self.state["history"])
        applied = self.self_optimization.apply(suggestion)
        logger.info("Optimierung: strategy=%s", applied["strategy"])
        return {"suggestion": suggestion, "applied": applied}

    async def run_cycle(self) -> Dict[str, Any]:
        cycle = self.state["cycle"]
        plan = await self.run_plan_phase()
        execution = await self.run_execution_phase(plan)
        evaluation = await self.run_evaluation_phase(execution)
        entry = {"cycle": cycle, "score": evaluation["score"],
                 "passed": evaluation["passed"], "ts": time.time(),
                 "provider": plan["provider"],
                 "offline_fallback": plan["offline_fallback"]}
        self.state["history"].append(entry)
        optimization = await self.run_optimization_phase()
        self.state["cycle"] = cycle + 1
        self._save_state()
        return {"cycle": cycle, **plan, "evaluation": evaluation,
                "optimization": optimization["applied"]}

    async def run(self, cycles: int = 1) -> Dict[str, Any]:
        if not isinstance(cycles, int) or cycles < 1:
            raise ValueError("cycles must be a positive integer")
        last = None
        for _ in range(cycles):
            last = await self.run_cycle()
        return {"metrics": calculate_agi_metrics(self.state["history"]),
                "last_cycle": last}


async def _main(cycles: int, state_file: str = None) -> None:
    engine = AgentLoopEngine(state_file=state_file)
    result = await engine.run(cycles=cycles)
    print(json.dumps(result["metrics"], indent=2, ensure_ascii=False))
    print(f"Letzter Zyklus: {result['last_cycle']['cycle']} | "
          f"Score: {result['last_cycle']['evaluation']['score']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="AGI-Agenten Loop-Engine")
    parser.add_argument("--cycles", type=int, default=1,
                        help="Anzahl auszufuehrender Zyklen, mindestens 1")
    parser.add_argument("--state-file", default=None, help="Pfad zur State-Datei")
    args = parser.parse_args()
    if args.cycles < 1:
        parser.error("--cycles must be >= 1")
    asyncio.run(_main(args.cycles, args.state_file))


if __name__ == "__main__":
    main()
