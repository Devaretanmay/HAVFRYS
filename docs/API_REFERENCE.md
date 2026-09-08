# Sheepdog API Reference & Documentation Map

**Version:** 1.0.4  
**Package:** `sheepdog` (PyPI)

---

## 1. Documentation Index

- **[Quickstart Guide](QUICKSTART.md)**: 2-minute quickstart guide for CLI and Python workflows.
- **[CLI Reference Guide](CLI.md)**: Complete guide to the frozen public CLI contract (`init`, `status`, `inspect`, `claude`, `opencode`, `codex`, `cursor`, `aider`, `exec`, `-w`, `step`, `--run`, `diff`, `apply`, `commit`, `undo`, `restore`).
- **[Agent Execution & TUI Supervision](AGENT_EXECUTION.md)**: Details on PTY terminal supervision, interactive coding agents, and kernel isolation.
- **[Framework Integration Hooks](FRAMEWORK_HOOKS.md)**: Drop-in sandboxing for LangGraph, LangChain, CrewAI, and AutoGen.
- **[Zero-Trust Credential Proxy](CREDENTIAL_PROXY.md)**: Safe API key injection and request routing without exposing raw secrets.
- **[BLAKE3 Snapshots & Rollback](SNAPSHOTS.md)**: Fast workspace hashing, diff tracking, and physical restoration with `sheepdog undo`.
- **[Output Compression & Token Crushing](COMPRESSION.md)**: High-speed Rust token reduction engines (`SmartCrusher`, `LogCompressor`, `DiffCompressor`).
- **[TypeScript & Node.js SDK](TYPESCRIPT_SDK.md)**: Native NAPI-RS bindings and TypeScript API reference.
- **[CI/CD Security Integration](CI_INTEGRATION.md)**: GitHub Actions and CI runner drop-in step isolation.
- **[Use Cases & Working Examples](USE_CASES.md)**: Practical security scenarios, prompt injection defense, and REPL sandboxing patterns.

---

## 2. Core Python SDK Classes

### `Sheepdog(workdir=".", config=None, verbose=False)`
Base compartment container for custom agent pipelines.
- `add(compartment: Compartment) -> Sheepdog`: Register an inner isolated compartment.
- `edge(from_name: str, to_name: str) -> Sheepdog`: Wire a directional dependency/communication path.
- `register_module(module_cls) -> Sheepdog`: Register an optional behavior module.
- `run(entry=None, request="") -> SheepdogResult`: Execute the topology under OS kernel isolation.

### `AgentSheepdog(workdir=".", config=None, verbose=False)`
Agent-oriented outer compartment container. Automatically loads standard behavior modules (Credential Proxy, Snapshots, Compression).

### `Compartment(name, fn=None, config=None)`
An individual unit of work executed in a specific kernel sandbox.
- `deliver(message: Message)`: Queue an inbound message.
- `receive() -> list[Message]`: Retrieve pending messages.
- `run(ctx: CompartmentContext)`: Execute compartment logic.

### `CompartmentConfig`
Configuration dataclass defining isolation rules:
- `permissions`: List of permissions (`"fs_read"`, `"fs_write"`, `"fs_exec"`, `"network"`).
- `filesystem`: Filesystem access mode (`"workspace"`, `"read-only"`, `"read-write"`, `"blocked"`).
- `network`: Network mode (`"allowed"`, `"restricted"`, `"blocked"`).
- `timeout_s`: Hard execution timeout in seconds.
- `allow_inbound_from`: Allowed source compartment names (`["*"]` for all).
- `allow_outbound_to`: Allowed target compartment names (`["*"]` for all).

### `RouteConfig`
Credential proxy routing rule:
- `prefix`: Path prefix to intercept (e.g. `"/openai"`).
- `upstream`: Target base URL (e.g. `"https://api.openai.com"`).
- `header`: Header name to inject (default `"Authorization"`).
- `format`: Format template (default `"Bearer {credential}"`).
- `credential_source`: Environment variable name (e.g. `"env:OPENAI_API_KEY"`).

### `SandboxRunner(workdir=".", verbose=False, block_network=False)`
Low-level process execution runner that applies kernel sandbox (Seatbelt / Landlock) to shell commands and captures file diffs.
- `run(command: str, permissions=None, env=None) -> ExecutionResult`

---

## 3. External-Change Intelligence & AutoPatch APIs

### `from sheepdog import autopatch`
- `plan_maintenance(old_spec: str, new_spec: str, repo_root: str = ".", config: ScanConfig = None) -> MaintenancePlan`: Generates breaking-change diff, scans callsites, and computes patch targets.
- `apply_patch(repo_root: str, plan: MaintenancePlan, dry_run: bool = False) -> List[PatchResult]`: Applies surgical AST transformations.
- `synthesize_contracts(api_name: str, old_ver: str, new_ver: str, specs: List[VerificationSpec], lang: str = "ts") -> str`: Synthesizes Vitest/pytest contract test suites.

### `from sheepdog.graph import build_dependency_graph, audit_dependency_graph`
- `build_dependency_graph(repo_root: str = ".") -> Dict[str, Any]`: Constructs the full External Dependency Graph across manifests, wrappers, and AST callsites.
- `audit_dependency_graph(repo_root: str = ".") -> Dict[str, Any]`: Generates structured audit summary (at-risk, watchlist, healthy).

### `from sheepdog.maintenance import run_maintenance_cycle, detect_drift`
- `detect_drift(repo_dir: str, provider_name: str) -> List[Dict[str, Any]]`: Scans for outdated external dependencies.
- `run_maintenance_cycle(repo_dir: str, provider_name: str, ...) -> MaintenanceReport`: Runs end-to-end drift detection, AST patching, formatting, test verification, and PR creation.

### `from sheepdog.maintenance_agents import AutonomousMaintenancePipeline, ChangeAnalyzer, ImpactAnalyst, PatchPlanner, PatchVerifier`
- `ChangeAnalyzer`: Analyzes vendor OpenAPI/SDK breaking contracts.
- `ImpactAnalyst`: Traces dependencies through wrappers to affected callsites. `analyze_impact_for(repo, source)` matches any `ChangeSource` identity against wrapper metadata, callsite patterns, and file paths; `analyze_impact(repo, provider)` is the preserved SDK branch.
- `PatchPlanner`: Synthesizes AST transformation plans.
- `PatchVerifier`: Runs sandboxed tests, compresses execution evidence logs, checks zero blast radius, and certifies merge readiness.
- `AutonomousMaintenancePipeline`: Coordinates the 4 specialized maintenance agents end-to-end.

---

## 4. Change Sources, Decisions, Knowledge & Installations

### `from sheepdog.change_source import ChangeSource, Detection`
- `ChangeSource(kind, identity, version_from, version_to, contract_hash, origin)`: kinds `external_api, sdk, openapi, graphql, protobuf, webhook, mcp_server, internal_service`. Helpers: `ChangeSource.sdk(provider, …)`, `.provider`, `.key()`.
- `Detection(source, outcome, reason, affected_files, callsite_count, ai_dependent, confidence)`: outcomes `NO_IMPACT / IMPACT_DIRECT / IMPACT_AI / IMPACT_QUARANTINE` (fail-closed).

### `from sheepdog.drift import detect_drift, detect_changes`
- `detect_changes(repo_dir, provider_name=None) -> List[Detection]`: read-only classification — never patches.

### `from sheepdog.intelligence import SheepdogIntelligence, Decision, resolve_migration`
- `Decision(strategy, reason, confidence, estimated_tokens, expected_blast_radius, verification_required)`: strategies `DIRECT / AI / HYBRID / REFUSE…QUARANTINE` are internal only (no CLI flag).
- `decide_for_source(repo_dir, source)`: routes any `ChangeSource`; kinds without registry connectors go AI-if-credentials else quarantine.

### `from sheepdog.providers.registry import find_migration_for`
- `find_migration_for(source) -> Optional[ProviderMigration]`: resolves `sdk`/`external_api` sources; all other kinds return `None` by design (no connectors yet).

### `from sheepdog.knowledge import lookup, upsert_learned, record_failure, ensure_test_recipe`
- Entries live at `.sheepdog/knowledge/{kind}/{identity}/{contract}.json` with legacy provider-path fallback reads. Only verified fixes upsert executable patterns; `record_failure()` quarantines guesses separately.

### `from sheepdog.github.installations import record_installation_event, set_repo_state, list_ready_repos`
- Flat-JSON install records (0600): repos tracked PENDING → INDEXED → READY.

### `from sheepdog.github.provisioning import ensure_repo_checkout, ensure_pr_checkout, resolve_pr_workdir`
- Managed clone/pull cache; exact PR-head checkout with `(path, exact)` honesty flag.

### `from sheepdog.github.watch import watch_once`
- Poll READY repos; run the pipeline only on new drift signatures.

### `from sheepdog.github.pr_render import render_consult_issue, render_pr_summary, render_flow_diagram`
- Consult Issue bodies, PR summary headers with evidence-grounded confidence, mermaid change→files→verification diagrams. Severity: P0 needs a human, P1 is repairable.

### `BotConfig.mode`
- `consult` (report only) or `work` (repair, default) in `.sheepdog/config.yaml`, plus `ignore_paths` / `exclude_labels` PR filters. See [GitHub App behavior](GITHUB_APP.md).

### `from sheepdog.credentials import save_credentials, load_credentials, has_valid_credentials`
- All accept optional `(installation_id, repo)` scope: env → scoped file → global file. Secrets never enter repo state, logs, or knowledge.

