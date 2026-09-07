from unittest.mock import MagicMock, patch

from compart.config import PipelinePolicy
from compart.github.pr_bot import (
    handle_pull_request_event,
    handle_installation_event,
    render_day0_onboarding_issue,
    make_pr_bot_handler,
    _extract_changed_files,
    _safe_preview,
)


def test_extract_changed_files_from_payload():
    payload_files = {
        "pull_request": {
            "files": [{"filename": "src/api.ts"}, {"filename": "package.json"}]
        }
    }
    assert _extract_changed_files(payload_files) == ["src/api.ts", "package.json"]

    payload_meta = {
        "compart": {"changed_files": ["lib/stripe.ts"]}
    }
    assert _extract_changed_files(payload_meta) == ["lib/stripe.ts"]

    assert _extract_changed_files({}) == []


def test_safe_preview():
    text = "line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8"
    preview = _safe_preview(text)
    assert len(preview.splitlines()) == 6
    assert _safe_preview("") == ""


def test_handle_pull_request_event_validation_failures():
    client = MagicMock()
    policy = PipelinePolicy()

    res_no_pr = handle_pull_request_event({}, "pull_request.opened", client, policy)
    assert res_no_pr["success"] is False
    assert "No pull_request" in res_no_pr["error"]

    res_no_repo = handle_pull_request_event(
        {"pull_request": {"number": 1}},
        "pull_request.opened",
        client,
        policy,
    )
    assert res_no_repo["success"] is False
    assert "No repository" in res_no_repo["error"]

    res_no_head = handle_pull_request_event(
        {"pull_request": {"number": 1}, "repository": {"full_name": "acme/repo"}},
        "pull_request.opened",
        client,
        policy,
    )
    assert res_no_head["success"] is False
    assert "Missing PR head info" in res_no_head["error"]


def test_make_pr_bot_handler_dispatches_events():
    client = MagicMock()
    policy = PipelinePolicy()

    handler = make_pr_bot_handler(client=client, policy=policy)

    res_unhandled = handler({}, "issues.opened")
    assert res_unhandled["success"] is True
    assert res_unhandled["handled"] is False

    with patch("compart.github.pr_bot.handle_pull_request_event") as mock_handle_pr:
        mock_handle_pr.return_value = {"success": True, "handled_pr": True}
        res_pr = handler({"pull_request": {}}, "pull_request.opened")
        assert res_pr["handled_pr"] is True
        mock_handle_pr.assert_called_once()

    with patch("compart.github.pr_bot.handle_external_change_event") as mock_handle_ext:
        mock_handle_ext.return_value = {"success": True, "handled_ext": True}
        res_ext = handler({}, "external.change.drift")
        assert res_ext["handled_ext"] is True
        mock_handle_ext.assert_called_once()

    with patch("compart.github.pr_bot.handle_installation_event") as mock_handle_inst:
        mock_handle_inst.return_value = {"success": True, "handled_inst": True}
        res_inst = handler({"repositories": []}, "installation.created")
        assert res_inst["handled_inst"] is True
        mock_handle_inst.assert_called_once()


def test_handle_installation_event():
    client = MagicMock()
    payload = {
        "action": "created",
        "repositories": [{"full_name": "acme/backend"}, {"full_name": "acme/frontend"}],
    }
    res = handle_installation_event(payload, "installation.created", client)
    assert res["success"] is True
    assert res["repositories_onboarded"] == ["acme/backend", "acme/frontend"]
    assert client.create_issue.call_count == 2


def test_render_day0_onboarding_issue():
    content = render_day0_onboarding_issue("acme/backend")
    assert "COMPART DAY-0 REPOSITORY ONBOARDING" in content
    assert "acme/backend" in content
    assert "Continuous Guard Status:" in content


def test_handle_pull_request_event_mergeable_flag():
    client = MagicMock()
    policy = PipelinePolicy()
    payload = {
        "action": "opened",
        "repository": {"full_name": "acme/backend"},
        "pull_request": {
            "number": 5,
            "title": "Clean PR",
            "body": "No changes",
            "head": {"ref": "feat", "sha": "123"},
            "base": {"ref": "main"},
        },
    }
    with patch("compart.github.pr_bot.MaintenancePipeline") as mock_pipe_cls:
        mock_pipe = mock_pipe_cls.return_value
        mock_result = MagicMock()
        mock_result.status = "clean"
        mock_result.mergeable = True
        mock_result.check_state = "success"
        mock_result.status_description = "clean"
        mock_result.comment_body = "clean comment"
        mock_pipe.run.return_value = mock_result

        res = handle_pull_request_event(payload, "pull_request.opened", client, policy)
        assert res["success"] is True
        assert res["mergeable"] is True
        assert res["check_state"] == "success"
