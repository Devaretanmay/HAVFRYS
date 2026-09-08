# Product Validation Guide: Testing Volf with Your AI Agents

This guide provides a quick test suite for validating Volf as the audit and control layer for your AI agents and codebase dependencies.

---

## The Core Validation Model

```text
WITHOUT VOLF
Agent -> Tools -> OS / Credentials / Network (Unmonitored)

WITH VOLF
Agent -> VOLF (Topology, Policies, Proxy, Snapshots) -> OS (Kernel Enforced)
```

---

## 1. Test Scenario 1: CLI Coding Agent (Claude Code / Shell Agent)

Validate that an AI agent reading your repo and executing bash commands is blocked from reading `~/.ssh` or `~/.aws` credentials while executing workspace tasks cleanly.

```bash
volf claude
# or arbitrary command execution:
volf exec -- cat ~/.ssh/id_rsa
```

### What You Observe:
- Host SSH credential access is blocked by the OS kernel.
- Workspace file modifications are tracked with BLAKE3 file diffs.
- `volf diff` isolates agent modifications.
- `volf undo` restores workspace state in 2ms.

---

## 2. Test Scenario 2: Day-0 External Dependency Audit & Risk Register

Audit your entire codebase for upstream breaking changes, deprecated API callsites, and auto-repairable integrations.

```bash
volf audit .
volf audit . --format=github-issue
```

### What You Observe:
- AST parser maps all external SDK and API callsites across TypeScript, Python, and Go.
- Categorizes dependencies into At-Risk, Watchlist, and Healthy.
- Generates formatted risk register markdown ready for GitHub Issues.

---

## 3. Test Scenario 3: Autonomous Continuous Maintenance Loop

Detect upstream API drift and synthesize verified AST patches against breaking changes.

```bash
volf maintain . --provider stripe
```

### What You Observe:
- Scans manifests and callsites against official provider contracts.
- Generates surgical AST patch and runs local formatters (prettier/ruff).
- Validates repository tests and blast-radius constraints before creating a Developer Trust PR.

---

## The Validation Question

After running these validation scenarios on your codebase:

> **"Would you run your coding agents without Volf?"**
