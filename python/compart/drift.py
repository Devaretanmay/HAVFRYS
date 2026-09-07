# Copyright 2026 Compart Authors
# SPDX-License-Identifier: Apache-2.0

import json
import os
import re
from typing import Any, Dict, List, Optional
from compart.change_source import (
    Detection, ChangeSource, NO_IMPACT, IMPACT_DIRECT, IMPACT_AI, IMPACT_QUARANTINE,
)
from compart.providers.registry import get_default_registry


def detect_drift(repo_dir: str, provider_name: Optional[str] = None) -> List[Dict[str, Any]]:
    registry = get_default_registry()
    detected = []

    def _add(dep_name: str, version: str, manifest: str):
        p_spec = registry.get(dep_name)
        if p_spec and (provider_name is None or p_spec.name.lower() == provider_name.lower()):
            target = None
            try:
                if p_spec.migrations:
                    target = next(iter(p_spec.migrations.values())).to_version
            except Exception:
                target = None
            detected.append({
                "provider": p_spec.name,
                "display_name": p_spec.display_name,
                "package_name": dep_name,
                "declared_version": version,
                "target_version": target,
                "manifest_path": manifest,
            })

    pkg_json_path = os.path.join(repo_dir, "package.json")
    if os.path.exists(pkg_json_path):
        try:
            with open(pkg_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for dep_name, version in deps.items():
                _add(dep_name, version, "package.json")
        except Exception:
            pass

    req_path = os.path.join(repo_dir, "requirements.txt")
    if os.path.exists(req_path):
        try:
            with open(req_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip().split("#")[0].strip()
                    if not line or line.startswith("-"):
                        continue
                    name = line.split("==")[0].split(">=")[0].split("~=")[0].split("<")[0].strip().lower()
                    ver = line.split("==")[-1].strip() if "==" in line else "unknown"
                    _add(name, ver, "requirements.txt")
        except Exception:
            pass

    pyproj = os.path.join(repo_dir, "pyproject.toml")
    if os.path.exists(pyproj):
        try:
            with open(pyproj, "r", encoding="utf-8") as f:
                txt = f.read()
            for m in re.finditer(r'["\']([a-zA-Z0-9_\-]+)["\']\s*=\s*["\']([^"\']+)["\']', txt):
                _add(m.group(1).lower(), m.group(2), "pyproject.toml")
        except Exception:
            pass

    cargo = os.path.join(repo_dir, "Cargo.toml")
    if os.path.exists(cargo):
        try:
            with open(cargo, "r", encoding="utf-8") as f:
                txt = f.read()
            for m in re.finditer(r'^([a-zA-Z0-9_\-]+)\s*=\s*["\']([^"\']+)["\']', txt, re.MULTILINE):
                _add(m.group(1), m.group(2), "Cargo.toml")
        except Exception:
            pass

    for lockfile in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml"):
        lp = os.path.join(repo_dir, lockfile)
        if os.path.exists(lp):
            try:
                with open(lp, "r", encoding="utf-8", errors="replace") as f:
                    txt = f.read(1_000_000)
                for m in re.finditer(r'"?(@?[a-zA-Z0-9_\-/]+)"?\s*[:@]', txt):
                    name = m.group(1).strip('"').lower()
                    if registry.get(name):
                        _add(name, "locked", lockfile)
                        break
            except Exception:
                pass

    gomod = os.path.join(repo_dir, "go.mod")
    if os.path.exists(gomod):
        try:
            with open(gomod, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(("module ", "go ", "require (", ")")):
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        _add(parts[0].lower(), parts[1], "go.mod")
        except Exception:
            pass

    gemfile = os.path.join(repo_dir, "Gemfile")
    if os.path.exists(gemfile):
        try:
            with open(gemfile, "r", encoding="utf-8", errors="replace") as f:
                txt = f.read()
            for m in re.finditer(r"gem\s+['\"]([^'\"]+)['\"]\s*(,\s*['\"]([^'\"]+)['\"])?", txt):
                _add(m.group(1).lower(), m.group(3) or "unknown", "Gemfile")
        except Exception:
            pass

    seen = set()
    uniq = []
    for d in detected:
        k = (d["provider"], d["package_name"], d["manifest_path"])
        if k not in seen:
            seen.add(k)
            uniq.append(d)
    return uniq


def detect_changes(repo_dir: str, provider_name: Optional[str] = None) -> List[Detection]:
    """Read-only detection: understand change + locate impact, never patch.

    Returns one Detection per detected dependency. Repair strategy is decided
    downstream by CompartIntelligence; this function only classifies.
    """
    from compart.autopatch import ScanConfig, scan_callsites
    from compart.intelligence import CompartIntelligence, resolve_migration

    intel = CompartIntelligence()
    out: List[Detection] = []
    for d in detect_drift(repo_dir, provider_name):
        source = ChangeSource.sdk(
            d["provider"],
            version_from=d.get("declared_version") or "unknown",
            version_to=d.get("target_version") or "unknown",
            origin="manifest",
            package_name=d.get("package_name", ""),
            manifest_path=d.get("manifest_path", ""),
        )
        try:
            res = scan_callsites(repo_dir, ScanConfig(sdk_names=[d["provider"]]))
            callsites = res.get("callsites", [])
        except Exception:
            callsites = []
        affected = sorted({c.get("file_path", "") for c in callsites if c.get("file_path")})
        if not callsites:
            out.append(Detection(source=source, outcome=NO_IMPACT,
                                 reason="dependency declared but no callsites reference it",
                                 affected_files=[], callsite_count=0,
                                 ai_dependent=False, confidence=0.9))
            continue
        _from, _to, migration = resolve_migration(
            d["provider"], d.get("declared_version"), d.get("target_version"))
        decision = intel.decide(repo_dir, d["provider"], _from, _to,
                                has_rewrites=bool(migration and migration.rewrites))
        mapping = {"DIRECT": (IMPACT_DIRECT, False, 0.9), "AI": (IMPACT_AI, True, 0.5),
                   "QUARANTINE": (IMPACT_QUARANTINE, False, 0.0)}
        outcome, ai_dep, conf = mapping[decision.strategy]
        out.append(Detection(source=source, outcome=outcome,
                             reason=f"{decision.strategy}: {decision.reason}",
                             affected_files=affected, callsite_count=len(callsites),
                             ai_dependent=ai_dep, confidence=conf))
    return out
