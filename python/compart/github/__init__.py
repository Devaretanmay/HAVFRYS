"""Compart GitHub App & Webhook Integration Module."""

from .client import (
    GitHubAppClient,
    verify_webhook_signature,
)
from .trust_pr import generate_trust_pr_markdown, TrustPRMetadata
from .webhook_server import WebhookServer, handle_webhook_payload
from .pr_bot import (
    handle_pull_request_event,
    handle_external_change_event,
    handle_installation_event,
    render_day0_onboarding_issue,
    make_pr_bot_handler,
    run_on_pr_locally,
)

__all__ = [
    "GitHubAppClient",
    "verify_webhook_signature",
    "generate_trust_pr_markdown",
    "TrustPRMetadata",
    "WebhookServer",
    "handle_webhook_payload",
    "handle_pull_request_event",
    "handle_external_change_event",
    "handle_installation_event",
    "render_day0_onboarding_issue",
    "make_pr_bot_handler",
    "run_on_pr_locally",
]
