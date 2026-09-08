# Compart CLI Reference & User Guide

Compart is autonomous software maintenance for systems that change. It detects contract drift, repairs the code, verifies against your real test suite, and delivers the evidence as a PR.

> **“Greptile understands changes humans make to software. Compart understands changes the outside world makes to software.”**

---

## The Public CLI Contract

```text
Maintenance product (normal flow: auth → doctor → index → check → fix)
  compart auth                     Connect BYOK AI provider (needed only for AI repair)
  compart doctor                   Product readiness: GitHub, AI, index, knowledge, tests
  compart index [path]             Index repository contracts & callsites (free, zero-token)
  compart check [path]             Detect contract changes & impact (read-only; needs no AI key)
          compart fix [path] [--provider]  Repair, verify in sandbox, report evidence (alias: maintain)
          compart consult [path]         Assess with AI reasoning, file GitHub Issue, change nothing
  compart providers                List monitored contract sources & migrations
  compart app serve                Run GitHub App webhook listener (secret required)
  compart pr                       Review a pull request with the contract guard

Legacy / advanced (workflows, sessions, lanes)
  compart init                     Initialize a Compart workspace (legacy path; onboarding no longer needs this)
  compart status                   Show workspace health & active executions
  compart inspect                  Dump declared compartments & policies

Agents
  compart claude | opencode | codex | cursor | aider
                                   Run coding agent in governed OS sandbox
  compart exec -- <cmd>            Run arbitrary command inside a compartment

Workflows
  compart -w <name>                Create a new workflow branch
  compart step <workflow> <target> Add a step with auto-inferred properties
  compart --run <workflow>         Execute declared workflow DAG

Changes
  compart diff                     Review change sets attributed by agent
  compart apply                    Promote changes to workspace baseline
  compart commit -m <msg>          Commit to Git with RFC-5322 metadata trailers
  compart undo                     Instant physical snapshot rollback
  compart restore                  Restore from session checkpoint
```

---

## 0. Product Onboarding

```bash
compart auth              # Connect AI provider (OpenAI / Anthropic / local). Needed only for AI repair.
compart doctor            # Readiness: GitHub, AI, Indexed, Knowledge Base, Test command, Monitoring
compart index .           # Zero-token static index → .compart/graph.json + knowledge test recipes
compart check .           # Read-only drift & impact audit (works with no AI key configured)
compart fix .             # Auto-detect provider, repair, sandbox-verify, report evidence
```

`check` never modifies code. `fix` with no safe path and no AI credentials refuses loudly
(`NOT RUN … REFUSED / INCOMPLETE`, zero files touched) instead of faking success.

---

## 1. Workspace Commands (legacy path)

> `init` is the legacy workspace path. Normal onboarding (`auth → index → check → fix`) does not need it.

### `compart init`
Initializes a `.compart/` control plane in the current directory:
- Detects installed agents (`claude`, `codex`, `opencode`, `cursor`, `aider`).
- Configures default security compartments (`default`, `research`, `builder`, `network`, `tester`).
- Sets up execution tracking and BLAKE3 snapshot storage.

```bash
compart init
```

---

### `compart status`
Shows live workspace health, active agents, recent executions, and security events.

```bash
compart status
```

---

### `compart inspect`
Dumps declarative topology, active compartments, filesystem permissions, and network policies.

```bash
compart inspect
compart inspect --json
```

---

## 2. Interactive Agent Execution

### Direct Agent Commands (`compart <agent>`)
Launch any interactive coding agent inside an isolated kernel sandbox with full native terminal TUI fidelity (colors, alternate screen, Ctrl+C, Ctrl+D, window resizing):

```bash
compart claude
compart opencode
compart codex
compart cursor
compart aider
```

**Under the Hood:**
1. Resolves genuine binary on system `PATH`.
2. Allocates a pseudo-terminal master/slave pair (`PtySupervisor`).
3. Takes a pre-execution BLAKE3 hash snapshot of the workspace.
4. Applies OS kernel sandboxing (Seatbelt on macOS / Landlock on Linux).
5. Captures file changes upon exit into `compart diff`.

---

### `compart exec`
Runs any arbitrary script, tool, or shell command inside an explicitly selected compartment:

```bash
# Run inside default compartment
compart exec -- python3 script.py

# Run inside 'research' (read-only filesystem, network allowed)
compart exec --compartment research -- python3 scraper.py

# Run inside 'builder' (read-write filesystem, network restricted)
compart exec --compartment builder -- pytest tests/
```

---

## 3. Agentic Workflows (Git-Style Pipelines)

### `compart -w <name>` (or `compart workflow create <name>`)
Creates a new workflow branch in `workflows/<name>.yaml` or `.compart/workflows/<name>.yaml`:

```bash
compart -w invoice-pipeline
```

---

### `compart step <workflow> <target>`
Adds steps to your workflow branch. Point Compart at an individual file, a command, or an entire directory:

```bash
# Add a single script with auto-inferred runner & compartment
compart step invoice-pipeline src/ocr.py

# Ingest an entire directory (scans and auto-chains scripts)
compart step invoice-pipeline src/

# Add a test or shell command
compart step invoice-pipeline "pytest tests/" --compartment tester
```

---

### `compart --run <workflow>` (or `compart run <workflow>`)
Executes the declared workflow DAG under kernel isolation:

```bash
compart --run invoice-pipeline
```

- Topologically sorts the execution graph.
- Executes each step in its designated compartment (`research`, `builder`, `tester`, `reviewer`).
- If an upstream step fails, downstream dependent steps are cleanly `SKIPPED` to prevent cascading data corruption. Independent branches continue running.

---

### `compart workflow show <workflow>`
Inspects and visualizes declared workflow DAG nodes, commands, and dependencies:

```bash
compart workflow show invoice-pipeline
```

---

## 4. Change Management & Git Provenance

### `compart diff`
Review change sets attributed by execution ID and agent name:

```bash
compart diff               # Show all execution change sets
compart diff --unapplied   # Only show pending changes not yet applied
compart diff --trailers    # View formatted RFC-5322 Git metadata trailers
```

---

### `compart apply`
Promotes an execution's recorded change set into the workspace baseline. Detects conflicts if another execution modified the same files.

```bash
compart apply                         # Apply all pending completed executions
compart apply --execution exec_101    # Apply a specific execution
compart apply --force                 # Apply even if changes overlap
```

---

### `compart commit`
Commits applied agent changes to Git, automatically embedding structured RFC-5322 metadata trailers for auditability and compliance:

```bash
compart commit -m "feat(auth): implement token verification"
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

### `compart undo`
Physically restores the workspace to its exact state before the execution ran using the pre-execution BLAKE3 hash snapshot (restores in ~2 milliseconds):

```bash
compart undo                         # Undo latest execution
compart undo --execution exec_101    # Undo a specific execution
```

---

### `compart restore [session_id]`
Restores workspace files from an Agent Session snapshot checkpoint:

```bash
compart restore                       # Restores latest session checkpoint
compart restore sess_1787082470931    # Restores specific session checkpoint
```

---

## 5. External-Change Intelligence & Autonomous Maintenance

### `compart auth [--provider … --api-key …] [--status] [--clear]`
Connects a BYOK AI provider, saved to `~/.compart/credentials.json` (0600), with per-installation
scoping available. Credentials are required only when AI reasoning/generation is actually needed —
`index` and `check` work without them. `--status` shows the masked active provider.

### `compart doctor`
Prints product readiness: GitHub CONNECTED / NOT CONFIGURED, AI provider, repository Indexed state,
Knowledge Base READY / STALE / MISSING, detected test command, and monitoring ACTIVE / NOT ACTIVE,
with remediation hints.

### `compart index [path]`
Zero-token static index: AST callsites, manifests, dependency graph → `.compart/graph.json`, plus
`index_state.json` (commit SHA + mtimes) for incremental re-indexing and knowledge test recipes.

### `compart check [path]` (alias: `scan`, `audit`)
Day-0 external-change dependency audit and risk register. Scans manifests, lockfiles, and AST callsites to report at-risk, deprecated, or breaking external integrations:

```bash
compart check .
compart check . --format=github-issue    # Markdown for GitHub Issue
compart check . --format=json            # Machine-readable JSON risk register
compart check . --write-graph            # Persists .compart/graph.json
```

---

### `compart graph [path]`
Queries and inspects the repository's External-Change Dependency Graph (providers, contracts, manifest dependencies, wrapper clients, AST callsites, and active edges):

```bash
compart graph .
compart graph . --json
```

---

### `compart fix [root_dir]` (alias: `maintain`, `update`)
Executes an autonomous continuous maintenance cycle: Compart's AI reasons over the repository,
the change, and maintenance memory, then repairs with deterministic tools, formats with local tools
(`prettier`/`ruff`), runs repository tests, verifies zero blast radius, and reports evidence.
Verified patterns execute without model calls; novel work uses your provider; unsafe repairs are
refused loudly with zero files touched. There is no engine flag — strategy is internal:

```bash
compart fix .                       # Auto-detect provider from manifests
compart fix . --provider stripe
compart fix . --provider openai --from v3.28.0 --to v4.0.0
compart fix . --detect              # Detect installed API providers
compart fix . --show-pr             # Preview Developer Trust PR body
compart fix . --create-pr --repo owner/repo
```

### `compart consult [path] [--repo owner/repo]`
Same AI reasoning as `fix` — codebase context, change context, maintenance memory, impact
analysis — but Consult authority: assess and report only. Files a GitHub Issue with findings,
affected files, inheritance notes, recommendation, and confidence, then declares no code was
modified. Requires AI credentials (refuses loudly without them); requires a resolvable repo
to file the Issue. Start here to build trust before enabling Work:

```bash
compart consult . --repo owner/repo
```

On refusal (no safe path, no AI credentials): `Repository Tests: NOT RUN`, zero files modified,
`REFUSED / INCOMPLETE`. Tests are never reported PASSED unless they actually ran and exited 0.

---

### `compart providers`
Lists the built-in provider contract registry and available breaking-change migration specifications:

```bash
compart providers
compart providers --json
```

---

### `compart app [serve|status]`
Runs the GitHub App continuous webhook listener daemon for automated PR drift detection and verification.
A webhook secret is required (fail-closed); `--no-secret` is local-debugging only:

```bash
compart app serve --port 8080 --secret $COMPART_WEBHOOK_SECRET
```

On installation events Compart persists the installation record, runs Day-0 indexing where a
checkout is available, and tracks per-repository state (PENDING → INDEXED → READY).

### `compart pr [number]`
Runs the contract guard against a local checkout of a PR (mergeable only on real green tests).

