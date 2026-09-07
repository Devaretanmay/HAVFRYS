# Copyright 2026 Compart Authors
# SPDX-License-Identifier: Apache-2.0

import json
import os
from typing import Any, Dict, List, Optional
from compart.providers.registry import get_default_registry


def detect_drift(repo_dir: str, provider_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Inspect repository manifests to detect installed providers."""
    registry = get_default_registry()
    detected = []

    pkg_json_path = os.path.join(repo_dir, "package.json")
    if os.path.exists(pkg_json_path):
        try:
            with open(pkg_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for dep_name, version in deps.items():
                p_spec = registry.get(dep_name)
                if p_spec and (provider_name is None or p_spec.name.lower() == provider_name.lower()):
                    detected.append({
                        "provider": p_spec.name,
                        "display_name": p_spec.display_name,
                        "package_name": dep_name,
                        "declared_version": version,
                        "manifest_path": "package.json",
                    })
        except Exception:
            pass

    return detected
