# Copyright 2026 Koyote Authors
# SPDX-License-Identifier: Apache-2.0
"""Phase 3: STABLE -> CONFIRMED -> NOTIFIED. Work-naming Issues, fan-out, dedupe."""

import json
import os
import time

from koyote import cross_repo, work_graph
from koyote.github.provisioning import cached_path
from koyote.github.push_events import parse_push_payload
from koyote.github.pr_bot import handle_push_event


class StubPlanner:
    def __init__(self, body="impact", confidence="high"):
        self.body = body
        self.confidence = confidence
        self.calls = []

    def assess(self, **kwargs):
        self.calls.append(kwargs)
        return {"body": self.body, "confidence": self.confidence}


class FakeClient:
    def __init__(self):
        self.issues = []
        self.comments = []

    def create_issue(self, repo, title, body, labels=None):
        self.issues.append({"repo": repo, "title": title, "body": body})
        return {"html_url": f"https://example/{repo}/issues/{len(self.issues)}",
                "number": len(self.issues)}

    def post_pr_comment(self, repo, pr_number, body):
        self.comments.append({"repo": repo, "pr": pr_number, "body": body})
        return {"id": len(self.comments)}


def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("KOYOTE_WORK_GRAPH_FILE", str(tmp_path / "wg.json"))
    monkeypatch.setenv("KOYOTE_INSTALLATIONS_DIR", str(tmp_path / "installs"))
    monkeypatch.setenv("KOYOTE_REPOS_DIR", str(tmp_path / "repos"))
    os.makedirs(os.environ["KOYOTE_INSTALLATIONS_DIR"], exist_ok=True)


def _install(*repos):
    with open(os.path.join(os.environ["KOYOTE_INSTALLATIONS_DIR"], "1.json"), "w") as f:
        json.dump({"installation_id": "1",
                   "repos": {r: {"state": "READY"} for r in repos}}, f)


def _checkout(repo):
    path = cached_path(repo)
    os.makedirs(os.path.join(path, ".git"), exist_ok=True)
    return path


def _raw_push(repo, branch, after, files=("src/api.ts",)):
    return {"ref": f"refs/heads/{branch}", "before": "0" * 40, "after": after,
            "repository": {"full_name": repo}, "pusher": {"name": "dev1"},
            "commits": [{"id": after, "added": list(files), "removed": [], "modified": []}]}


def _setup(tmp_path, monkeypatch, consumers=("acme/admin",), confidence="high"):
    _env(tmp_path, monkeypatch)
    _install("acme/api-service", *consumers)
    for repo in consumers:
        co = _checkout(repo)
        with open(os.path.join(co, "client.ts"), "w") as f:
            f.write("import { x } from 'api-service';\n")
        work_graph.record_push(parse_push_payload(
            _raw_push(repo, "feature/work", "ddd", files=())))
    work_graph.record_push(parse_push_payload(
        _raw_push("acme/api-service", "feature/payments", "aaa")))
    monkeypatch.setattr(cross_repo, "scan_callsites",
                        lambda d, cfg: {"callsites": [{"file_path": "client.ts"}]}
                        if "__admin" in d or "__mobile" in d else {"callsites": []})
    stub = StubPlanner(confidence=confidence)
    monkeypatch.setattr(cross_repo.AIPatchPlanner, "from_env",
                        classmethod(lambda cls: stub))
    return stub


def _potential(tmp_path, monkeypatch, **kw):
    stub = _setup(tmp_path, monkeypatch, **kw)
    res = cross_repo.evaluate_candidate("acme/api-service", "feature/payments", planner=stub)
    assert res["status"] == work_graph.POTENTIAL
    return stub


def test_sweep_moves_only_quiet(tmp_path, monkeypatch):
    _potential(tmp_path, monkeypatch, confidence="medium")
    assert cross_repo.sweep_and_notify(FakeClient(), quiet_s=10**9) == []
    moved = work_graph.sweep_quiet(window_s=0, now=time.time() + 10**6)
    assert [m["status"] for m in moved] == [work_graph.STABLE]


def test_sweep_notifies_work_naming_issue(tmp_path, monkeypatch):
    _potential(tmp_path, monkeypatch, confidence="medium")
    client = FakeClient()
    before = open(os.path.join(
        __import__("koyote.github.provisioning", fromlist=["cached_path"]).cached_path("acme/admin"),
        "client.ts")).read()
    out = cross_repo.sweep_and_notify(client, quiet_s=0, now=time.time() + 10**6)
    assert out[0]["confirmed"] is True and out[0]["notified"] is True
    assert len(client.issues) == 1
    issue = client.issues[0]
    assert issue["repo"] == "acme/admin"
    assert "acme/admin" in issue["title"] and "feature/work" in issue["title"]
    assert "acme/api-service" in issue["title"] and "feature/payments" in issue["title"]
    assert "No code was modified" in issue["body"]
    cand = work_graph.get_candidate("acme/api-service", "feature/payments")
    assert cand["status"] == work_graph.NOTIFIED
    after = open(os.path.join(cached_path("acme/admin"), "client.ts")).read()
    assert before == after


def test_retract_leaves_no_notification(tmp_path, monkeypatch):
    _potential(tmp_path, monkeypatch, confidence="medium")
    monkeypatch.setattr(cross_repo, "scan_callsites", lambda d, cfg: {"callsites": []})
    client = FakeClient()
    out = cross_repo.sweep_and_notify(client, quiet_s=0, now=time.time() + 10**6)
    assert out[0]["confirmed"] is False
    assert client.issues == []
    assert work_graph.get_candidate("acme/api-service", "feature/payments")["status"] == work_graph.OBSERVED


def test_fanout_and_dedupe_and_pr_link(tmp_path, monkeypatch):
    _potential(tmp_path, monkeypatch, consumers=("acme/admin", "acme/mobile"), confidence="medium")
    work_graph.record_branch_activity("acme/admin", "feature/work", "ddd", open_pr=7)
    client = FakeClient()
    out = cross_repo.sweep_and_notify(client, quiet_s=0, now=time.time() + 10**6)
    assert len(out) == 1 and out[0]["notified"] is True
    assert len(client.issues) == 2
    assert len(client.comments) == 1
    assert client.comments[0]["pr"] == 7
    out2 = cross_repo.sweep_and_notify(client, quiet_s=0, now=time.time() + 10**6)
    assert out2 == []
    assert len(client.issues) == 2


def test_high_confidence_fastpath_on_push(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, confidence="high")
    client = FakeClient()
    res = handle_push_event(_raw_push("acme/api-service", "feature/payments", "aaa"), client)
    assert res["status"] == work_graph.NOTIFIED and res["notified"] is True
    assert len(client.issues) == 1


def test_medium_confidence_waits_for_stability(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, confidence="medium")
    client = FakeClient()
    res = handle_push_event(_raw_push("acme/api-service", "feature/payments", "aaa"), client)
    assert res["status"] == work_graph.POTENTIAL and not res["notified"]
    assert client.issues == []


def test_pr_opened_fastpath(tmp_path, monkeypatch):
    _potential(tmp_path, monkeypatch, confidence="medium")
    client = FakeClient()
    res = cross_repo.pr_fastpath({
        "action": "opened",
        "repository": {"full_name": "acme/api-service"},
        "pull_request": {"number": 3, "head": {"ref": "feature/payments", "sha": "aaa"},
                         "merged": False},
    }, client)
    assert res.get("confirmed") is True and res.get("notified") is True
    assert len(client.issues) == 1


def test_pr_event_without_candidate_untouched(tmp_path, monkeypatch):
    _env(tmp_path, monkeypatch)
    client = FakeClient()
    res = cross_repo.pr_fastpath({
        "action": "opened",
        "repository": {"full_name": "acme/unknown"},
        "pull_request": {"number": 1, "head": {"ref": "x", "sha": "y"}, "merged": False},
    }, client)
    assert res == {"fastpath": False}
    assert not os.path.exists(os.environ["KOYOTE_WORK_GRAPH_FILE"])
