# Koyote Architecture: Maintenance Layer for Systems That Change

> **Koyote keeps software working when the systems around it change.**

The wedge is vendor SDK/API migrations. The architecture is a general contract-maintenance
loop: any machine-readable interface a repository depends on is a `ChangeSource`, and every
change flows through detect → decide → verify → learn.

---

## 1. The loop

```text
PUBLIC WORLD                          INTERNAL COMPANY SOFTWARE (future)
Stripe / OpenAI / AWS / MCP / APIs    Service A → API → Service B → SDK → MCP → Service C
│                                     │
└──────────────┬──────────────────────┘
               ▼
      KOYOTE CHANGE RADAR (detect_changes: read-only, zero-token)
               ▼
      ┌────────────────────────┴────────────────────────┐
      ↓                                                 ↓
CODEBASE CONTEXT                              CHANGE CONTEXT
graph · callsites · wrappers · tests       ChangeSource · migration · changelog
      │                                                 │
      └────────────────────────┬────────────────────────┘
                               ▼
                    AI REASONING (customer BYOK provider)
                    impact · scope · minimal repair plan
                               ▼
              DETERMINISTIC TOOLS (internal optimization)
              verified rewrites · KB patterns · SEARCH/REPLACE apply
                               ▼
              PATCH
                               ▼
      SANDBOX / REAL TESTS (fail closed — no suite means never merge-ready)
                               ▼
         GREEN → EVIDENCE (BLAKE3) → PR
                               ▼
      KNOWLEDGE CAPTURE (verified patterns only; failures quarantined separately)

Insufficient confidence at any stage → loud refusal, zero files touched.
The engine never asks the user to choose a strategy; `Decision`
(DIRECT / AI / HYBRID / QUARANTINE) is internal cost accounting, not product.

## 1b. Authority modes: Consult vs Work

One reasoning engine, two authorities. `Consult` runs the full pipeline through
impact reasoning, then files a GitHub Issue and stops — the worktree is never
touched. `Work` continues through repair, sandbox verification, and PR.
`BotConfig.mode` sets the default; the CLI (`consult` vs `fix`) overrides per run.
Adoption ladder: start in Consult, graduate to Work when the reasoning earns it.

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
