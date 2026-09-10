# Copyright 2026 Koyote Authors
# SPDX-License-Identifier: Apache-2.0
"""Repository-level identity, deterministic Repository Keys, and shared bot state.

A repository connected to Koyote receives a persistent repository identity.
Two different devices connecting to the same GitHub repository derive the exact
same Repository Key (`kyp_<digest>`), allowing team members to share repository
identity, memory, and bot watcher states (Howl / Hunt: AVAILABLE -> ACTIVE).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import stat
import time
from typing import Any, Dict, Optional

STATE_AVAILABLE = "AVAILABLE"
STATE_ACTIVE = "ACTIVE"
STATE_PAUSED = "PAUSED"

REPO_STORE_DIR = os.path.expanduser("~/.koyote")
REPO_STORE_FILE = os.path.join(REPO_STORE_DIR, "repositories.json")
ACTIVE_REPO_FILE = os.path.join(REPO_STORE_DIR, "active_repo")
SALT_FILE = os.path.join(REPO_STORE_DIR, ".koyote_salt")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _get_master_salt() -> bytes:
    _ensure_dir(REPO_STORE_DIR)
    if os.path.isfile(SALT_FILE):
        try:
            with open(SALT_FILE, "rb") as f:
                content = f.read().strip()
                if len(content) >= 32:
                    return content
        except Exception:
            pass
    salt = os.urandom(32).hex().encode("utf-8")
    fd = os.open(SALT_FILE, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(fd, "wb") as f:
        f.write(salt)
    return salt


def derive_repository_key(repo_full_name: str, repo_id: Optional[str] = None) -> str:
    """Generate a persistent, deterministic Repository Key for a given repo.
    
    Any device connecting to `owner/repo` produces the exact same Repository Key
    when given the repository identifier, enabling team sharing without creating
    duplicate logical projects.
    """
    clean_name = repo_full_name.strip().lower()
    salt = _get_master_salt()
    seed = f"{clean_name}::{repo_id or 'default'}"
    digest = hmac.new(salt, seed.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"kyp_{digest[:28]}"


def load_all_repositories() -> Dict[str, Dict[str, Any]]:
    if not os.path.isfile(REPO_STORE_FILE):
        return {}
    try:
        with open(REPO_STORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_all_repositories(repos: Dict[str, Dict[str, Any]]) -> None:
    _ensure_dir(REPO_STORE_DIR)
    fd = os.open(REPO_STORE_FILE, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(repos, f, indent=2)
        f.write("\n")


def register_repository(
    repo_full_name: str,
    repo_id: Optional[str] = None,
    installation_id: Optional[str] = None,
    workdir: Optional[str] = None,
) -> Dict[str, Any]:
    """Register or update a repository with deterministic key and initial state."""
    clean_name = repo_full_name.strip()
    key_name = clean_name.lower()
    repos = load_all_repositories()
    existing = repos.get(key_name, {})

    repo_key = existing.get("repo_key") or derive_repository_key(clean_name, repo_id)
    record = {
        "repo_name": clean_name,
        "repo_id": repo_id or existing.get("repo_id") or "unknown",
        "installation_id": installation_id or existing.get("installation_id"),
        "repo_key": repo_key,
        "workdir": workdir or existing.get("workdir"),
        "howl_state": existing.get("howl_state", STATE_AVAILABLE),
        "hunt_state": existing.get("hunt_state", STATE_AVAILABLE),
        "index_state": existing.get("index_state", "READY"),
        "created_utc": existing.get("created_utc", _now()),
        "updated_utc": _now(),
    }
    repos[key_name] = record
    save_all_repositories(repos)
    return record


def get_repository(repo_full_name: str) -> Optional[Dict[str, Any]]:
    repos = load_all_repositories()
    return repos.get(repo_full_name.strip().lower())


def set_bot_state(repo_full_name: str, bot_name: str, state: str) -> Optional[Dict[str, Any]]:
    """Update Howl or Hunt state for a repository (AVAILABLE -> ACTIVE -> PAUSED)."""
    clean_name = repo_full_name.strip().lower()
    repos = load_all_repositories()
    record = repos.get(clean_name)
    if not record:
        record = register_repository(repo_full_name)
        repos = load_all_repositories()

    bot = bot_name.strip().lower()
    if bot in ("howl", "consult"):
        record["howl_state"] = state
    elif bot in ("hunt", "work"):
        record["hunt_state"] = state
    record["updated_utc"] = _now()
    repos[clean_name] = record
    save_all_repositories(repos)
    return record


def get_active_repo() -> Optional[str]:
    """Return currently active repository name from local working context."""
    if os.path.isfile(ACTIVE_REPO_FILE):
        try:
            with open(ACTIVE_REPO_FILE, "r", encoding="utf-8") as f:
                val = f.read().strip()
                if val:
                    return val
        except Exception:
            pass
    repos = load_all_repositories()
    if repos:
        first = next(iter(repos.values()))
        return first.get("repo_name")
    return None


def set_active_repo(repo_name: str) -> str:
    """Set active repository working context."""
    clean = repo_name.strip()
    _ensure_dir(REPO_STORE_DIR)
    with open(ACTIVE_REPO_FILE, "w", encoding="utf-8") as f:
        f.write(clean + "\n")
    return clean
