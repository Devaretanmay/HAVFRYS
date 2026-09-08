<div align="center">

# Volf

### External-change intelligence for codebases.

**Volf understands the changes the outside world makes to software — and repairs them.**

[PyPI Package](https://pypi.org/project/volf/) | [Quickstart](docs/QUICKSTART.md) | [CLI Reference](docs/CLI.md) | [Architecture](docs/ARCHITECTURE.md) | [Validation Guide](docs/VALIDATION_GUIDE.md)

<br/>

```text
   APIs drift. SDKs break.
   Volf keeps your codebase continuously updated and verified.
```

</div>

---

## The Problem

Software changes in two ways:
1. **Internal changes**: Features and fixes written by your team (handled by code review and CI).
2. **External changes**: Upstream API contract drift, major SDK breaking bumps, deprecated endpoints, and security migrations.

Dependabot bumps version strings in lockfiles and leaves CI broken. Human engineers spend 20%+ of engineering cycles reading migration guides, mapping AST callsites, updating wrappers, and fixing broken tests.

**Volf manages software changes originating outside the repository** — mapping external contracts to internal callsites, synthesizing surgical AST patches, running local formatters, and verifying zero blast radius with sandbox isolation.

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
volf auth              # BYOK provider — needed only for AI repair
volf doctor            # GitHub / AI / Indexed / Knowledge / Tests / Monitoring
volf index .           # Zero-token static index
volf check .           # Read-only drift & impact audit
volf consult .         # AI assessment as a GitHub Issue, modifies nothing
volf fix .             # Repair, verify, report (refuses loudly when unsafe)
```

Start in Consult to build trust in the reasoning, enable Work when ready —
one engine, three voices: **Howl** hunts, **Shepherd** reports, **Shearer** repairs.
See [GitHub App behavior](docs/GITHUB_APP.md).

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

## 1. Day-0 Risk Register (`volf check`)

When you run Volf on any repository, it immediately answers:
- *What external APIs and SDKs does this codebase depend on?*
- *Which integrations are deprecated, behind, or at risk?*
- *Which breaking changes can Volf already auto-repair?*

```bash
volf check .
```

```text
================================================================================
         VOLF: EXTERNAL-CHANGE DEPENDENCY AUDIT & RISK REGISTER
================================================================================
Total External Providers Detected: 3
Total AST Callsites Mapped:        14
Auto-Repairable Callsites:         6
--------------------------------------------------------------------------------
[CRITICAL] AT RISK (Action Required):
  * Stripe (stripe@v21.0.0 -> v22.0.0)
    - Status: Breaking parameter mutation detected (amount: number -> string)
    - 4 callsites affected (4 auto-repairable by Volf)

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
volf check . --format=github-issue   # Formatted markdown table for GitHub Issues
volf check . --format=json           # Machine-readable risk register
```

---

## 2. External-Change Dependency Graph (`volf graph`)

Volf builds a unified dependency graph linking:
`Provider -> Version -> API Contract -> Manifest Dependency -> Wrapper Client -> AST Callsite -> Migration History`

```bash
volf graph .
```

```text
================================================================================
                 VOLF: EXTERNAL-CHANGE DEPENDENCY GRAPH                     
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

## 3. Autonomous Continuous Maintenance (`volf fix`)

When upstream providers release breaking changes, Volf detects the drift, synthesizes surgical AST transformations, matches your team's code formatting (`prettier`/`ruff`), validates local tests, and opens a Developer Trust PR:

```bash
# Autonomous migration for a target provider:
volf fix . --provider stripe

# Custom version bump:
volf fix . --provider openai --from v3.28.0 --to v4.0.0 --create-pr --repo owner/repo
```

### What `volf fix` guarantees:
1. **Surgical AST Patching**: Only transforms affected callsites and wrappers.
2. **Local Formatter Bridge**: Formats changed files with your project's `prettier`, `ruff`, or `biome`.
3. **Local Test Verification**: Executes test suites and rejects patches if tests remain red.
4. **Zero Blast Radius**: Verifies that 0 unintended files were modified.
5. **Developer Trust PR**: Generates audit-grade PR markdown containing primary sources, exact callsites, test receipts, and rollback hashes.

---

## 4. Controlled Execution & Sandboxed Verification

Volf provides **controlled, reproducible execution** across local kernel sandboxes (macOS Seatbelt, Linux Landlock), Docker, and CI runners:
- **Zero-Exfiltration Isolation**: Credentials (`~/.ssh`, `~/.aws`, keychains) denied at the kernel boundary.
- **Execution-Evidence Compression**: Native Rust engines distill massive test outputs down to high-signal failure traces and stack traces for PR evidence.
- **2ms Instant Undo**: Pre-execution BLAKE3 hash snapshots enable physical rollback of modified and generated files in 2 milliseconds.

```bash
volf init                          # Initialize workspace control plane
volf diff                          # Inspect isolated execution change sets
volf undo                          # Instant 2ms physical rollback
```

---

## Python SDK

```python
from volf.graph import build_dependency_graph, audit_dependency_graph
from volf.maintenance import run_maintenance_cycle

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
MCP server, internal service): Volf keeps software working when the systems around it change.
Vendor SDK migrations are the working wedge; other contract kinds are representable types with no
connectors yet — they fail closed to quarantine instead of guessing.

Under the hood, Volf is an AI maintenance agent with deterministic tools: a code graph,
repository memory, verified rewrite patterns, sandbox execution, and a fail-closed verifier.
Repeated work reuses verified knowledge instead of re-reasoning, so the system gets faster,
cheaper, and more precise the longer it watches a repository.

## Where Volf Fits

Conventional AI reviewers start from a human pull request and ask whether the change
is correct. Volf starts from the other end: a dependency or contract changed out
in the world, and it asks what that breaks in your repository. One AI reasons over
your codebase plus the change itself, backed by maintenance memory — past verified
repairs and quarantined failures. The output is not a review but a repair, proven
against your real test suite before it ever reaches a pull request.

Volf is not a generic coding agent, a PR reviewer, a Dependabot clone, a
codebase Q&A tool, or vulnerability-management software. It is autonomous
maintenance for systems that change.

The old fable got it backwards: the village stopped believing because the boy
cried wolf over nothing. Most automation still does — vague green checks,
unverified badges, silent passes. Volf only howls when there's actually
one in the fence: verified repairs, loud refusals, never a faked pass.

## License

Apache-2.0. Copyright 2026 Volf Authors.

