# Copyright 2026 Compart Authors
# SPDX-License-Identifier: Apache-2.0

"""
Compart GitHub App PR bot.

This is the first product milestone: install the app, open a PR, and Compart
automatically posts a verification result on that PR.

The PR bot is not a separate code path from the maintenance engine. It is an
event handler that constructs a TriggerContext and passes it to the shared
MaintenancePipeline.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from typing import Any, Callable, Dict, List, Optional

from compart.github.client import GitHubAppClient
from compart.pipeline import (
    MaintenancePipeline,
    PipelinePolicy,
    TriggerContext,
    analyze_trigger_context,
)
from compart.github.pr_render import (
    render_verification_comment,
    render_maintenance_issue_comment,
)
from compart.graph import build_dependency_graph
from compart.drift import detect_drift

_logger = logging.getLogger("compart.pr_bot")


# ── PR event handlers ──────────────────────────────────────────────────────

def handle_pull_request_event(
    payload: Dict[str, Any],
    event_type: str,
    client: GitHubAppClient,
    policy: Optional[PipelinePolicy] = None,
    workdir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Handle a pull_request.* webhook event.

    Supported trigger types:

    * pull_request.opened
    * pull_request.synchronize
    * pull_request.reopened
    """
    policy = policy or PipelinePolicy()

    ppr = payload.get("pull_request")
    if not ppr:
        return {"success": False, "error": "No pull_request in payload"}

    repo = payload.get("repository", {}).get("full_name")
    if not repo:
        return {"success": False, "error": "No repository in payload"}

    number = ppr.get("number")
    action = payload.get("action", "")
    full_event = f"pull_request.{action}"

    ref = ppr.get("head", {}).get("ref")
    sha = ppr.get("head", {}).get("sha")
    base_ref = ppr.get("base", {}).get("ref")

    if not number or not ref or not sha:
        return {"success": False, "error": "Missing PR head info"}

    changed_files = _extract_changed_files(payload)
    ctx = TriggerContext.from_pull_request_event(payload, workdir=workdir, changed_files=changed_files)

    pipeline = MaintenancePipeline(client=client, policy=policy)
    result = pipeline.run(ctx)

    return {
        "success": True,
        "event_type": full_event,
        "repository": repo,
        "pr_number": number,
        "pipeline_status": result.status,
        "mergeable": result.mergeable,
        "check_state": result.check_state,
        "check_description": result.status_description,
        "comment_posted": bool(result.comment_body),
        "comment_preview": _safe_preview(result.comment_body),
    }


def _extract_changed_files(payload: Dict[str, Any]) -> List[str]:
    """Try to extract changed file list from webhook payload or metadata."""
    ppr = payload.get("pull_request") or {}
    if ppr.get("files"):
        return [f.get("filename") for f in ppr.get("files") if f.get("filename")]

    meta = payload.get("compart", {})
    if isinstance(meta, dict):
        return meta.get("changed_files", [])
    return []


def _safe_preview(text: str) -> str:
    if not text:
        return ""
    lines = text.splitlines()[:6]
    return "\n".join(lines)


# ── External-change event handler ──────────────────────────────────────────

def handle_external_change_event(
    payload: Dict[str, Any],
    client: GitHubAppClient,
    policy: Optional[PipelinePolicy] = None,
    workdir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Handle an external-change event (provider version drift detected).

    The payload should contain:
        provider_name, from_version, to_version, repository, ref, sha, workdir
    """
    policy = policy or PipelinePolicy()

    repo = payload.get("repository")
    if not repo:
        return {"success": False, "error": "No repository in payload"}

    ctx = TriggerContext.from_external_change(
        provider_name=payload.get("provider_name", ""),
        from_version=payload.get("from_version", ""),
        to_version=payload.get("to_version", ""),
        repository=repo,
        ref=payload.get("ref", "main"),
        sha=payload.get("sha", ""),
        workdir=workdir,
        description=payload.get("description", ""),
    )

    pipeline = MaintenancePipeline(client=client, policy=policy)
    result = pipeline.run(ctx)

    return {
        "success": True,
        "event_type": "external.change.drift",
        "repository": repo,
        "pipeline_status": result.status,
        "mergeable": result.mergeable,
        "check_state": result.check_state,
        "comment_posted": bool(result.comment_body),
    }


# ── Local / CI run helpers ─────────────────────────────────────────────────

def run_on_pr_locally(
    repo: str,
    pr_number: int,
    workdir: str,
    base_branch: str = "main",
    client: Optional[GitHubAppClient] = None,
    policy: Optional[PipelinePolicy] = None,
) -> Dict[str, Any]:
    """
    Run the PR bot against a local checkout of a PR.

    Useful for:
    * local development
    * CI check jobs that want Compart to post results
    """
    client = client or GitHubAppClient()
    changed_files = _diff_files_locally(workdir, base_branch)

    payload: Dict[str, Any] = {
        "action": "synchronize",
        "pull_request": {
            "number": pr_number,
            "title": "Local PR simulation",
            "body": "Compart local run",
            "head": {"ref": "pr-branch", "sha": "local-sha"},
            "base": {"ref": base_branch},
            "files": [{"filename": f} for f in changed_files],
        },
        "repository": {"full_name": repo},
        "compart": {"changed_files": changed_files},
    }

    return handle_pull_request_event(
        payload,
        "pull_request.synchronize",
        client,
        policy,
        workdir=workdir,
    )


def _diff_files_locally(workdir: str, base_branch: str) -> List[str]:
    """Return files changed in the current checkout relative to base_branch."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", base_branch],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
            return files
    except Exception as e:
        _logger.warning("git diff failed: %s", e)

    return []


def render_day0_onboarding_issue(repo: str, workdir: Optional[str] = None) -> str:
    """Render the Day-0 repository onboarding and contract inventory issue."""
    providers_text = "  - No external third-party SDK dependencies detected"
    total_files = 0
    callsites = 0

    if workdir and os.path.isdir(workdir):
        try:
            detected = detect_drift(workdir, None)
            if detected:
                providers_text = "\n".join(
                    f"  - {d.get('provider', 'API')} ({d.get('package_name', '')}) -> declared: {d.get('declared_version', 'unknown')}"
                    for d in detected
                )
            graph = build_dependency_graph(workdir)
            total_files = len(graph.get("nodes", []))
            callsites = sum(len(node.get("callsites", [])) for node in graph.get("nodes", []))
        except Exception as e:
            _logger.warning("failed to compute Day-0 stats for %s: %s", repo, e)

    lines = [
        "-----------------------------------------",
        "   COMPART DAY-0 REPOSITORY ONBOARDING   ",
        "-----------------------------------------",
        "",
        f"Compart has mapped external API dependencies and contracts for `{repo}`.",
        "",
        "### External APIs & SDKs Monitored:",
        providers_text,
        "",
        "### Repository Architecture Graph:",
        f"  - Total indexed files: {total_files}",
        f"  - External call sites inspected: {callsites}",
        "",
        "### Continuous Guard Status:",
        "  - [OK] Automated PR Review: Active (Audit Mode)",
        "  - [OK] Auto-Fix Policy: Opt-in (Configurable via .compart/config.yaml)",
        "  - [OK] External Contract Drift: Watching upstream provider releases",
        "",
        "-----------------------------------------",
    ]
    return "\n".join(lines)


def handle_installation_event(
    payload: Dict[str, Any],
    event_type: str,
    client: GitHubAppClient,
    workdir_fn: Optional[Callable[[str], str]] = None,
) -> Dict[str, Any]:
    """Handle installation.* and installation_repositories.* webhook events."""
    repos_data = payload.get("repositories") or payload.get("repositories_added") or []
    onboarded: List[str] = []

    for repo_info in repos_data:
        repo_name = repo_info.get("full_name") if isinstance(repo_info, dict) else str(repo_info)
        if not repo_name:
            continue

        workdir = workdir_fn(repo_name) if workdir_fn else None
        issue_body = render_day0_onboarding_issue(repo_name, workdir=workdir)
        try:
            client.create_issue(
                repo=repo_name,
                title="[COMPART] Day-0 External Contract & API Dependency Map",
                body=issue_body,
                labels=["compart", "maintenance"],
            )
            onboarded.append(repo_name)
        except Exception as e:
            _logger.warning("failed to post Day-0 onboarding issue for %s: %s", repo_name, e)

    return {
        "success": True,
        "event_type": event_type,
        "repositories_onboarded": onboarded,
    }


def make_pr_bot_handler(
    client: Optional[GitHubAppClient] = None,
    policy: Optional[PipelinePolicy] = None,
    workdir_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
) -> Callable[[Dict[str, Any], str], Dict[str, Any]]:
    client = client or GitHubAppClient()
    policy = policy or PipelinePolicy()

    def handler(payload: Dict[str, Any], event_type: str) -> Dict[str, Any]:
        workdir = None
        if workdir_fn:
            workdir = workdir_fn(payload)

        if event_type.startswith("pull_request."):
            return handle_pull_request_event(
                payload,
                event_type,
                client,
                policy,
                workdir=workdir,
            )

        if event_type.startswith("external.change"):
            return handle_external_change_event(
                payload,
                client,
                policy,
                workdir=workdir,
            )

        if event_type.startswith("installation"):
            def repo_workdir_resolver(repo_name: str) -> Optional[str]:
                if workdir_fn:
                    return workdir_fn({"repository": {"full_name": repo_name}})
                return None

            return handle_installation_event(
                payload,
                event_type,
                client,
                workdir_fn=repo_workdir_resolver,
            )

        return {
            "success": True,
            "event": event_type,
            "handled": False,
            "note": "Event type not handled by PR bot",
        }

    return handler
