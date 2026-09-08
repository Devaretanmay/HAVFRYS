# Sheepdog Workspace Initialization & Agent Execution

## 1. What It Is

When you run `sheepdog init`, Sheepdog turns your project directory into a **managed agent workspace**. You launch your favorite agent directly inside an isolated kernel sandbox.

---

## 2. How It Works

```text
sheepdog init
└── creates .sheepdog/
    ├── config.yaml    <- workspace compartment policy
    ├── state/         <- runtime state
    ├── snapshots/     <- BLAKE3 worktree diff snapshots
    └── executions/    <- execution records

Direct Execution:
  $ sheepdog claude      -> Launches Claude Code in kernel sandbox
  $ sheepdog opencode    -> Launches OpenCode in kernel sandbox
  $ sheepdog codex       -> Launches Codex in kernel sandbox
  $ sheepdog cursor      -> Launches Cursor in kernel sandbox
  $ sheepdog aider       -> Launches Aider in kernel sandbox
```

---

## 3. Running Interactive Coding Agents

```bash
sheepdog claude
sheepdog opencode
sheepdog codex
sheepdog cursor
sheepdog aider
```

Each interactive agent runs with:
- Full native TUI support (colors, alternate screen, Ctrl+C, Ctrl+D, window resize).
- Hard OS-level kernel isolation (Seatbelt on macOS / Landlock on Linux).
- Deny-by-default credential protection (`~/.ssh`, `~/.aws`, `~/.config/gcloud` blocked).
- Automatic BLAKE3 pre-execution snapshots for physical instant rollback (`sheepdog undo`).

---

## 4. Checking Workspace Health

```bash
sheepdog status
```

```text
SHEEPDOG WORKSPACE: billing-service

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
sheepdog --run invoice-pipeline
```

Or run standalone Python agent scripts:

```bash
sheepdog exec --compartment research -- python3 scraper.py
```
