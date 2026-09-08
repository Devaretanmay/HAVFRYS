<div align="center">

# Compart

### External-change intelligence for codebases.

**Greptile understands changes humans make to software. Compart understands changes the outside world makes to software.**

[PyPI Package](https://pypi.org/project/compart/) | [Quickstart](docs/QUICKSTART.md) | [CLI Reference](docs/CLI.md) | [Architecture](docs/ARCHITECTURE.md) | [Validation Guide](docs/VALIDATION_GUIDE.md)

<br/>

```text
   APIs drift. SDKs break.
   Compart keeps your codebase continuously updated and verified.
```

</div>

---

## The Problem

Software changes in two ways:
1. **Internal changes**: Features and fixes written by your team (handled by code review and CI).
2. **External changes**: Upstream API contract drift, major SDK breaking bumps, deprecated endpoints, and security migrations.

Dependabot bumps version strings in lockfiles and leaves CI broken. Human engineers spend 20%+ of engineering cycles reading migration guides, mapping AST callsites, updating wrappers, and fixing broken tests.

**Compart manages software changes originating outside the repository** — mapping external contracts to internal callsites, synthesizing surgical AST patches, running local formatters, and verifying zero blast radius with sandbox isolation.

---

## The Core Loop

```text
Install GitHub App → Select repo → Connect AI → Automatic index → READY
        ↓
Check / background detection (free, zero-token, no AI key needed)
        ↓
AI reasons over codebase + change + maintenance memory; deterministic tools execute
        ↓
Sandbox + real tests → Evidence → GitHub PR → Knowledge capture (next run is cheaper)
```

```bash
compart auth              # BYOK provider — needed only for AI repair
compart doctor            # GitHub / AI / Indexed / Knowledge / Tests / Monitoring
compart index .           # Zero-token static index
compart check .           # Read-only drift & impact audit
compart fix .             # Repair, verify, report (refuses loudly when unsafe)
```

## The Core Pipeline

```text
┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
│ 1. Change Detection     │ 2. Dependency Graph     │ 3. Impact Analysis      │
│    Contract drift       │    Source → Callsite    │    ChangeSource-aware   │
├─────────────────────────┼─────────────────────────┼─────────────────────────┤
│ 4. AI-Guided Repair     │ 5. Controlled Execution │ 6. Developer Trust PR   │
│    Reasoned, then applied │    Sandboxed + Evidence │    Verified merge-ready │
└─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

---

## 1. Day-0 Risk Register (`compart check`)

When you run Compart on any repository, it immediately answers:
- *What external APIs and SDKs does this codebase depend on?*
- *Which integrations are deprecated, behind, or at risk?*
- *Which breaking changes can Compart already auto-repair?*

```bash
compart check .
```

```text
================================================================================
         COMPART: EXTERNAL-CHANGE DEPENDENCY AUDIT & RISK REGISTER
================================================================================
Total External Providers Detected: 3
Total AST Callsites Mapped:        14
Auto-Repairable Callsites:         6
--------------------------------------------------------------------------------
[CRITICAL] AT RISK (Action Required):
  * Stripe (stripe@v21.0.0 -> v22.0.0)
    - Status: Breaking parameter mutation detected (amount: number -> string)
    - 4 callsites affected (4 auto-repairable by Compart)

[WATCHLIST] UPCOMING DEPRECATION:
  * OpenAI (openai@v3.28.0)
    - Status: Deprecated client interface (v4 migration available)
    - 6 callsites affected

[HEALTHY] UP-TO-DATE INTEGRATIONS:
  * Anthropic (@anthropic-ai/sdk@v0.25.0)
    - Status: Up-to-date with active provider contract (4 callsites mapped)
================================================================================
```

Export directly to GitHub Issues or JSON:
```bash
compart check . --format=github-issue   # Formatted markdown table for GitHub Issues
compart check . --format=json           # Machine-readable risk register
```

---

## 2. External-Change Dependency Graph (`compart graph`)

Compart builds a unified dependency graph linking:
`Provider -> Version -> API Contract -> Manifest Dependency -> Wrapper Client -> AST Callsite -> Migration History`

```bash
compart graph .
```

```text
================================================================================
                 COMPART: EXTERNAL-CHANGE DEPENDENCY GRAPH                     
================================================================================
Repository:              /path/to/my-repo
Providers Ingested:      3
Contracts Modeled:       6
Manifest Dependencies:   4
Wrapper Clients Found:   2
AST Callsites Mapped:    14
Active Graph Edges:      28
================================================================================
  [Wrapper] src/lib/stripe.ts -> wraps stripe
  [Callsite] src/billing.ts:12 -> stripe.charges.create
  [Callsite] src/checkout.ts:45 -> stripe.paymentIntents.create
================================================================================
```

---

## 3. Autonomous Continuous Maintenance (`compart fix`)

When upstream providers release breaking changes, Compart detects the drift, synthesizes surgical AST transformations, matches your team's code formatting (`prettier`/`ruff`), validates local tests, and opens a Developer Trust PR:

```bash
# Autonomous migration for a target provider:
compart fix . --provider stripe

# Custom version bump:
compart fix . --provider openai --from v3.28.0 --to v4.0.0 --create-pr --repo owner/repo
```

### What `compart fix` guarantees:
1. **Surgical AST Patching**: Only transforms affected callsites and wrappers.
2. **Local Formatter Bridge**: Formats changed files with your project's `prettier`, `ruff`, or `biome`.
3. **Local Test Verification**: Executes test suites and rejects patches if tests remain red.
4. **Zero Blast Radius**: Verifies that 0 unintended files were modified.
5. **Developer Trust PR**: Generates audit-grade PR markdown containing primary sources, exact callsites, test receipts, and rollback hashes.

---

## 4. Controlled Execution & Sandboxed Verification

Compart provides **controlled, reproducible execution** across local kernel sandboxes (macOS Seatbelt, Linux Landlock), Docker, and CI runners:
- **Zero-Exfiltration Isolation**: Credentials (`~/.ssh`, `~/.aws`, keychains) denied at the kernel boundary.
- **Execution-Evidence Compression**: Native Rust engines distill massive test outputs down to high-signal failure traces and stack traces for PR evidence.
- **2ms Instant Undo**: Pre-execution BLAKE3 hash snapshots enable physical rollback of modified and generated files in 2 milliseconds.

```bash
compart init                          # Initialize workspace control plane
compart diff                          # Inspect isolated execution change sets
compart undo                          # Instant 2ms physical rollback
```

---

## Python SDK

```python
from compart.graph import build_dependency_graph, audit_dependency_graph
from compart.maintenance import run_maintenance_cycle

# 1. Audit repository external dependencies
summary = audit_dependency_graph(repo_root=".")
print(f"At Risk: {len(summary['at_risk'])}, Auto-Repairable: {summary['total_auto_repairable']}")

# 2. Run autonomous maintenance cycle
report = run_maintenance_cycle(
    repo_dir=".",
    provider_name="stripe",
    create_pr=False,
)
print(f"Maintenance Outcome: {'GREEN' if report.success else 'REFUSED'}")
print(report.unified_diff)
```

---

## Documentation

[Quickstart Guide](docs/QUICKSTART.md) · [CLI Reference](docs/CLI.md) · [Architecture](docs/ARCHITECTURE.md) · [API Reference](docs/API_REFERENCE.md) · [Validation Guide](docs/VALIDATION_GUIDE.md) · [Agent Governance & Trailers](SPEC.md)

The core abstraction is `ChangeSource` (external API, SDK, OpenAPI, GraphQL, protobuf, webhook,
MCP server, internal service): Compart keeps software working when the systems around it change.
Vendor SDK migrations are the working wedge; other contract kinds are representable types with no
connectors yet — they fail closed to quarantine instead of guessing.

Under the hood, Compart is an AI maintenance agent with deterministic tools: a code graph,
repository memory, verified rewrite patterns, sandbox execution, and a fail-closed verifier.
Repeated work reuses verified knowledge instead of re-reasoning, so the system gets faster,
cheaper, and more precise the longer it watches a repository.

## Compart vs Greptile

| | Greptile | Compart |
|---|---|---|
| AI understands | Codebase + PR | Codebase + system change |
| Starting event | PR / code change | Dependency / contract change |
| AI asks | Is this change correct? | What does this change break? |
| AI output | Review / fix | Repair |
| Memory | Repository knowledge | Repository + maintenance history |
| Verification | Tests / validation | Tests + repair evidence |
| End result | Safe code change | Working software after ecosystem change |

Greptile gives an AI agent context about your code. Compart gives an AI agent context
about how your software changes.

## License

Apache-2.0. Copyright 2026 Compart Authors.

