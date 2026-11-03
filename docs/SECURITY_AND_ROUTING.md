# Security and routing assessment

- The former gitignore excluded the entire application library; it has been restored.
- The CodeExecutionAgent accepts only a small AST subset, runs Python with -I -S, no inherited environment, an isolated temporary working directory and a timeout. **This is not a security boundary**; hostile code must run inside an isolated no-network container/VM with OS-enforced memory, CPU and disk quotas.
- FreeLLMAgent uses configured credentials only; endpoints are bounded and unauthorized usage is not attempted. Provider availability, cost and current quota are **not** live-verified.
- Offline fallback is a deterministic placeholder, **not a real inference response**.
- MCPConnectorAgent is an in-process JSON tool registry, **not a complete remote MCP client**.
- Loop execution currently runs a fixed sample script and metrics are heuristic; not autonomous product development.
- CI runs pytest on pull requests and pushes. External API integration smoke tests require separately configured accounts.
