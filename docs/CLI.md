# Volf CLI Reference & User Guide

Volf is autonomous software maintenance for systems that change. It detects contract drift, repairs the code, verifies against your real test suite, and delivers the evidence as a PR.

> **“Volf understands the changes the outside world makes to software — and repairs them.”**

---

## The Public CLI Contract

```text
Maintenance product (normal flow: auth → doctor → index → check → fix)
  volf auth                     Connect BYOK AI provider (needed only for AI repair)
  volf doctor                   Product readiness: GitHub, AI, index, knowledge, tests
  volf index [path]             Index repository contracts & callsites (free, zero-token)
  volf check [path]             Detect contract changes & impact (read-only; needs no AI key)
          volf fix [path] [--provider]  Repair, verify in sandbox, report evidence (alias: maintain)
          volf consult [path]         Assess with AI reasoning, file GitHub Issue, change nothing
          volf reviews [path]         List past maintenance runs from the ledger
          volf onboard [path]         Guided setup: auth → index → doctor
          volf logout                 Remove stored credentials (alias for auth --clear)
  volf providers                List monitored contract sources & migrations
  volf app serve                Run GitHub App webhook listener (secret required)
  volf pr                       Review a pull request with the contract guard

Legacy / advanced (workflows, sessions, lanes)
  volf init                     Initialize a Volf workspace (legacy path; onboarding no longer needs this)
  volf status                   Show workspace health & active executions
  volf inspect                  Dump declared compartments & policies

Agents
  volf claude | opencode | codex | cursor | aider
                                   Run coding agent in governed OS sandbox
  volf exec -- <cmd>            Run arbitrary command inside a compartment

Workflows
  volf -w <name>                Create a new workflow branch
  volf step <workflow> <target> Add a step with auto-inferred properties
  volf --run <workflow>         Execute declared workflow DAG

Changes
  volf diff                     Review change sets attributed by agent
  volf apply                    Promote changes to workspace baseline
  volf commit -m <msg>          Commit to Git with RFC-5322 metadata trailers
  volf undo                     Instant physical snapshot rollback
  volf restore                  Restore from session checkpoint
```

---

## 0. Product Onboarding

```bash
volf auth              # Connect AI provider (OpenAI / Anthropic / local). Needed only for AI repair.
volf doctor            # Readiness: GitHub, AI, Indexed, Knowledge Base, Test command, Monitoring
volf index .           # Zero-token static index → .volf/graph.json + knowledge test recipes
volf check .           # Read-only drift & impact audit (works with no AI key configured)
volf fix .             # Auto-detect provider, repair, sandbox-verify, report evidence
```

`check` never modifies code. `fix` with no safe path and no AI credentials refuses loudly
(`NOT RUN … REFUSED / INCOMPLETE`, zero files touched) instead of faking success.

---

## 1. Workspace Commands (legacy path)

> `init` is the legacy workspace path. Normal onboarding (`auth → index → check → fix`) does not need it.

### `volf init`
Initializes a `.volf/` control plane in the current directory:
- Detects installed agents (`claude`, `codex`, `opencode`, `cursor`, `aider`).
- Configures default security compartments (`default`, `research`, `builder`, `network`, `tester`).
- Sets up execution tracking and BLAKE3 snapshot storage.

```bash
volf init
```

---

### `volf status`
Shows live workspace health, active agents, recent executions, and security events.

```bash
volf status
```

---

### `volf inspect`
Dumps declarative topology, active compartments, filesystem permissions, and network policies.

```bash
volf inspect
volf inspect --json
```

---

## 2. Interactive Agent Execution

### Direct Agent Commands (`volf <agent>`)
Launch any interactive coding agent inside an isolated kernel sandbox with full native terminal TUI fidelity (colors, alternate screen, Ctrl+C, Ctrl+D, window resizing):

```bash
volf claude
volf opencode
volf codex
volf cursor
volf aider
```

**Under the Hood:**
1. Resolves genuine binary on system `PATH`.
2. Allocates a pseudo-terminal master/slave pair (`PtySupervisor`).
3. Takes a pre-execution BLAKE3 hash snapshot of the workspace.
4. Applies OS kernel sandboxing (Seatbelt on macOS / Landlock on Linux).
5. Captures file changes upon exit into `volf diff`.

---

### `volf exec`
Runs any arbitrary script, tool, or shell command inside an explicitly selected compartment:

```bash
# Run inside default compartment
volf exec -- python3 script.py

# Run inside 'research' (read-only filesystem, network allowed)
volf exec --compartment research -- python3 scraper.py

# Run inside 'builder' (read-write filesystem, network restricted)
volf exec --compartment builder -- pytest tests/
```

---

## 3. Agentic Workflows (Git-Style Pipelines)

### `volf -w <name>` (or `volf workflow create <name>`)
Creates a new workflow branch in `workflows/<name>.yaml` or `.volf/workflows/<name>.yaml`:

```bash
volf -w invoice-pipeline
```

---

### `volf step <workflow> <target>`
Adds steps to your workflow branch. Point Volf at an individual file, a command, or an entire directory:

```bash
# Add a single script with auto-inferred runner & compartment
volf step invoice-pipeline src/ocr.py

# Ingest an entire directory (scans and auto-chains scripts)
volf step invoice-pipeline src/

# Add a test or shell command
volf step invoice-pipeline "pytest tests/" --compartment tester
```

---

### `volf --run <workflow>` (or `volf run <workflow>`)
Executes the declared workflow DAG under kernel isolation:

```bash
volf --run invoice-pipeline
```

- Topologically sorts the execution graph.
- Executes each step in its designated compartment (`research`, `builder`, `tester`, `reviewer`).
- If an upstream step fails, downstream dependent steps are cleanly `SKIPPED` to prevent cascading data corruption. Independent branches continue running.

---

### `volf workflow show <workflow>`
Inspects and visualizes declared workflow DAG nodes, commands, and dependencies:

```bash
volf workflow show invoice-pipeline
```

---

## 4. Change Management & Git Provenance

### `volf diff`
Review change sets attributed by execution ID and agent name:

```bash
volf diff               # Show all execution change sets
volf diff --unapplied   # Only show pending changes not yet applied
volf diff --trailers    # View formatted RFC-5322 Git metadata trailers
```

---

### `volf apply`
Promotes an execution's recorded change set into the workspace baseline. Detects conflicts if another execution modified the same files.

```bash
volf apply                         # Apply all pending completed executions
volf apply --execution exec_101    # Apply a specific execution
volf apply --force                 # Apply even if changes overlap
```

---

### `volf commit`
Commits applied agent changes to Git, automatically embedding structured RFC-5322 metadata trailers for auditability and compliance:

```bash
volf commit -m "feat(auth): implement token verification"
```

*Commit will contain metadata trailers (per the [Agent Provenance Trailers spec](../SPEC.md)):*
```text
Agent-Origin: agent
Agent-Agent: claude
Agent-Execution: exec_1787082469762
Agent-Compartment: builder
Agent-Sandbox: clean
```

---

### `volf undo`
Physically restores the workspace to its exact state before the execution ran using the pre-execution BLAKE3 hash snapshot (restores in ~2 milliseconds):

```bash
volf undo                         # Undo latest execution
volf undo --execution exec_101    # Undo a specific execution
```

---

### `volf restore [session_id]`
Restores workspace files from an Agent Session snapshot checkpoint:

```bash
volf restore                       # Restores latest session checkpoint
volf restore sess_1787082470931    # Restores specific session checkpoint
```

---

## 5. External-Change Intelligence & Autonomous Maintenance

### `volf auth [--provider … --api-key …] [--status] [--clear]`
Connects a BYOK AI provider, saved to `~/.volf/credentials.json` (0600), with per-installation
scoping available. Credentials are required only when AI reasoning/generation is actually needed —
`index` and `check` work without them. `--status` shows the masked active provider.

### `volf doctor`
Prints product readiness: GitHub CONNECTED / NOT CONFIGURED, AI provider, repository Indexed state,
Knowledge Base READY / STALE / MISSING, detected test command, and monitoring ACTIVE / NOT ACTIVE,
with remediation hints.

### `volf index [path]`
Zero-token static index: AST callsites, manifests, dependency graph → `.volf/graph.json`, plus
`index_state.json` (commit SHA + mtimes) for incremental re-indexing and knowledge test recipes.

### `volf check [path]` (alias: `scan`, `audit`)
Day-0 external-change dependency audit and risk register. Scans manifests, lockfiles, and AST callsites to report at-risk, deprecated, or breaking external integrations:

```bash
volf check .
volf check . --format=github-issue    # Markdown for GitHub Issue
volf check . --format=json            # Machine-readable JSON risk register
volf check . --write-graph            # Persists .volf/graph.json
```

---

### `volf graph [path]`
Queries and inspects the repository's External-Change Dependency Graph (providers, contracts, manifest dependencies, wrapper clients, AST callsites, and active edges):

```bash
volf graph .
volf graph . --json
```

---

### `volf fix [root_dir]` (alias: `maintain`, `update`)
Executes an autonomous continuous maintenance cycle: Volf's AI reasons over the repository,
the change, and maintenance memory, then repairs with deterministic tools, formats with local tools
(`prettier`/`ruff`), runs repository tests, verifies zero blast radius, and reports evidence.
Verified patterns execute without model calls; novel work uses your provider; unsafe repairs are
refused loudly with zero files touched. There is no engine flag — strategy is internal:

```bash
volf fix .                       # Auto-detect provider from manifests
volf fix . --provider stripe
volf fix . --provider openai --from v3.28.0 --to v4.0.0
volf fix . --detect              # Detect installed API providers
volf fix . --show-pr             # Preview Developer Trust PR body
volf fix . --create-pr --repo owner/repo
```

### `volf consult [path] [--repo owner/repo]`
Same AI reasoning as `fix` — codebase context, change context, maintenance memory, impact
analysis — but Consult authority: assess and report only. Files a GitHub Issue with findings,
affected files, inheritance notes, recommendation, and confidence, then declares no code was
modified. Requires AI credentials (refuses loudly without them); requires a resolvable repo
to file the Issue. Start here to build trust before enabling Work:

```bash
volf consult . --repo owner/repo
```

### `volf reviews [path]` / `volf onboard [path]` / `volf logout`
- `reviews` lists past maintenance runs (provider, versions, outcome) from `.volf/history.json`.
- `onboard` chains `auth → index → doctor` as one guided setup.
- `logout` clears stored credentials. `auth --status` also reports GitHub identity when a token is present.

On refusal (no safe path, no AI credentials): `Repository Tests: NOT RUN`, zero files modified,
`REFUSED / INCOMPLETE`. Tests are never reported PASSED unless they actually ran and exited 0.

---

### `volf providers`
Lists the built-in provider contract registry and available breaking-change migration specifications:

```bash
volf providers
volf providers --json
```

---

### `volf app [serve|status]`
Runs the GitHub App continuous webhook listener daemon for automated PR drift detection and verification.
A webhook secret is required (fail-closed); `--no-secret` is local-debugging only:

```bash
volf app serve --port 8080 --secret $VOLF_WEBHOOK_SECRET
```

On installation events Volf persists the installation record, runs Day-0 indexing where a
checkout is available, and tracks per-repository state (PENDING → INDEXED → READY).

### `volf pr [number]`
Runs the contract guard against a local checkout of a PR (mergeable only on real green tests).

