# Sheepdog CLI Reference & User Guide

Sheepdog is autonomous software maintenance for systems that change. It detects contract drift, repairs the code, verifies against your real test suite, and delivers the evidence as a PR.

> **“Sheepdog understands the changes the outside world makes to software — and repairs them.”**

---

## The Public CLI Contract

```text
Maintenance product (normal flow: auth → doctor → index → check → fix)
  sheepdog auth                     Connect BYOK AI provider (needed only for AI repair)
  sheepdog doctor                   Product readiness: GitHub, AI, index, knowledge, tests
  sheepdog index [path]             Index repository contracts & callsites (free, zero-token)
  sheepdog check [path]             Detect contract changes & impact (read-only; needs no AI key)
          sheepdog fix [path] [--provider]  Repair, verify in sandbox, report evidence (alias: maintain)
          sheepdog consult [path]         Assess with AI reasoning, file GitHub Issue, change nothing
          sheepdog reviews [path]         List past maintenance runs from the ledger
          sheepdog onboard [path]         Guided setup: auth → index → doctor
          sheepdog logout                 Remove stored credentials (alias for auth --clear)
  sheepdog providers                List monitored contract sources & migrations
  sheepdog app serve                Run GitHub App webhook listener (secret required)
  sheepdog pr                       Review a pull request with the contract guard

Legacy / advanced (workflows, sessions, lanes)
  sheepdog init                     Initialize a Sheepdog workspace (legacy path; onboarding no longer needs this)
  sheepdog status                   Show workspace health & active executions
  sheepdog inspect                  Dump declared compartments & policies

Agents
  sheepdog claude | opencode | codex | cursor | aider
                                   Run coding agent in governed OS sandbox
  sheepdog exec -- <cmd>            Run arbitrary command inside a compartment

Workflows
  sheepdog -w <name>                Create a new workflow branch
  sheepdog step <workflow> <target> Add a step with auto-inferred properties
  sheepdog --run <workflow>         Execute declared workflow DAG

Changes
  sheepdog diff                     Review change sets attributed by agent
  sheepdog apply                    Promote changes to workspace baseline
  sheepdog commit -m <msg>          Commit to Git with RFC-5322 metadata trailers
  sheepdog undo                     Instant physical snapshot rollback
  sheepdog restore                  Restore from session checkpoint
```

---

## 0. Product Onboarding

```bash
sheepdog auth              # Connect AI provider (OpenAI / Anthropic / local). Needed only for AI repair.
sheepdog doctor            # Readiness: GitHub, AI, Indexed, Knowledge Base, Test command, Monitoring
sheepdog index .           # Zero-token static index → .sheepdog/graph.json + knowledge test recipes
sheepdog check .           # Read-only drift & impact audit (works with no AI key configured)
sheepdog fix .             # Auto-detect provider, repair, sandbox-verify, report evidence
```

`check` never modifies code. `fix` with no safe path and no AI credentials refuses loudly
(`NOT RUN … REFUSED / INCOMPLETE`, zero files touched) instead of faking success.

---

## 1. Workspace Commands (legacy path)

> `init` is the legacy workspace path. Normal onboarding (`auth → index → check → fix`) does not need it.

### `sheepdog init`
Initializes a `.sheepdog/` control plane in the current directory:
- Detects installed agents (`claude`, `codex`, `opencode`, `cursor`, `aider`).
- Configures default security compartments (`default`, `research`, `builder`, `network`, `tester`).
- Sets up execution tracking and BLAKE3 snapshot storage.

```bash
sheepdog init
```

---

### `sheepdog status`
Shows live workspace health, active agents, recent executions, and security events.

```bash
sheepdog status
```

---

### `sheepdog inspect`
Dumps declarative topology, active compartments, filesystem permissions, and network policies.

```bash
sheepdog inspect
sheepdog inspect --json
```

---

## 2. Interactive Agent Execution

### Direct Agent Commands (`sheepdog <agent>`)
Launch any interactive coding agent inside an isolated kernel sandbox with full native terminal TUI fidelity (colors, alternate screen, Ctrl+C, Ctrl+D, window resizing):

```bash
sheepdog claude
sheepdog opencode
sheepdog codex
sheepdog cursor
sheepdog aider
```

**Under the Hood:**
1. Resolves genuine binary on system `PATH`.
2. Allocates a pseudo-terminal master/slave pair (`PtySupervisor`).
3. Takes a pre-execution BLAKE3 hash snapshot of the workspace.
4. Applies OS kernel sandboxing (Seatbelt on macOS / Landlock on Linux).
5. Captures file changes upon exit into `sheepdog diff`.

---

### `sheepdog exec`
Runs any arbitrary script, tool, or shell command inside an explicitly selected compartment:

```bash
# Run inside default compartment
sheepdog exec -- python3 script.py

# Run inside 'research' (read-only filesystem, network allowed)
sheepdog exec --compartment research -- python3 scraper.py

# Run inside 'builder' (read-write filesystem, network restricted)
sheepdog exec --compartment builder -- pytest tests/
```

---

## 3. Agentic Workflows (Git-Style Pipelines)

### `sheepdog -w <name>` (or `sheepdog workflow create <name>`)
Creates a new workflow branch in `workflows/<name>.yaml` or `.sheepdog/workflows/<name>.yaml`:

```bash
sheepdog -w invoice-pipeline
```

---

### `sheepdog step <workflow> <target>`
Adds steps to your workflow branch. Point Sheepdog at an individual file, a command, or an entire directory:

```bash
# Add a single script with auto-inferred runner & compartment
sheepdog step invoice-pipeline src/ocr.py

# Ingest an entire directory (scans and auto-chains scripts)
sheepdog step invoice-pipeline src/

# Add a test or shell command
sheepdog step invoice-pipeline "pytest tests/" --compartment tester
```

---

### `sheepdog --run <workflow>` (or `sheepdog run <workflow>`)
Executes the declared workflow DAG under kernel isolation:

```bash
sheepdog --run invoice-pipeline
```

- Topologically sorts the execution graph.
- Executes each step in its designated compartment (`research`, `builder`, `tester`, `reviewer`).
- If an upstream step fails, downstream dependent steps are cleanly `SKIPPED` to prevent cascading data corruption. Independent branches continue running.

---

### `sheepdog workflow show <workflow>`
Inspects and visualizes declared workflow DAG nodes, commands, and dependencies:

```bash
sheepdog workflow show invoice-pipeline
```

---

## 4. Change Management & Git Provenance

### `sheepdog diff`
Review change sets attributed by execution ID and agent name:

```bash
sheepdog diff               # Show all execution change sets
sheepdog diff --unapplied   # Only show pending changes not yet applied
sheepdog diff --trailers    # View formatted RFC-5322 Git metadata trailers
```

---

### `sheepdog apply`
Promotes an execution's recorded change set into the workspace baseline. Detects conflicts if another execution modified the same files.

```bash
sheepdog apply                         # Apply all pending completed executions
sheepdog apply --execution exec_101    # Apply a specific execution
sheepdog apply --force                 # Apply even if changes overlap
```

---

### `sheepdog commit`
Commits applied agent changes to Git, automatically embedding structured RFC-5322 metadata trailers for auditability and compliance:

```bash
sheepdog commit -m "feat(auth): implement token verification"
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

### `sheepdog undo`
Physically restores the workspace to its exact state before the execution ran using the pre-execution BLAKE3 hash snapshot (restores in ~2 milliseconds):

```bash
sheepdog undo                         # Undo latest execution
sheepdog undo --execution exec_101    # Undo a specific execution
```

---

### `sheepdog restore [session_id]`
Restores workspace files from an Agent Session snapshot checkpoint:

```bash
sheepdog restore                       # Restores latest session checkpoint
sheepdog restore sess_1787082470931    # Restores specific session checkpoint
```

---

## 5. External-Change Intelligence & Autonomous Maintenance

### `sheepdog auth [--provider … --api-key …] [--status] [--clear]`
Connects a BYOK AI provider, saved to `~/.sheepdog/credentials.json` (0600), with per-installation
scoping available. Credentials are required only when AI reasoning/generation is actually needed —
`index` and `check` work without them. `--status` shows the masked active provider.

### `sheepdog doctor`
Prints product readiness: GitHub CONNECTED / NOT CONFIGURED, AI provider, repository Indexed state,
Knowledge Base READY / STALE / MISSING, detected test command, and monitoring ACTIVE / NOT ACTIVE,
with remediation hints.

### `sheepdog index [path]`
Zero-token static index: AST callsites, manifests, dependency graph → `.sheepdog/graph.json`, plus
`index_state.json` (commit SHA + mtimes) for incremental re-indexing and knowledge test recipes.

### `sheepdog check [path]` (alias: `scan`, `audit`)
Day-0 external-change dependency audit and risk register. Scans manifests, lockfiles, and AST callsites to report at-risk, deprecated, or breaking external integrations:

```bash
sheepdog check .
sheepdog check . --format=github-issue    # Markdown for GitHub Issue
sheepdog check . --format=json            # Machine-readable JSON risk register
sheepdog check . --write-graph            # Persists .sheepdog/graph.json
```

---

### `sheepdog graph [path]`
Queries and inspects the repository's External-Change Dependency Graph (providers, contracts, manifest dependencies, wrapper clients, AST callsites, and active edges):

```bash
sheepdog graph .
sheepdog graph . --json
```

---

### `sheepdog fix [root_dir]` (alias: `maintain`, `update`)
Executes an autonomous continuous maintenance cycle: Sheepdog's AI reasons over the repository,
the change, and maintenance memory, then repairs with deterministic tools, formats with local tools
(`prettier`/`ruff`), runs repository tests, verifies zero blast radius, and reports evidence.
Verified patterns execute without model calls; novel work uses your provider; unsafe repairs are
refused loudly with zero files touched. There is no engine flag — strategy is internal:

```bash
sheepdog fix .                       # Auto-detect provider from manifests
sheepdog fix . --provider stripe
sheepdog fix . --provider openai --from v3.28.0 --to v4.0.0
sheepdog fix . --detect              # Detect installed API providers
sheepdog fix . --show-pr             # Preview Developer Trust PR body
sheepdog fix . --create-pr --repo owner/repo
```

### `sheepdog consult [path] [--repo owner/repo]`
Same AI reasoning as `fix` — codebase context, change context, maintenance memory, impact
analysis — but Consult authority: assess and report only. Files a GitHub Issue with findings,
affected files, inheritance notes, recommendation, and confidence, then declares no code was
modified. Requires AI credentials (refuses loudly without them); requires a resolvable repo
to file the Issue. Start here to build trust before enabling Work:

```bash
sheepdog consult . --repo owner/repo
```

### `sheepdog reviews [path]` / `sheepdog onboard [path]` / `sheepdog logout`
- `reviews` lists past maintenance runs (provider, versions, outcome) from `.sheepdog/history.json`.
- `onboard` chains `auth → index → doctor` as one guided setup.
- `logout` clears stored credentials. `auth --status` also reports GitHub identity when a token is present.

On refusal (no safe path, no AI credentials): `Repository Tests: NOT RUN`, zero files modified,
`REFUSED / INCOMPLETE`. Tests are never reported PASSED unless they actually ran and exited 0.

---

### `sheepdog providers`
Lists the built-in provider contract registry and available breaking-change migration specifications:

```bash
sheepdog providers
sheepdog providers --json
```

---

### `sheepdog app [serve|status]`
Runs the GitHub App continuous webhook listener daemon for automated PR drift detection and verification.
A webhook secret is required (fail-closed); `--no-secret` is local-debugging only:

```bash
sheepdog app serve --port 8080 --secret $SHEEPDOG_WEBHOOK_SECRET
```

On installation events Sheepdog persists the installation record, runs Day-0 indexing where a
checkout is available, and tracks per-repository state (PENDING → INDEXED → READY).

### `sheepdog pr [number]`
Runs the contract guard against a local checkout of a PR (mergeable only on real green tests).

