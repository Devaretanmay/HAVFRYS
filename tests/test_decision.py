# Copyright 2026 Compart Authors
# SPDX-License-Identifier: Apache-2.0
"""Decision engine: automatic strategy selection, hidden from users (no CLI flag)."""

import subprocess
import sys

from compart.change_source import ChangeSource
from compart.intelligence import CompartIntelligence, Decision
from compart.providers.registry import find_migration_for


def test_direct_for_known_sdk_rewrite():
    d = CompartIntelligence().decide("/tmp", "stripe", "11.18.0", "13.0.0", has_rewrites=True)
    assert d.strategy == "DIRECT"
    assert d.estimated_tokens == 0
    assert d.confidence > 0.9
    assert d.verification_required is True


def test_quarantine_without_creds_or_rewrites(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPART_CREDENTIALS_FILE", str(tmp_path / "none.json"))
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "COMPART_LLM_KEY"):
        monkeypatch.delenv(k, raising=False)
    d = CompartIntelligence().decide(str(tmp_path), "twilio", "1.0", "2.0", has_rewrites=False)
    assert d.strategy == "QUARANTINE"
    assert d.confidence == 0.0


def test_no_direct_or_ai_cli_flag():
    res = subprocess.run(
        [sys.executable, "-m", "compart.cli.main", "fix", "--help"],
        capture_output=True, text=True, env={"PYTHONPATH": "python", "PATH": "/usr/bin:/bin"},
    )
    assert "--direct" not in res.stdout
    assert "--ai" not in res.stdout


def test_find_migration_for_sdk_kind():
    m = find_migration_for(ChangeSource.sdk("stripe", version_to="13.0.0"))
    assert m is not None and m.to_version == "13.0.0"


def test_find_migration_for_future_kinds_returns_none():
    for kind in ("openapi", "graphql", "protobuf", "webhook", "mcp_server", "internal_service"):
        assert find_migration_for(ChangeSource(kind=kind, identity="x")) is None


def test_decide_for_source_future_kind_quarantines_without_creds(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPART_CREDENTIALS_FILE", str(tmp_path / "none.json"))
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "COMPART_LLM_KEY"):
        monkeypatch.delenv(k, raising=False)
    d = CompartIntelligence().decide_for_source(
        str(tmp_path), ChangeSource(kind="mcp_server", identity="internal-tools"))
    assert d.strategy == "QUARANTINE"
    assert "mcp_server" in d.reason


def test_decision_fields_have_sane_defaults():
    d = Decision(strategy="DIRECT", reason="test")
    assert d.confidence == 0.0
    assert d.estimated_tokens is None
    assert d.expected_blast_radius == []
    assert d.verification_required is True
