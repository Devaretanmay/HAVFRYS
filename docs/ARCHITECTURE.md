# Compart Architecture: Maintenance Layer for Systems That Change

> **Compart keeps software working when the systems around it change.**

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
      COMPART CHANGE RADAR (detect_changes: read-only, zero-token)
               ▼
      REPOSITORY KNOWLEDGE (.compart/: graph, index_state, knowledge/)
               ▼
      IMPACT ANALYSIS (ChangeSource-aware callsites + wrappers)
               ▼
      DECISION ENGINE (CompartIntelligence — internal only)
        ↙               ↘
   DIRECT (0 tokens)   AI (customer BYOK provider)
        ↘               ↙  (HYBRID: direct pre-pass + AI repair of failures)
              PATCH
               ▼
      SANDBOX / REAL TESTS (fail closed — no suite means never merge-ready)
               ▼
         GREEN → EVIDENCE (BLAKE3) → PR
               ▼
      KNOWLEDGE CAPTURE (verified patterns only; failures quarantined separately)
```

## 2. Core types

| Type | Module | Role |
|---|---|---|
| `ChangeSource` | `compart.change_source` | Names the depended-upon system: `kind` (`sdk`, `external_api`, `openapi`, `graphql`, `protobuf`, `webhook`, `mcp_server`, `internal_service`), `identity`, versions or `contract_hash` |
| `Detection` | `compart.change_source` | Read-only outcome: `NO_IMPACT`, `IMPACT_DIRECT`, `IMPACT_AI`, `IMPACT_QUARANTINE` (+ `ai_dependent` flag for checks needing reasoning) |
| `Decision` | `compart.intelligence` | Internal routing: `DIRECT / AI / HYBRID / QUARANTINE` + `confidence`, `estimated_tokens` (`0` = verified zero-token, `None` = unknown), `expected_blast_radius`, `verification_required`. Never a CLI flag |
| `KBEntry` | `compart.knowledge` | Repository memory at `.compart/knowledge/{kind}/{identity}/{contract}.json` (legacy provider paths still read). Executable patterns + test recipes + evidence + quarantined `failed_patterns` |

## 3. State on disk (per repository)

```text
.compart/
  graph.json            Full dependency graph (Rust AST engine, zero-token)
  index_state.json      commit SHA + file mtimes + discovery counts (incremental re-index)
  knowledge/            Verified repair patterns + test recipes (the flywheel)
  history.json          Auditable migration ledger
  snapshots/            Pre-execution BLAKE3 snapshots for rollback
```

Per installation (host side, `~/.compart/installations/{id}.json`, 0600):
repositories with `PENDING → INDEXED → READY`, provider association, index timestamps.

## 4. Trust rules (non-negotiable)

- No real test suite = never merge-ready.
- Tests are reported PASSED only with a real command, real exit 0. Refusals print NOT RUN.
- No `exit 0` fallbacks, no default-pass counters, no fake badges.
- Unverified AI guesses never enter trusted knowledge.
- Webhook serving without a secret is a hard error.
- Secrets never enter repo state, logs, or knowledge.

## 5. Deliberately not built yet

Connectors for OpenAPI/GraphQL/protobuf/MCP/internal-service kinds (types exist, resolution returns `None` → quarantine/AI), multi-repository fan-out orchestration, hosted background monitoring daemon, web dashboard beyond `compart doctor`. Seams are defined; products wait for users.
