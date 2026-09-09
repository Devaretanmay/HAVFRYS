# Koyote Quickstart Guide

Get up and running with Koyote in under 2 minutes.

> **“Koyote understands the changes the outside world makes to software — and repairs them.”**

---

## 1. Installation

From source (builds the native core, ~2 minutes, needs Rust + Python 3.10+):

```bash
git clone https://github.com/Devaretanmay/Koyote && cd Koyote
pip install .
```

`pip install koyote` from PyPI lands with the public beta — this page will
say so when it does.

---

## 2. Onboarding (no AI key required)

```bash
cd my-project

koyote auth              # Connect AI provider — only needed when AI repair is required
koyote doctor            # Readiness: GitHub, AI, Indexed, Knowledge Base, Tests, Monitoring
koyote index .           # Zero-token static index of contracts & callsites
```

---

## 3. Day-0 Dependency Check & Risk Register

Immediately scan your codebase for breaking upstream changes, deprecated callsites, and auto-repairable integrations. Read-only — works with no AI credentials configured:

```bash
# Run terminal risk register:
koyote check .

# Export as GitHub Issue markdown:
koyote check . --format=github-issue

# Inspect the External-Change Dependency Graph:
koyote graph .
```

---

## 4. Consult First, Then Work

New teams start in Consult: same AI reasoning, zero code changes, findings filed
as a GitHub Issue. Graduate to Work when the reasoning earns it.

```bash
koyote consult . --repo owner/repo   # Assess only, files an Issue
koyote fix .                         # Repair, verify, report
```

See [GitHub App behavior](GITHUB_APP.md) for modes, triggers, and bot config.

## 5. Autonomous Continuous Maintenance

Run autonomous maintenance on external providers (e.g. Stripe, OpenAI, Anthropic, Clerk, AWS).
Koyote's AI reasons about the change against your repository and repairs with deterministic tools —
there is no engine flag to choose. Unsafe repairs refuse loudly with zero files touched:

```bash
# Auto-detect provider and repair:
koyote fix .

# Targeted migration and open PR:
koyote fix . --provider stripe
koyote fix . --provider openai --from v3.28.0 --to v4.0.0 --create-pr --repo owner/repo
```

---

## 6. Interactive Coding Agents & Sandboxed Governance (advanced)

Run terminal coding agents inside a kernel-enforced sandbox with full native TUI fidelity:

```bash
# Launch Claude Code, OpenCode, Codex, Cursor, or Aider directly:
koyote claude

# When the agent finishes:
koyote diff    # Review what the agent changed
koyote undo    # Instantly restore files if the agent made a mistake
koyote commit  # Commit to Git with verified provenance trailers
```

---

## 7. Key Guarantees

- **External Intelligence**: Full-codebase AST mapping of providers, contracts, wrappers, and callsites.
- **Continuous Maintenance**: Surgical AST patching with local formatter matching and automated Developer Trust PRs.
- **Kernel Enforcement**: Built on native OS isolation (macOS Seatbelt / Linux Landlock).
- **Credential Protection**: `~/.ssh`, `~/.aws`, `~/.config/gcloud`, git credentials, and keychains are denied by default.
- **Instant Rollback**: Hash-based BLAKE3 file snapshots allow physical restoration of modified and deleted files in 2ms.
- **Zero Infrastructure**: No Docker, no daemon, no cloud account required.
