# Copyright 2026 Koyote Authors
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import subprocess
import json


def _run_koyote_cli(args):
    env = dict(os.environ)
    env["PYTHONPATH"] = "python"
    env.setdefault("KOYOTE_LLM_KEY", "sk-ant-test-credential-key")
    return subprocess.run(
        [sys.executable, "-m", "koyote.cli.main"] + args,
        capture_output=True,
        text=True,
        env=env
    )


def test_cli_audit_default():
    result = _run_koyote_cli(["audit", "trials/fixtures/taxonomy_stripe/"])
    assert result.returncode == 0
    assert "KOYOTE: EXTERNAL-CHANGE DEPENDENCY AUDIT" in result.stdout
    assert "Stripe" in result.stdout


def test_cli_audit_github_issue():
    result = _run_koyote_cli(["audit", "trials/fixtures/taxonomy_stripe/", "--format=github-issue"])
    assert result.returncode == 0
    assert "# Koyote: External Dependency Map & Risk Register" in result.stdout
    assert "| **Stripe** |" in result.stdout


def test_cli_audit_json():
    result = _run_koyote_cli(["audit", "trials/fixtures/taxonomy_stripe/", "--format=json"])
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "total_providers_detected" in data
    assert "at_risk" in data


def test_cli_graph():
    result = _run_koyote_cli(["graph", "trials/fixtures/taxonomy_stripe/"])
    assert result.returncode == 0
    assert "KOYOTE: EXTERNAL-CHANGE DEPENDENCY GRAPH" in result.stdout


def test_cli_check_default():
    result = _run_koyote_cli(["check", "trials/fixtures/taxonomy_stripe/"])
    assert result.returncode == 0
    assert "KOYOTE: EXTERNAL-CHANGE DEPENDENCY AUDIT" in result.stdout
    assert "Stripe" in result.stdout


def test_cli_fix_detect():
    result = _run_koyote_cli(["fix", "trials/fixtures/taxonomy_stripe/", "--detect"])
    assert result.returncode == 0
    assert "KOYOTE AUTONOMOUS MAINTENANCE LOOP" in result.stdout

