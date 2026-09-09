# Copyright 2026 Koyote Authors
# SPDX-License-Identifier: Apache-2.0
"""Howl Bot: The Advisory & Consult Review Bot for Koyote.

Howl reviews pull requests, investigates contract and dependency drift,
explains risk, and files guidance. Howl is strictly read-only: it never
patches code, never commits files, and never opens pull requests.
"""

from __future__ import annotations

import logging
from typing import Any

from koyote.ai_planner import AIPatchPlanner, build_reasoning_context
from koyote.credentials import has_valid_credentials
from koyote.github.client import GitHubAppClient
from koyote.github.pr_render import render_consult_issue, render_flow_diagram
from koyote.intelligence import KoyoteIntelligence, resolve_migration
from koyote.pipeline import (
    AnalysisResult,
    PipelinePolicy,
    TriggerContext,
    analyze_trigger_context,
)

_logger = logging.getLogger("koyote.howl")


class HowlBot:
    """The Advisory & Review Bot. Explains, consults, and warns without touching code."""

    def __init__(self, client: GitHubAppClient | None = None, policy: PipelinePolicy | None = None):
        self.client = client or GitHubAppClient()
        self.policy = policy or PipelinePolicy()
        self.intel = KoyoteIntelligence()

    def review_pull_request(self, ctx: TriggerContext, require_ai: bool = False) -> dict[str, Any]:
        """Review a pull request and post Howl's advisory assessment."""
        if require_ai and not has_valid_credentials():
            return {
                "success": False,
                "error": "explain needs AI reasoning: no provider configured",
            }

        analysis = analyze_trigger_context(ctx)

        if not analysis.has_findings:
            body = (
                "## Howl Review: No Contract Impact Detected\n\n"
                f"Checked {analysis.callsites_total or len(analysis.providers_detected) or 1} external touchpoint(s). "
                "No breaking contract changes or API regressions detected.\n\n"
                "— Howl, Advisory Bot"
            )
            if ctx.pr_number is not None:
                try:
                    self.client.post_pr_comment(ctx.repository, ctx.pr_number, body)
                except Exception as e:
                    _logger.warning("Howl failed to post clean comment: %s", e)
            return {
                "success": True,
                "bot": "howl",
                "status": "clean",
                "findings_count": 0,
                "comment_body": body,
                "comment_posted": True,
            }

        items = self._assess_findings(ctx, analysis)
        body = render_consult_issue(items)
        if analysis.has_findings:
            body += "\n\n" + render_flow_diagram(analysis)
        body += f"\n\nReviewed commit: `{ctx.sha}`\nComment `@howl` or `@howl explain` to re-run."

        if ctx.pr_number is not None:
            try:
                self.client.post_pr_comment(ctx.repository, ctx.pr_number, body)
            except Exception as e:
                _logger.warning("Howl failed to post advisory comment: %s", e)

        return {
            "success": True,
            "bot": "howl",
            "status": "advisory_posted",
            "findings_count": len(analysis.findings),
            "comment_body": body,
            "comment_posted": True,
        }

    def _assess_findings(self, ctx: TriggerContext, analysis: AnalysisResult) -> list[dict[str, Any]]:
        planner = AIPatchPlanner.from_env() if has_valid_credentials() else None
        items = []
        for finding in analysis.findings:
            _from, _to, migration = resolve_migration(
                finding.provider_name, finding.current_version, finding.target_version
            )
            decision = self.intel.decide(ctx.workdir, finding.provider_name, _from, _to,
                                         has_rewrites=bool(migration and migration.rewrites))
            assessment_text = ""
            confidence = "high" if decision.strategy == "DIRECT" else "medium"
            if planner:
                reason_ctx = build_reasoning_context(
                    ctx.workdir, finding.provider_name, _from, _to,
                    finding.breaking_change, finding.migration_guide_url
                )
                assessment = planner.assess(
                    repo_dir=ctx.workdir,
                    provider_name=finding.provider_name,
                    from_version=_from,
                    to_version=_to,
                    migration_details=finding.breaking_change,
                    changelog_url=finding.migration_guide_url,
                    affected_files=finding.affected_files,
                    context=reason_ctx,
                )
                assessment_text = assessment.get("body", "")
                confidence = assessment.get("confidence", confidence)

            items.append({
                "display": finding.display_name,
                "version_from": _from,
                "version_to": _to,
                "breaking_change": finding.breaking_change,
                "guide_url": finding.migration_guide_url,
                "affected_files": finding.affected_files,
                "assessment_body": assessment_text,
                "auto_repairable": decision.strategy in ("DIRECT", "AI"),
                "confidence": confidence,
            })
        return items
