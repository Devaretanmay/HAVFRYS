# Compart Quickstart Guide

Get up and running with Compart in under 2 minutes.

> **“Greptile understands changes humans make to software. Compart understands changes the outside world makes to software.”**

---

## 1. Installation

Install Compart via PyPI:

```bash
pip install --upgrade compart
```

---

## 2. Onboarding (no AI key required)

```bash
cd my-project

compart auth              # Connect AI provider — only needed when AI repair is required
compart doctor            # Readiness: GitHub, AI, Indexed, Knowledge Base, Tests, Monitoring
compart index .           # Zero-token static index of contracts & callsites
```

---

## 3. Day-0 Dependency Check & Risk Register

Immediately scan your codebase for breaking upstream changes, deprecated callsites, and auto-repairable integrations. Read-only — works with no AI credentials configured:

```bash
# Run terminal risk register:
compart check .

# Export as GitHub Issue markdown:
compart check . --format=github-issue

# Inspect the External-Change Dependency Graph:
compart graph .
```

---

## 4. Autonomous Continuous Maintenance

Run autonomous maintenance on external providers (e.g. Stripe, OpenAI, Anthropic, Clerk, AWS).
Compart's AI reasons about the change against your repository and repairs with deterministic tools —
there is no engine flag to choose. Unsafe repairs refuse loudly with zero files touched:

```bash
# Auto-detect provider and repair:
compart fix .

# Targeted migration and open PR:
compart fix . --provider stripe
compart fix . --provider openai --from v3.28.0 --to v4.0.0 --create-pr --repo owner/repo
```

---

## 5. Interactive Coding Agents & Sandboxed Governance (advanced)

Run terminal coding agents inside a kernel-enforced sandbox with full native TUI fidelity:

```bash
# Launch Claude Code, OpenCode, Codex, Cursor, or Aider directly:
compart claude

# When the agent finishes:
compart diff    # Review what the agent changed
compart undo    # Instantly restore files if the agent made a mistake
compart commit  # Commit to Git with verified provenance trailers
```

---

## 6. Key Guarantees

- **External Intelligence**: Full-codebase AST mapping of providers, contracts, wrappers, and callsites.
- **Continuous Maintenance**: Surgical AST patching with local formatter matching and automated Developer Trust PRs.
- **Kernel Enforcement**: Built on native OS isolation (macOS Seatbelt / Linux Landlock).
- **Credential Protection**: `~/.ssh`, `~/.aws`, `~/.config/gcloud`, git credentials, and keychains are denied by default.
- **Instant Rollback**: Hash-based BLAKE3 file snapshots allow physical restoration of modified and deleted files in 2ms.
- **Zero Infrastructure**: No Docker, no daemon, no cloud account required.
