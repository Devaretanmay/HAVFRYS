
"""Continuous Autonomous API Maintenance Loop Engine."""

from dataclasses import dataclass, field
import json
import os
import subprocess
import time
from typing import Any, Dict, List, Optional

from compart.ai_planner import AIPatchPlanner
from compart.drift import detect_drift  # noqa: F401 — re-exported for CLI/SDK callers
from compart.formatters import run_style_formatter
from compart.github.trust_pr import generate_trust_pr_markdown, TrustPRMetadata
from compart.git_ops import git_commit_and_push, gh_create_pr
from compart.maintenance_agents import ImpactAnalyst
from compart.patch_writer import apply_rewrites, PatchResult
from compart.providers.registry import get_default_registry
from compart.sandbox.snapshot import SnapshotManager, _file_hash

from compart.intelligence import CompartIntelligence, resolve_migration
from compart.knowledge import direct_rewrites_for, upsert_learned as kb_upsert
from compart.test_runner import (
    _blake3_digest,
    _detect_test_command,
    _compute_lockfile_hash,
    _run_install,
    _run_tests,
)

@dataclass
class MaintenanceRunReport:
    success: bool
    provider_name: str
    from_version: str
    to_version: str
    repository_path: str
    files_scanned: int
    files_modified: int
    unintended_files_modified: int
    blast_radius_verified: bool
    test_exit_code: int
    test_duration_ms: int
    unified_diff: str
    trust_pr_body: str
    patch_results: List[PatchResult] = field(default_factory=list)
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    error: Optional[str] = None




def record_migration_history(repo_dir: str, record: Dict[str, Any]) -> None:
    """Record an auditable verified migration event into the repository history ledger."""
    history_dir = os.path.join(repo_dir, ".compart")
    os.makedirs(history_dir, exist_ok=True)
    history_file = os.path.join(history_dir, "history.json")

    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(record)
    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)


def get_migration_history(repo_dir: str) -> List[Dict[str, Any]]:
    """Retrieve verified migration history records from .compart/history.json."""
    history_file = os.path.join(repo_dir, ".compart", "history.json")
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def run_maintenance_cycle(
    repo_dir: str,
    provider_name: str,
    from_version: Optional[str] = None,
    to_version: Optional[str] = None,
    create_pr: bool = False,
    github_repo: Optional[str] = None,
    github_client: Any = None,
    llm_api_key: Optional[str] = None,
    llm_model: Optional[str] = None,
    llm_base_url: Optional[str] = None,
    **_ignored: Any,
) -> MaintenanceRunReport:
    """Execute full autonomous maintenance loop on a repository. Intelligence picks DIRECT vs AI."""
    repo_dir = os.path.abspath(repo_dir)
    registry = get_default_registry()
    p_spec = registry.get(provider_name)
    if not p_spec:
        return MaintenanceRunReport(
            success=False, provider_name=provider_name,
            from_version=from_version or "unknown", to_version=to_version or "unknown",
            repository_path=repo_dir, files_scanned=0, files_modified=0,
            unintended_files_modified=0, blast_radius_verified=False,
            test_exit_code=-1, test_duration_ms=0, unified_diff="",
            trust_pr_body="", error=f"Provider {provider_name} not found in registry",
        )

    actual_from, actual_to, migration = resolve_migration(provider_name, from_version, to_version)
    changelog_url = migration.changelog_url if migration else p_spec.docs_url
    rewrites = migration.rewrites if migration else []

    snapshot_dir = os.path.join(repo_dir, ".compart", "snapshot_tmp")
    snapshotter = SnapshotManager(workdir=repo_dir, snapshot_dir=snapshot_dir)
    files_scanned = snapshotter.snapshot()

    intel = CompartIntelligence()
    decision = intel.decide(repo_dir, provider_name, actual_from, actual_to, has_rewrites=bool(rewrites))

    patch_results: List[PatchResult] = []
    ai_planner = None
    quarantine_error: Optional[str] = None

    if decision.strategy == "DIRECT":
        # G1: executable flywheel — registry rewrites + KB-cached rewrites, deduped by pattern
        kb_rules = direct_rewrites_for(repo_dir, provider_name, actual_from, actual_to)
        seen_patterns = {r.pattern for r in rewrites}
        extra = [r for r in kb_rules if r.pattern not in seen_patterns]
        combined = list(rewrites) + extra
        if combined:
            patch_results = apply_rewrites(repo_dir, combined, dry_run=False)
    elif decision.strategy == "AI":
        ai_planner = AIPatchPlanner.from_env(api_key=llm_api_key, model=llm_model, base_url=llm_base_url)
        if ai_planner is None:
            quarantine_error = (
                "AI repair required (novel change, no verified pattern) but no AI provider is configured. "
                "Run `compart auth` or set ANTHROPIC_API_KEY / OPENAI_API_KEY."
            )
        else:
            impact = ImpactAnalyst().analyze_impact(repo_dir, provider_name)
            target_files = impact.affected_files
            if target_files:
                migration_desc = migration.description if migration else f"Upgrade {provider_name} to {actual_to}"
                ai_results = ai_planner.plan_and_apply(
                    repo_dir=repo_dir,
                    affected_files=target_files,
                    provider_name=provider_name,
                    from_version=actual_from,
                    to_version=actual_to,
                    migration_details=migration_desc,
                    dry_run=False,
                )
                if ai_results:
                    patch_results.extend(ai_results)
    else:
        quarantine_error = (
            f"No safe repair path for {provider_name} {actual_from}->{actual_to} ({decision.reason}). "
            "Run `compart auth` to enable AI repair, or add a verified migration to the registry."
        )

    modified_paths = [os.path.abspath(r.file_path) for r in patch_results if r.success]
    files_modified = len(modified_paths)
    unified_diff = "\n".join(r.unified_diff for r in patch_results if r.unified_diff)

    run_style_formatter(repo_dir, modified_paths)

    # Blast radius: files changed that were NOT targeted by the patch plan
    all_changed: set[str] = set()
    targeted: set[str] = set(modified_paths)
    for dirpath, dirnames, filenames in os.walk(repo_dir, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", ".next", "__pycache__", ".compart"}]
        for fn in filenames:
            fp = os.path.abspath(os.path.join(dirpath, fn))
            try:
                snap_hash = snapshotter._snapshot_dir
                rel = os.path.relpath(fp, repo_dir)
                snap_copy = os.path.join(snap_hash, rel)
                if os.path.exists(snap_copy):
                    if _file_hash(fp) != _file_hash(snap_copy):
                        all_changed.add(fp)
            except Exception:
                pass

    unintended = all_changed - targeted
    unintended_count = len(unintended)
    blast_radius_verified = unintended_count == 0

    # Install dependencies then run tests. -1 means NOT RUN (no repair applied, no execution to verify).
    test_cmd = _detect_test_command(repo_dir)
    test_exit_code = -1
    test_duration_ms = 0
    raw_output = ""

    if files_modified > 0:
        if test_cmd:
            try:
                _run_install(repo_dir, timeout=120)
            except Exception:
                pass

        test_start = time.time()
        try:
            proc = _run_tests(repo_dir, test_cmd, timeout=120)
            test_exit_code = proc.returncode
            raw_output = f"{proc.stdout or ''}\n{proc.stderr or ''}"
        except subprocess.TimeoutExpired:
            test_exit_code = 1
            raw_output = "Test run timed out after 120s"
        except Exception as exc:
            test_exit_code = 1
            raw_output = str(exc)
        test_duration_ms = max(1, int((time.time() - test_start) * 1000))

        # AI Self-Repair Loop: if tests failed and AI planner is available, retry once with test error
        if test_exit_code != 0 and ai_planner and modified_paths:
            retry_results = ai_planner.plan_and_apply(
                repo_dir=repo_dir,
                affected_files=modified_paths,
                provider_name=provider_name,
                from_version=actual_from,
                to_version=actual_to,
                migration_details=migration.description if migration else "",
                test_error=raw_output,
                dry_run=False,
            )
            if retry_results:
                # Explicit hybrid: deterministic pre-pass + AI repair of the failure.
                decision.strategy = "HYBRID"
                decision.reason = "direct_then_ai_repair"
                decision.confidence = 0.7
                run_style_formatter(repo_dir, modified_paths)
                retry_proc = _run_tests(repo_dir, test_cmd, timeout=120)
                if retry_proc.returncode == 0:
                    test_exit_code = 0
                    patch_results = retry_results
                    unified_diff = "\n".join(r.unified_diff for r in patch_results if r.unified_diff)

    # Roll back if tests failed
    if test_exit_code != 0:
        snapshotter.restore()
        files_modified = 0
        unified_diff = ""

    snapshotter.cleanup()
    lockfile_hash = _compute_lockfile_hash(repo_dir)
    patch_hash = _blake3_digest(unified_diff.encode("utf-8"))

    all_rules = [desc for r in patch_results for desc in r.rules_applied]
    meta = TrustPRMetadata(
        provider_name=p_spec.display_name,
        from_version=actual_from,
        to_version=actual_to,
        changelog_url=changelog_url,
        files_modified=files_modified,
        files_scanned=files_scanned,
        unintended_files_modified=unintended_count,
        quarantined_callsites_count=0,
        unified_diff=unified_diff,
        test_command=test_cmd,
        test_exit_code=test_exit_code,
        test_duration_ms=test_duration_ms,
        lockfile_hash=lockfile_hash,
        patch_hash=patch_hash,
        semantic_score=1.0,
        impacted_callsites=[{"description": d} for d in all_rules],
    )
    pr_body = generate_trust_pr_markdown(meta)

    success = blast_radius_verified and test_exit_code == 0 and files_modified > 0 and quarantine_error is None

    if success:
        record_migration_history(repo_dir, {
            "migration_id": f"migration:{p_spec.name.lower()}:{actual_to}",
            "provider_name": p_spec.name,
            "from_version": actual_from,
            "to_version": actual_to,
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "test_command": test_cmd,
            "test_exit_code": test_exit_code,
            "test_duration_ms": test_duration_ms,
            "patch_sha256": patch_hash,
            "blast_radius_zero": blast_radius_verified,
            "files_modified": modified_paths,
            "strategy": decision.strategy,
            "reason": decision.reason,
        })
        kb_upsert(
            repo_dir,
            provider_name,
            actual_from,
            actual_to,
            applied_rules=all_rules,
            patch_results=patch_results,
            test_command=test_cmd,
            evidence={"patch_hash": patch_hash, "lockfile_hash": lockfile_hash},
            rewrites=rewrites,
        )
    elif quarantine_error and not patch_results:
        # G5: loud quarantine — never silent
        pr_body = (
            f"## Compart: repair quarantined\n\n{quarantine_error}\n\n"
            f"Provider: {p_spec.display_name} {actual_from} -> {actual_to}\n"
            f"Strategy: {decision.strategy} ({decision.reason})\n"
        )

    pr_url = None
    pr_number = None
    if create_pr and github_repo and files_modified > 0:
        branch_name = f"compart/{p_spec.name}-v{actual_to.replace('.', '-')}"
        commit_msg = (
            f"migrate: {p_spec.display_name} {actual_from} -> {actual_to}\n\n"
            f"Detected and patched by Compart autonomous maintenance engine.\n"
            f"Rules applied:\n" + "\n".join(f"- {d}" for d in all_rules)
        )
        pushed = git_commit_and_push(repo_dir, modified_paths, branch_name, commit_msg)

        if pushed:
            pr_title = f"compart: migrate {p_spec.display_name} {actual_from} -> {actual_to}"
            pr_url = gh_create_pr(github_repo, branch_name, pr_title, pr_body)

        if not pr_url and github_client:
            pr_resp = github_client.create_pull_request(
                repo=github_repo,
                title=f"fix(deps): upgrade {p_spec.display_name} to {actual_to}",
                body=pr_body,
                head_branch=branch_name,
                labels=["compart-maintenance", "verified-green"],
            )
            if pr_resp.get("html_url"):
                pr_url = pr_resp["html_url"]
                pr_number = pr_resp.get("number")

    return MaintenanceRunReport(
        success=success,
        provider_name=p_spec.name,
        from_version=actual_from,
        to_version=actual_to,
        repository_path=repo_dir,
        files_scanned=files_scanned,
        files_modified=files_modified,
        unintended_files_modified=unintended_count,
        blast_radius_verified=blast_radius_verified,
        test_exit_code=test_exit_code,
        test_duration_ms=test_duration_ms,
        unified_diff=unified_diff,
        trust_pr_body=pr_body,
        patch_results=patch_results,
        pr_url=pr_url,
        pr_number=pr_number,
        error=quarantine_error,
    )
