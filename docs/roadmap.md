# Project Roadmap - GitHub Issue-to-PR Agent

This document outlines the milestones and timeline of features for the GitHub Issue-to-PR Agent.

---

## Milestone 1: Pipeline Core & Mock Interface (Completed)
- **FastAPI Core**: Host the server routes and health indicators.
- **GitHub Client Mock**: Retrieve issue payloads and simulate draft PR generation.
- **Pattern Editor**: Safe file search-and-replace interface.
- **Local Test Scaffold**: Basic test-running process placeholder.

---

## Milestone 2: Live GitHub API & Hermes Integration (Planned)
- **Active GitHub Integration**: Swap Mock client with official GitHub integration using JWT token auth, supporting webhook trigger actions on issue creation.
- **Hermes Agent Framework Loop**: Connect to the Hermes agent loop, allowing the agent to dynamically plan, edit, test, and self-correct on test failure.
- **Audit Console**: A web interface rendering the timeline of processed issues, LLM code plans, test logs, and git diff snapshots.
- **Safety Allowlist Management**: Configure allowed files/directories paths and repo filters via DB configurations.

---

## Milestone 3: Sandboxed Environments & Performance Evaluations (Future)
- **Dockerized Test Sandbox**: Execute editing and test execution inside ephemeral, network-isolated Docker containers to safeguard host system files.
- **Multi-File Context Refactoring**: Enhance the planning and editing logic to support multi-file structural modifications.
- **Performance Regression Checks**: Run performance profiling (using LLM monitor logs) on the generated code to check for memory leaks or latency increases before PR creation.
