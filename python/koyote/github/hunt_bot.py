# Copyright 2026 Koyote Authors
# SPDX-License-Identifier: Apache-2.0
"""Hunt Bot: The Autonomous Worker & Repair Bot for Koyote.

Hunt detects breaking drift, generates AI patches using the user's configured
LLM provider (guided by verified pattern memory to save tokens), verifies
the repair in an OS-enforced sandbox, and pushes verified commits or opens PRs.
"""

from __future__ import annotations

import logging
from typing import Any

from koyote.github.client import GitHubAppClient
from koyote.pipeline import (
    MaintenancePipeline,
    PipelinePolicy,
    PipelineResult,
    TriggerContext,
)

_logger = logging.getLogger("koyote.hunt")


class HuntBot:
    """The Worker / Repair Bot. Repairs, sandboxes, verifies, and delivers PRs."""

    def __init__(self, client: GitHubAppClient | None = None, policy: PipelinePolicy | None = None):
        self.client = client or GitHubAppClient()
        self.policy = policy or PipelinePolicy(mode="work")
        # Ensure work mode is enforced for Hunt
        self.policy.mode = "work"

    def execute_repair(self, ctx: TriggerContext) -> dict[str, Any]:
        """Execute full autonomous repair loop on the PR or repository."""
        pipeline = MaintenancePipeline(client=self.client, policy=self.policy)
        result: PipelineResult = pipeline.run(ctx)

        return {
            "success": True,
            "bot": "hunt",
            "mode": "work",
            "status": result.status,
            "mergeable": result.mergeable,
            "committed": result.committed,
            "commit_url": result.commit_url,
            "pr_url": result.pr_url,
            "comment_posted": bool(result.comment_body),
            "status_description": result.status_description,
        }


WorkBot = HuntBot
