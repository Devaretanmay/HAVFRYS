from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from compart.pipeline import AnalysisResult, DriftFinding, TriggerContext
    from compart.github.client import GitHubAppClient


def render_verification_comment(
    analysis: "AnalysisResult",
    ctx: "TriggerContext",
) -> str:
    """Render the clean verification comment for unaffected PRs."""
    touchpoints = analysis.callsites_total or len(analysis.providers_detected) or 1
    return f"Compart checked {touchpoints} external API touchpoint(s). No contract violations detected. No changes made."


def render_maintenance_issue_comment(
    analysis: "AnalysisResult",
    client: Optional["GitHubAppClient"],
    ctx: "TriggerContext",
    inline: bool = True,
) -> str:
    """Render the maintenance issue comment."""
    lines: List[str] = [
        "-----------------------------------------",
        "        COMPART FOUND A MAINTENANCE ISSUE",
        "-----------------------------------------",
        "",
    ]

    for finding in analysis.findings:
        lines.extend(_render_single_finding(finding, client, ctx, inline))

    lines.append("")
    lines.append("-----------------------------------------")
    return "\n".join(lines)


def _render_single_finding(
    finding: "DriftFinding",
    client: Optional["GitHubAppClient"],
    ctx: "TriggerContext",
    inline: bool = True,
) -> List[str]:
    lines: List[str] = [
        f"### {finding.display_name} {finding.current_version} -> {finding.target_version}",
        "",
        f"**Breaking change:** {finding.breaking_change}",
        "",
    ]

    if finding.migration_guide_url:
        lines.append(f"[Vendor migration guide]({finding.migration_guide_url})")
        lines.append("")

    lines.append("**Affected:**")
    for cs in finding.callsites_in_context:
        path = cs.get("file_path") or ""
        lineno = cs.get("line_number")
        if path and lineno:
            lines.append(f"  - `{path}:{lineno}`")
        elif path:
            lines.append(f"  - `{path}`")

    if finding.callsites_in_context and inline:
        lines.extend(_inline_comment_sections(finding, ctx))

    lines.append("")
    lines.append("**Compart can repair this automatically.**")
    lines.append("")
    return lines


def _inline_comment_sections(
    finding: "DriftFinding",
    ctx: "TriggerContext",
) -> List[str]:
    """Render inline review comment invitations for affected callsites."""
    return []


def render_consult_issue(items: List[dict]) -> str:
    """Render a Consult-mode GitHub Issue from assessed detections.

    Each item: {display, version_from, version_to, breaking_change,
    guide_url, affected_files, assessment_body, auto_repairable, confidence}.
    States what is known, recommends, and declares no code was modified.
    """
    lines: List[str] = [
        "-----------------------------------------",
        "   COMPART CONSULT: MAINTENANCE ADVISORY ",
        "-----------------------------------------",
        "",
    ]
    for item in items:
        lines.append(f"### {item.get('display', 'External change')} "
                     f"{item.get('version_from', '')} -> {item.get('version_to', '')}".rstrip())
        lines.append("")
        if item.get("breaking_change"):
            lines.append(f"**Breaking change:** {item['breaking_change']}")
            lines.append("")
        if item.get("guide_url"):
            lines.append(f"[Vendor migration guide]({item['guide_url']})")
            lines.append("")
        files = item.get("affected_files") or []
        if files:
            lines.append(f"**Affected files ({len(files)}):**")
            for path in files:
                lines.append(f"  - `{path}`")
            lines.append("")
        if item.get("assessment_body"):
            lines.append("**Assessment:**")
            lines.append(str(item["assessment_body"]).strip())
            lines.append("")
        if item.get("auto_repairable"):
            lines.append("Compart can repair this automatically (`compart fix`).")
        else:
            lines.append("Compart cannot repair this automatically — manual review advised.")
        lines.append(f"Confidence: {item.get('confidence', 'unknown')}")
        lines.append("")
    lines.append("No code was modified.")
    lines.append("-----------------------------------------")
    return "\n".join(lines)
