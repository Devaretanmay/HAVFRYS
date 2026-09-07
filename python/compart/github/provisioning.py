# Copyright 2026 Compart Authors
# SPDX-License-Identifier: Apache-2.0
"""Repository provisioning: managed clone/pull cache for installed repos.

Gives the GitHub App a real checkout to analyze: install event → clone →
Day-0 index → READY. PR events resolve to the same checkout instead of the
daemon's cwd. Cloning uses a token when configured, anonymous https
otherwise (public repos), or COMPART_REPO_REMOTE_* overrides (tests,
mirrors, self-hosted).
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Any, Dict, Optional

_logger = logging.getLogger("compart.provisioning")


def cache_dir() -> str:
    base = os.environ.get("COMPART_REPOS_DIR",
                           os.path.join(os.path.expanduser("~/.compart"), "repos"))
    os.makedirs(base, exist_ok=True)
    return base


def cached_path(repo_full_name: str) -> str:
    slug = repo_full_name.replace("/", "__")
    return os.path.join(cache_dir(), slug)


def remote_for(repo_full_name: str, token: Optional[str] = None) -> str:
    """Clone URL for a repo. Env override wins (mirrors/tests), else github."""
    slug = repo_full_name.replace("/", "__").upper()
    override = os.environ.get(f"COMPART_REPO_REMOTE_{slug}")
    if override:
        return override
    if token:
        return f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
    return f"https://github.com/{repo_full_name}.git"


def _run_git(args: list, cwd: str, timeout: int = 120) -> bool:
    try:
        proc = subprocess.run(["git"] + args, cwd=cwd, capture_output=True,
                              text=True, timeout=timeout)
        return proc.returncode == 0
    except Exception as e:
        _logger.warning("git %s failed in %s: %s", args[:2], cwd, e)
        return False


def ensure_repo_checkout(repo_full_name: str, token: Optional[str] = None,
                         ref: str = "main") -> Optional[str]:
    """Clone on first sight, fast-forward on later sightings. Returns path or None."""
    dest = cached_path(repo_full_name)
    if os.path.isdir(os.path.join(dest, ".git")):
        _run_git(["fetch", "origin"], dest)
        _run_git(["checkout", ref], dest)
        _run_git(["merge", "--ff-only", f"origin/{ref}"], dest)
        return dest
    parent = os.path.dirname(dest)
    os.makedirs(parent, exist_ok=True)
    ok = _run_git(["clone", remote_for(repo_full_name, token), dest], parent, timeout=300)
    if not ok or not os.path.isdir(os.path.join(dest, ".git")):
        return None
    _run_git(["checkout", ref], dest)
    return dest


def workdir_for_event(payload: Dict[str, Any], token: Optional[str] = None) -> Optional[str]:
    """Resolve a managed checkout for any webhook payload carrying a repository."""
    repo = (payload.get("repository") or {}).get("full_name", "")
    if not repo:
        return None
    return ensure_repo_checkout(repo, token=token)
