# Copyright 2026 Koyote Authors
# SPDX-License-Identifier: Apache-2.0
"""Phase 2: cheap match -> active-work filter -> gated AI -> POTENTIAL. Silent."""

import json
import os
import time

from koyote import cross_repo, work_graph
from koyote.github.provisioning import cached_path
from koyote.github.push_events import parse_push_payload


class StubPlanner:
    def __init__(self, body="impact confirmed"):
        self.body = body
        self.calls = []

    def assess(self, **kwargs):
        self.calls.append(kwargs)
        return {"body": self.body, "confidence": "high"}


def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("KOYOTE_WORK_GRAPH_FILE", str(tmp_path / "wg.json"))
    monkeypatch.setenv("KOYOTE_INSTALLATIONS_DIR", str(tmp_path / "installs"))
    monkeypatch.setenv("KOYOTE_REPOS_DIR", str(tmp_path / "repos"))
    os.makedirs(os.environ["KOYOTE_INSTALLATIONS_DIR"], exist_ok=True)


def _install(*repos):
    rec = {"installation_id": "1", "repos": {r: {"state": "READY"} for r in repos}}
    with open(os.path.join(os.environ["KOYOTE_INSTALLATIONS_DIR"], "1.json"), "w") as f:
        json.dump(rec, f)


def _checkout(repo, with_git=True):
    path = cached_path(repo)
    os.makedirs(os.path.join(path, ".git") if with_git else path, exist_ok=True)
    return path


def _push(repo="acme/api-service", branch="feature/payments", after="abc123"):
    return parse_push_payload({
        "ref": f"refs/heads/{branch}", "before": "0" * 40, "after": after,
        "repository": {"full_name": repo}, "pusher": {"name": "dev1"},
        "commits": [{"id": after, "message": "change api",
                      "added": ["src/api.ts"], "removed": [], "modified": []}],
    })


def test_changed_files_union(tmp_path, monkeypatch):
    _env(tmp_path, monkeypatch)
    work_graph.record_push(_push(after="aaa"))
    cand = work_graph.record_push({**_push(after="bbb"),
                                   "commits": [{"id": "bbb", "added": ["src/other.ts"],
                                                "removed": [], "modified": ["src/api.ts"]}]})
    assert sorted(work_graph.candidate_changed_files(cand)) == ["src/api.ts", "src/other.ts"]


def _consumer_setup(tmp_path, monkeypatch, active=True):
    _env(tmp_path, monkeypatch)
    _install("acme/api-service", "acme/admin", "acme/billing")
    admin = _checkout("acme/admin")
    with open(os.path.join(admin, "client.ts"), "w") as f:
        f.write("import { x } from 'api-service';\n")
    billing = _checkout("acme/billing")
    with open(os.path.join(billing, "inv.ts"), "w") as f:
        f.write("console.log('unrelated');\n")
    work_graph.record_push(_push())
    work_graph.record_push({**_push(repo="acme/admin", branch="feature/checkout", after="ddd"),
                            "commits": []})
    if not active:
        g = work_graph.load_graph()
        g["branches"]["acme/admin#feature/checkout"]["last_push_ts"] = (
            time.time() - work_graph.DEFAULT_ACTIVE_WINDOW_S - 1)
        work_graph.save_graph(g)
    monkeypatch.setattr(cross_repo, "scan_callsites",
                        lambda d, cfg: {"callsites": [{"file_path": "client.ts"}]}
                        if d.endswith("acme__admin") else {"callsites": []})
    return admin


def test_matcher_filters_to_active_consumers(tmp_path, monkeypatch):
    _consumer_setup(tmp_path, monkeypatch)
    targets = cross_repo.find_plausible_targets("acme/api-service", "feature/payments")
    assert [(t["repository"], t["branch"]) for t in targets] == [("acme/admin", "feature/checkout")]


def test_stale_branch_excluded(tmp_path, monkeypatch):
    _consumer_setup(tmp_path, monkeypatch, active=False)
    assert cross_repo.find_plausible_targets("acme/api-service", "feature/payments") == []


def test_ai_gated_to_plausible_pairs_only(tmp_path, monkeypatch):
    _consumer_setup(tmp_path, monkeypatch)
    stub = StubPlanner()
    res = cross_repo.evaluate_candidate("acme/api-service", "feature/payments", planner=stub)
    assert res["status"] == work_graph.POTENTIAL
    assert len(stub.calls) == 1
    assert stub.calls[0]["provider_name"] == "acme/api-service"
    assert "Active Work Context" in stub.calls[0]["migration_details"]
    cand = work_graph.get_candidate("acme/api-service", "feature/payments")
    assert cand["status"] == work_graph.POTENTIAL
    assert cand["potential_targets"][0]["repository"] == "acme/admin"


def test_ai_never_called_without_plausible_target(tmp_path, monkeypatch):
    _env(tmp_path, monkeypatch)
    _install("acme/api-service")
    work_graph.record_push(_push())
    stub = StubPlanner()
    res = cross_repo.evaluate_candidate("acme/api-service", "feature/payments", planner=stub)
    assert res["status"] == work_graph.OBSERVED
    assert stub.calls == []


def test_empty_assessment_retracts(tmp_path, monkeypatch):
    _consumer_setup(tmp_path, monkeypatch)
    res = cross_repo.evaluate_candidate("acme/api-service", "feature/payments",
                                        planner=StubPlanner(body=""))
    assert res["status"] == work_graph.OBSERVED


def test_no_credentials_fail_closed(tmp_path, monkeypatch):
    _consumer_setup(tmp_path, monkeypatch)
    monkeypatch.setattr(cross_repo.AIPatchPlanner, "from_env", classmethod(lambda cls: None))
    res = cross_repo.evaluate_candidate("acme/api-service", "feature/payments")
    assert res == {"evaluated": False, "reason": "no_credentials_for_ai"}
    assert work_graph.get_candidate("acme/api-service", "feature/payments")["status"] == work_graph.OBSERVED
