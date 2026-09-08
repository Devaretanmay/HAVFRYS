# Copyright 2026 Sheepdog Authors
# SPDX-License-Identifier: Apache-2.0
"""Doctor reports GitHub / AI / index / KB / test-cmd / monitoring states."""

import os
import shutil
import subprocess
import sys


def _run(args, env):
    return subprocess.run(
        [sys.executable, "-m", "sheepdog.cli.main"] + args,
        capture_output=True, text=True, env=env,
    )


def _env(tmp_path):
    env = dict(os.environ)
    env["PYTHONPATH"] = "python"
    env["SHEEPDOG_CREDENTIALS_FILE"] = str(tmp_path / "creds.json")
    env["SHEEPDOG_INSTALLATIONS_DIR"] = str(tmp_path / "inst")
    for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "SHEEPDOG_LLM_KEY",
              "GITHUB_TOKEN", "SHEEPDOG_GITHUB_TOKEN"):
        env.pop(k, None)
    return env


def test_doctor_all_states(tmp_path):
    env = _env(tmp_path)
    res = _run(["doctor"], env)
    assert res.returncode == 0
    for line in ("GitHub:", "AI provider:", "Indexed:", "Knowledge Base:",
                 "Test command:", "Monitoring:"):
        assert line in res.stdout
    assert "NOT CONFIGURED" in res.stdout
    assert "MISSING" in res.stdout


def test_doctor_ready_after_index(tmp_path):
    dst = str(tmp_path / "r")
    shutil.copytree("trials/fixtures/taxonomy_stripe", dst)
    env = _env(tmp_path)
    _run(["index", dst, "--write-graph"], env)
    res = subprocess.run(
        [sys.executable, "-m", "sheepdog.cli.main", "doctor"],
        capture_output=True, text=True, env=env, cwd=dst,
    )
    assert res.returncode == 0
    assert "Indexed:            YES" in res.stdout
    assert "Knowledge Base:     READY" in res.stdout


def test_app_serve_requires_secret(tmp_path):
    env = _env(tmp_path)
    env.pop("SHEEPDOG_WEBHOOK_SECRET", None)
    res = subprocess.run(
        [sys.executable, "-c",
         "from sheepdog.cli.main import cmd_app; "
         "import argparse; cmd_app(argparse.Namespace(app_action='serve', port=18099, secret=None, no_secret=False))"],
        capture_output=True, text=True, env=env,
    )
    assert res.returncode == 2
    assert "without a secret" in res.stdout
