# Copyright 2026 Koyote Authors
# SPDX-License-Identifier: Apache-2.0
"""Tests for Howl and Hunt separate bots."""

from unittest.mock import MagicMock
from koyote.github.howl_bot import HowlBot
from koyote.github.hunt_bot import HuntBot
from koyote.pipeline import TriggerContext


def test_howl_bot_never_modifies_files(tmp_path):
    client = MagicMock()
    howl = HowlBot(client=client)
    ctx = TriggerContext(
        event_id="test-1",
        event_type="pull_request.opened",
        repository="owner/repo",
        ref="feat",
        sha="abc1234",
        workdir=str(tmp_path),
        pr_number=10,
    )
    res = howl.review_pull_request(ctx)
    assert res["success"] is True
    assert res["bot"] == "howl"
    assert res["findings_count"] == 0
    client.post_pr_comment.assert_called_once()
    assert "Howl Review" in client.post_pr_comment.call_args[0][2]


def test_hunt_bot_executes_pipeline_with_work_mode(tmp_path):
    client = MagicMock()
    hunt = HuntBot(client=client)
    assert hunt.policy.mode == "work"
    ctx = TriggerContext(
        event_id="test-2",
        event_type="pull_request.opened",
        repository="owner/repo",
        ref="feat",
        sha="abc1234",
        workdir=str(tmp_path),
        pr_number=10,
    )
    res = hunt.execute_repair(ctx)
    assert res["success"] is True
    assert res["bot"] == "hunt"
