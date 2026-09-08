# Volf Workspace Initialization & Agent Execution

## 1. What It Is

When you run `volf init`, Volf turns your project directory into a **managed agent workspace**. You launch your favorite agent directly inside an isolated kernel sandbox.

---

## 2. How It Works

```text
volf init
└── creates .volf/
    ├── config.yaml    <- workspace compartment policy
    ├── state/         <- runtime state
    ├── snapshots/     <- BLAKE3 worktree diff snapshots
    └── executions/    <- execution records

Direct Execution:
  $ volf claude      -> Launches Claude Code in kernel sandbox
  $ volf opencode    -> Launches OpenCode in kernel sandbox
  $ volf codex       -> Launches Codex in kernel sandbox
  $ volf cursor      -> Launches Cursor in kernel sandbox
  $ volf aider       -> Launches Aider in kernel sandbox
```

---

## 3. Running Interactive Coding Agents

```bash
volf claude
volf opencode
volf codex
volf cursor
volf aider
```

Each interactive agent runs with:
- Full native TUI support (colors, alternate screen, Ctrl+C, Ctrl+D, window resize).
- Hard OS-level kernel isolation (Seatbelt on macOS / Landlock on Linux).
- Deny-by-default credential protection (`~/.ssh`, `~/.aws`, `~/.config/gcloud` blocked).
- Automatic BLAKE3 pre-execution snapshots for physical instant rollback (`volf undo`).

---

## 4. Checking Workspace Health

```bash
volf status
```

```text
VOLF WORKSPACE: billing-service

AGENTS RUNNING
  none

RECENT SESSIONS
  [OK] Claude       lane:default_lane 1 change(s)  (0.5s)

SECURITY
  0 blocked action(s)
  0 credential escapes
```

---

## 5. Running Multi-Agent Workflows

Run a declared workflow DAG:

```bash
volf --run invoice-pipeline
```

Or run standalone Python agent scripts:

```bash
volf exec --compartment research -- python3 scraper.py
```
