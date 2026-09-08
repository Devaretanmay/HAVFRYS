# Copyright 2026 Volf Authors
# SPDX-License-Identifier: Apache-2.0
"""Detection-vs-repair split: detect_changes classifies without patching."""

import os
import shutil

from volf.change_source import IMPACT_DIRECT
from volf.drift import detect_changes


def test_stripe_fixture_detects_direct_impact():
    dets = detect_changes("trials/fixtures/taxonomy_stripe", "stripe")
    assert len(dets) == 1
    d = dets[0]
    assert d.outcome == IMPACT_DIRECT
    assert d.callsite_count > 0 and d.affected_files
    assert d.ai_dependent is False


def test_empty_repo_detects_nothing(tmp_path):
    assert detect_changes(str(tmp_path)) == []


def test_check_writes_nothing_outside_sheepdog(tmp_path):
    dst = str(tmp_path / "r")
    shutil.copytree("trials/fixtures/taxonomy_stripe", dst)
    before = {}
    for dirpath, dirnames, filenames in os.walk(dst):
        dirnames[:] = [d for d in dirnames if d not in {".volf"}]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            before[fp] = open(fp, "rb").read()
    from volf.audit import run_audit
    run_audit(dst, output_format="json", write_graph=True)
    for fp, content in before.items():
        assert open(fp, "rb").read() == content
