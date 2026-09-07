from dataclasses import dataclass, field
import os
import subprocess
import time
from typing import Any, Dict, List, Optional

from compart.ai_planner import AIPatchPlanner
from compart.change_source import ChangeSource
from compart.graph import build_dependency_graph
from compart.sandbox.snapshot import SnapshotManager, _file_hash
from compart.intelligence import CompartIntelligence, resolve_migration
from compart.knowledge import direct_rewrites_for
from compart.patch_writer import apply_rewrites, discover_aliases, instantiate_alias_rules
from compart.providers.registry import get_default_registry
from compart.test_runner import _detect_test_command as _detect, _run_tests

try:
    from compart._core import route_and_compress
except ImportError:
    def route_and_compress(content: str) -> str:
        return content


@dataclass
class ChangeAnalysisResult:
    provider: str
    from_version: str
    to_version: str
    breaking_changes_count: int
    mutations: List[Dict[str, Any]] = field(default_factory=list)
    changelog_url: str = ""


@dataclass
class ImpactAnalysisResult:
    provider: str
    affected_files: List[str]
    callsites_count: int
    wrapper_files: List[str]
    callsites: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PatchPlanResult:
    provider: str
    plan_id: str
    targets: List[Dict[str, Any]]
    transformations_count: int
    raw_plan: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    success: bool
    test_command: str
    test_exit_code: int
    duration_ms: int
    blast_radius_verified: bool
    unintended_files_modified: int
    compressed_execution_log: str
    raw_log_bytes: int
    compressed_log_bytes: int
    unified_diff: str


class ChangeAnalyzer:
    def analyze(self, provider_name: str, from_version: Optional[str] = None, to_version: Optional[str] = None) -> ChangeAnalysisResult:
        registry = get_default_registry()
        p_spec = registry.get(provider_name)
        if not p_spec:
            return ChangeAnalysisResult(provider=provider_name, from_version=from_version or "unknown", to_version=to_version or "unknown", breaking_changes_count=0)

        migration = None
        if p_spec.migrations:
            migration = next(iter(p_spec.migrations.values()))

        actual_from = from_version or (migration.from_version if migration else "1.0.0")
        actual_to = to_version or (migration.to_version if migration else "2.0.0")
        changelog_url = migration.changelog_url if migration else p_spec.docs_url

        mutations = []
        if migration:
            mutations.append({
                "description": migration.description,
                "breaking_changes_count": migration.breaking_changes_count,
            })

        return ChangeAnalysisResult(
            provider=p_spec.name,
            from_version=actual_from,
            to_version=actual_to,
            breaking_changes_count=migration.breaking_changes_count if migration else 0,
            mutations=mutations,
            changelog_url=changelog_url,
        )


class ImpactAnalyst:
    def analyze_impact(self, repo_dir: str, provider_name: str) -> ImpactAnalysisResult:
        """Provider path preserved: vendors match by SDK name (one branch of the general matcher)."""
        return self.analyze_impact_for(repo_dir, ChangeSource.sdk(provider_name))

    def analyze_impact_for(self, repo_dir: str, source: Any) -> ImpactAnalysisResult:
        """General matcher: identity against wrapper metadata, callsite patterns, and file paths."""
        identity = (getattr(source, "identity", "") or "").lower()
        provider_name = (getattr(source, "provider", "") or identity) or ""
        graph = build_dependency_graph(repo_dir)
        affected_files = set()
        wrappers = []
        matched_callsites = []

        for w in graph.get("wrappers", []):
            hay = f"{w.get('wrapper_file', '')} {w.get('wraps_provider', '')}".lower()
            if identity and identity in hay:
                wrappers.append(w.get("wrapper_file"))
                affected_files.add(w.get("wrapper_file"))

        for c in graph.get("callsites", []):
            hay = f"{c.get('function_name', '')} {c.get('matched_pattern', '')} {c.get('file_path', '')}".lower()
            if identity and identity in hay:
                matched_callsites.append(c)
                affected_files.add(c.get("file_path"))

        return ImpactAnalysisResult(
            provider=provider_name,
            affected_files=sorted(list(affected_files)),
            callsites_count=len(matched_callsites),
            wrapper_files=wrappers,
            callsites=matched_callsites,
        )


class PatchPlanner:
    def __init__(self, ai_planner: Optional[AIPatchPlanner] = None):
        self.ai_planner = ai_planner

    def plan(self, repo_dir: str, change_analysis: ChangeAnalysisResult) -> PatchPlanResult:
        _from, _to, migration = resolve_migration(
            change_analysis.provider, change_analysis.from_version, change_analysis.to_version
        )

        rewrites = migration.rewrites if migration else []
        intel = CompartIntelligence()
        dec = intel.decide(repo_dir, change_analysis.provider, _from, _to, has_rewrites=bool(rewrites))
        patch_results = []
        if dec.strategy == "DIRECT" and rewrites:
            kb_rules = direct_rewrites_for(repo_dir, change_analysis.provider, _from, _to)
            seen = {r.pattern for r in rewrites}
            combined = list(rewrites) + [r for r in kb_rules if r.pattern not in seen]
            for ar in instantiate_alias_rules(combined, discover_aliases(repo_dir, change_analysis.provider)):
                if ar.pattern not in seen:
                    seen.add(ar.pattern)
                    combined.append(ar)
            patch_results = apply_rewrites(repo_dir, combined, dry_run=True)
        elif dec.strategy == "AI":
            planner = self.ai_planner or AIPatchPlanner.from_env()
            if planner:
                impact = ImpactAnalyst().analyze_impact(repo_dir, change_analysis.provider)
                if impact.affected_files:
                    desc = change_analysis.mutations[0]["description"] if change_analysis.mutations else ""
                    patch_results = planner.plan_and_apply(
                        repo_dir=repo_dir,
                        affected_files=impact.affected_files,
                        provider_name=change_analysis.provider,
                        from_version=change_analysis.from_version,
                        to_version=change_analysis.to_version,
                        migration_details=desc,
                        dry_run=True,
                    )

        targets = [
            {
                "file_path": r.file_path,
                "lines_changed": r.lines_changed,
                "unified_diff": r.unified_diff,
                "rules_applied": r.rules_applied,
            }
            for r in patch_results if r.success
        ]

        return PatchPlanResult(
            provider=change_analysis.provider,
            plan_id=f"plan_{change_analysis.provider}_{change_analysis.to_version}",
            targets=targets,
            transformations_count=len(targets),
            raw_plan={"patch_targets": targets, "files_scanned": len(patch_results)},
        )


class PatchVerifier:
    def verify(self, repo_dir: str, test_cmd: Optional[str] = None, expected_modified_files: Optional[List[str]] = None) -> VerificationResult:
        start_time = time.time()
        cmd = test_cmd if test_cmd is not None else _detect(repo_dir)
        # Never synthesize exit 0 — empty means no test suite, so verification must fail closed.
        if not cmd:
            return VerificationResult(
                success=False,
                test_command="",
                test_exit_code=1,
                duration_ms=int((time.time() - start_time) * 1000),
                blast_radius_verified=False,
                unintended_files_modified=0,
                compressed_execution_log=route_and_compress("no test command detected"),
                raw_log_bytes=0,
                compressed_log_bytes=0,
                unified_diff="",
            )

        try:
            proc = _run_tests(repo_dir, cmd, timeout=120)
        except subprocess.TimeoutExpired:
            proc = subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="timed out after 120s")
        duration_ms = max(1, int((time.time() - start_time) * 1000))

        raw_output = f"{proc.stdout or ''}\n{proc.stderr or ''}"
        compressed_output = route_and_compress(raw_output)

        # Blast radius is verified by the caller (AutonomousMaintenancePipeline.run
        # snapshots before apply and diffs after); this verifier only certifies tests.
        unintended_count = 0
        blast_radius_ok = True

        return VerificationResult(
            success=(proc.returncode == 0 and blast_radius_ok),
            test_command=cmd,
            test_exit_code=proc.returncode,
            duration_ms=duration_ms,
            blast_radius_verified=blast_radius_ok,
            unintended_files_modified=unintended_count,
            compressed_execution_log=compressed_output,
            raw_log_bytes=len(raw_output.encode("utf-8")),
            compressed_log_bytes=len(compressed_output.encode("utf-8")),
            unified_diff="",
        )


class AutonomousMaintenancePipeline:
    def __init__(self, ai_planner: Optional[AIPatchPlanner] = None):
        self.change_analyzer = ChangeAnalyzer()
        self.impact_analyst = ImpactAnalyst()
        self.patch_planner = PatchPlanner(ai_planner=ai_planner)
        self.patch_verifier = PatchVerifier()
        self.ai_planner = ai_planner

    def run(self, repo_dir: str, provider_name: str, from_version: Optional[str] = None, to_version: Optional[str] = None) -> Dict[str, Any]:
        change_info = self.change_analyzer.analyze(provider_name, from_version, to_version)
        impact_info = self.impact_analyst.analyze_impact(repo_dir, provider_name)
        patch_plan = self.patch_planner.plan(repo_dir, change_info)

        _from, _to, migration = resolve_migration(provider_name, change_info.from_version, change_info.to_version)
        rewrites = migration.rewrites if migration else []

        intel = CompartIntelligence()
        dec = intel.decide(repo_dir, provider_name, _from, _to, has_rewrites=bool(rewrites))
        # snapshot before apply so blast radius is real
        snapshotter = SnapshotManager(workdir=repo_dir, snapshot_dir=os.path.join(repo_dir, ".compart", "snapshot_tmp_agents"))
        snapshotter.snapshot()
        real_results = []
        if dec.strategy == "DIRECT" and rewrites:
            kb_rules = direct_rewrites_for(repo_dir, provider_name, _from, _to)
            seen = {r.pattern for r in rewrites}
            combined = list(rewrites) + [r for r in kb_rules if r.pattern not in seen]
            for ar in instantiate_alias_rules(combined, discover_aliases(repo_dir, provider_name)):
                if ar.pattern not in seen:
                    seen.add(ar.pattern)
                    combined.append(ar)
            real_results = apply_rewrites(repo_dir, combined, dry_run=False)
        elif dec.strategy == "AI":
            planner = self.ai_planner or AIPatchPlanner.from_env()
            if planner and impact_info.affected_files:
                desc = change_info.mutations[0]["description"] if change_info.mutations else ""
                real_results = planner.plan_and_apply(
                    repo_dir=repo_dir,
                    affected_files=impact_info.affected_files,
                    provider_name=provider_name,
                    from_version=change_info.from_version,
                    to_version=change_info.to_version,
                    migration_details=desc,
                    dry_run=False,
                )

        unified_diff = "\n".join(r.unified_diff for r in real_results if r.unified_diff)
        modified_paths = [r.file_path for r in real_results if r.success]

        # G7: real blast check — diff worktree vs pre-apply snapshot
        targeted = {os.path.abspath(p) for p in modified_paths}
        unintended = 0
        try:
            snap_dir = snapshotter._snapshot_dir
            for dirpath, dirnames, filenames in os.walk(repo_dir, topdown=True):
                dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", ".next", "__pycache__", ".venv", "venv", "env", "dist", "build", "target", ".compart"}]
                for fn in filenames:
                    fp = os.path.abspath(os.path.join(dirpath, fn))
                    rel = os.path.relpath(fp, repo_dir)
                    snap_copy = os.path.join(snap_dir, rel)
                    if os.path.exists(snap_copy):
                        try:
                            if _file_hash(fp) != _file_hash(snap_copy) and fp not in targeted:
                                unintended += 1
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            snapshotter.cleanup()
        except Exception:
            pass

        verification = self.patch_verifier.verify(repo_dir, expected_modified_files=modified_paths)
        verification.unified_diff = unified_diff
        verification.unintended_files_modified = unintended
        verification.blast_radius_verified = (unintended == 0)
        verification.success = verification.success and (unintended == 0)

        return {
            "success": verification.success,
            "provider": provider_name,
            "change_analysis": change_info,
            "impact_analysis": impact_info,
            "patch_plan": patch_plan,
            "verification": verification,
            "unified_diff": unified_diff,
            "files_modified": len(modified_paths),
        }
