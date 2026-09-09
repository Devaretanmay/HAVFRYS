# Koyote Architecture: Maintenance Layer for Systems That Change

> **Koyote keeps software working when the systems around it change.**

The wedge is vendor SDK/API migrations. The architecture is a general contract-maintenance
loop: any machine-readable interface a repository depends on is a `ChangeSource`, and every
change flows through detect → decide → verify → learn.

---

## 1. The loop

```text
WEBHOOK EVENT (PR opened / synchronized / @howl / @hunt)
│
▼
KOYOTE CHANGE RADAR (detect_changes: read-only, zero-token AST scan)
▼
┌────────────────────────┴────────────────────────┐
↓                                                 ↓
CODEBASE CONTEXT                              CHANGE CONTEXT
graph · callsites · wrappers · tests       ChangeSource · migration · changelog
│                                                 │
└────────────────────────┬────────────────────────┘
                         ▼
SEMANTIC KNOWLEDGE BASE (.koyote/knowledge/)
Ground truth verified patterns fed to prompt to minimize token burn
                         ▼
AI REASONING & GENERATION (Customer BYOK Provider)
The sole author of reviews, assessments, and code repairs
┌────────────────────────┴────────────────────────┐
↓                                                 ↓
HOWL (ADVISOR BOT)                            HUNT (WORKER BOT)
Read-only advisory review                     Surgical AI patch generation
Explains risk & files Issue / comment         Kernel sandbox + real test suite
Zero files touched                            Evidence (BLAKE3) & Trust PR
```

## 1b. The Two Distinct Bots: Howl vs Hunt

Instead of a monolithic reviewer, Koyote is split into two specialized bots:
- **Howl (The Advisor)**: Always read-only. Reviews incoming PRs and upstream contract changes, assesses architectural risk, answers `@howl explain` queries, and files advisory GitHub Issues. Never commits code or opens PRs.
- **Hunt (The Worker)**: The autonomous maintenance agent. Synthesizes surgical code repairs via the user's AI provider, tests inside the OS kernel sandbox (Linux Landlock / macOS Seatbelt), and delivers verified, merge-ready pull requests with BLAKE3 cryptographic receipts.

## 2. Core types

| Type | Module | Role |
|---|---|---|
| `ChangeSource` | `koyote.change_source` | Names the depended-upon system: `kind` (`sdk`, `external_api`, `openapi`, `graphql`, `protobuf`, `webhook`, `mcp_server`, `internal_service`), `identity`, versions or `contract_hash` |
| `Detection` | `koyote.change_source` | Read-only outcome: `NO_IMPACT`, `IMPACT_DIRECT`, `IMPACT_AI`, `IMPACT_QUARANTINE` (+ `ai_dependent` flag for checks needing reasoning) |
| `Decision` | `koyote.intelligence` | Internal routing: `DIRECT / AI / HYBRID / QUARANTINE` + `confidence`, `estimated_tokens` (`0` = verified zero-token, `None` = unknown), `expected_blast_radius`, `verification_required`. Never a CLI flag |
| `KBEntry` | `koyote.knowledge` | Repository memory at `.koyote/knowledge/{kind}/{identity}/{contract}.json` (legacy provider paths still read). Executable patterns + test recipes + evidence + quarantined `failed_patterns` |

## 3. State on disk (per repository)

```text
.koyote/
  graph.json            Full dependency graph (Rust AST engine, zero-token)
  index_state.json      commit SHA + file mtimes + discovery counts (incremental re-index)
  knowledge/            Verified repair patterns + test recipes (the flywheel)
  history.json          Auditable migration ledger
  snapshots/            Pre-execution BLAKE3 snapshots for rollback
```

Per installation (host side, `~/.koyote/installations/{id}.json`, 0600):
repositories with `PENDING → INDEXED → READY`, provider association, index timestamps.

## 4. Trust rules (non-negotiable)

- No real test suite = never merge-ready.
- Tests are reported PASSED only with a real command, real exit 0. Refusals print NOT RUN.
- No `exit 0` fallbacks, no default-pass counters, no fake badges.
- Unverified AI guesses never enter trusted knowledge.
- Webhook serving without a secret is a hard error.
- Secrets never enter repo state, logs, or knowledge.
- Koyote never cries wolf: no alert, badge, or pass is ever issued without the execution behind it.

## 5. Deliberately not built yet

Connectors for OpenAPI/GraphQL/protobuf/MCP/internal-service kinds (types exist, resolution returns `None` → quarantine/AI), multi-repository fan-out orchestration, hosted background monitoring daemon, web dashboard beyond `koyote doctor`. Seams are defined; products wait for users.
