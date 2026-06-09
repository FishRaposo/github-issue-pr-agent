# Architectural Design - GitHub Issue-to-PR Agent

This document outlines the architectural design, dataflow, and component interactions of the GitHub Issue-to-PR Agent.

---

## 1. System Overview

The GitHub Issue-to-PR Agent is an autonomous development bot designed to ingest GitHub issues, formulate code modifications, apply code patches locally, run regression test suites, and open draft pull requests. 

The architecture is built on a step-by-step pipeline ensuring security gates (like path allowlists) are checked before any code edit occurs.

---

## 2. Ingestion & Execution Workflow

```mermaid
graph TD
    subgraph GitHub
        Issue[GitHub Issue]
        PR[Draft Pull Request]
    end

    subgraph Agent Pipeline
        Ingest[MockGitHubClient github.py] -->|1. Fetch Issue| Planner[CodePlanner planner.py]
        Planner -->|2. Generate Plan| Sandbox[CodeEditor editor.py]
        Sandbox -->|3. Apply Code Fix| Runner[LocalTestRunner test_runner.py]
        Runner -->|4. Execute Tests| Ingest
        Ingest -->|5. Create Draft PR| PR
    end

    subgraph Infrastructure
        APIServer[main.py] --> DB[PostgreSQL]
        APIServer --> Redis[Redis]
    end
```

---

## 3. Detailed Dataflow Sequence

```mermaid
sequenceDiagram
    participant GH as GitHub API / Client
    participant App as API Server (main.py)
    participant Plan as CodePlanner
    participant Edit as CodeEditor
    participant Test as TestRunner

    App->>GH: get_issue(issue_id)
    GH-->>App: Issue Payload (Title, Body, Labels)
    App->>Plan: plan_changes(issue)
    Note over Plan: Formulate file fix steps
    Plan-->>App: Execution Plan text
    App->>Edit: apply_fix(filepath)
    Note over Edit: Verify allowlisted paths
    Edit->>Edit: Apply target search-and-replace
    Edit-->>App: Fix applied status
    App->>Test: run_tests()
    Note over Test: Execute pytest subprocess
    Test-->>App: tests_passed (True/False)
    App->>GH: create_pull_request(branch, title, body)
    GH-->>App: Pull Request URL (draft)
```

---

## 4. Module Breakdown

### 4.1 GitHub Client (`github.py`)
- **`MockGitHubClient`**: Simulates communication with the GitHub API. In production, this utilizes PyGithub or standard requests to fetch issue details and submit pull requests.

### 4.2 Code Planner (`planner.py`)
- **`CodePlanner`**: Analyzes the issue content (such as bug descriptions) and generates a step-by-step text instruction mapping which files need modification and how to apply the fix.

### 4.3 Code Editor (`editor.py`)
- **`CodeEditor`**: Handles files edits. It implements search-and-replace algorithms to apply patches. It must validate that target filepaths fall within strict safety directories.

### 4.4 Local Test Runner (`test_runner.py`)
- **`LocalTestRunner`**: Spawns local test environments (e.g. executing `pytest` via `subprocess`) and parses the terminal exit codes and console logs to verify that the code edits did not break the build.
