# Sprint-Log
Alle 10 Sprints abgeschlossen. Jeder Sprint: Implementierung + Tests + Commit.

- Sprint 1: Fundament (lib/, BaseAgent, config) - 2 Tests
- Sprint 2: OrchestratorAgent - 3 Tests
- Sprint 3: FreeLLMAgent (Ollama/Groq/Together + Offline-Fallback) - 3 Tests
- Sprint 4: APIRotatorAgent (Round-Robin, Cooldown) - 5 Tests
- Sprint 5: CodeExecutionAgent (Sandbox, Timeout, Denylist) - 5 Tests
- Sprint 6: EvaluationAgent (Heuristik-Score) - 5 Tests
- Sprint 7: SelfOptimizationAgent (Strategieregeln) - 5 Tests
- Sprint 8: MCPConnectorAgent (JSON-Config, Handler) - 5 Tests
- Sprint 9: SkillAgent + Design-Tokens + Metriken - 6 Tests
- Sprint 10: Engine komplett, install.sh (fake HTML) entfernt, README, E2E - 2 Tests
Ergebnis: 41/41 Tests gruen, CLI-Smoke-Test ok.

## Neue Sprint-Serie

- Sprint 11: Zuverlässigkeit – Zustands-Historie validiert Scores im Bereich 0–1,
  optionale Metadaten und Zyklusreihenfolge; Persistenz verbietet nicht-endliche
  JSON-Werte und synchronisiert den Verzeichniseintrag nach atomarem Replace.
  Sparse Historien aus älteren Versionen bleiben unterstützt.
- Abnahme Sprint 11: 75/75 Tests gruen (inkl. Parallelitäts- und Multiprozess-Tests).
- Sprint 12: Zuverlässigkeit – Code-Executor liest stdout/stderr fortlaufend und
  beendet den Kindprozess, sobald ein Stream 64 KiB überschreitet; Timeout und
  Cancellation räumen weiter Prozess und Reader auf.
- Abnahme Sprint 12: 77/77 Tests gruen, einschließlich großer stdout/stderr-Ausgaben.
