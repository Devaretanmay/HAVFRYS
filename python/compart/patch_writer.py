"""PatchWriter - regex-based surgical file rewriter with unified diff output."""

import difflib
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from compart.providers.registry import RewriteRule


@dataclass
class PatchResult:
    file_path: str
    success: bool
    lines_changed: int
    unified_diff: str
    rules_applied: List[str] = field(default_factory=list)
    error: Optional[str] = None


_SKIP_DIRS = frozenset({
    ".git", "node_modules", ".next", "__pycache__", ".venv",
    "venv", "env", "dist", "build", "target", ".compart",
})


_IDENT = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*\Z")


def discover_aliases(repo_dir: str, provider: str) -> Dict[str, str]:
    """Map local client identifiers to their SDK: {"s": "stripe"}.

    Read from the static scan (zero-token). Only exact bindings the locator
    proved — never guessed. Used to scope rewrites precisely, never loosely.
    """
    from compart.autopatch import ScanConfig, scan_callsites

    try:
        result = scan_callsites(repo_dir, ScanConfig(sdk_names=[provider]))
    except Exception:
        return {}
    aliases: Dict[str, str] = {}
    for c in result.get("callsites", []):
        alias = c.get("alias")
        if alias and _IDENT.match(alias):
            aliases[alias] = provider.lower()
    return aliases


def instantiate_alias_rules(
    rules: List[RewriteRule],
    aliases: Dict[str, str],
) -> List[RewriteRule]:
    """Build exact-identifier variants of registry rules for aliased clients.

    Only rewrites rules whose regex pattern begins with the escaped SDK prefix
    `<sdk>\\.` — e.g. `stripe\\.subscriptions\\.del\\(` becomes
    `s\\.subscriptions\\.del\\(` for alias `s`. Same replacement, same files,
    same precision. Non-conforming rules and non-identifier aliases are skipped.
    """
    out: List[RewriteRule] = []
    for alias, sdk in aliases.items():
        if alias == sdk or not _IDENT.match(alias):
            continue
        prefix = re.escape(sdk) + r"\."
        for rule in rules:
            if not rule.is_regex or not rule.pattern.startswith(prefix):
                continue
            # Preserve the receiver: a replacement rooted at `stripe.` must be
            # re-rooted at the alias, otherwise the rewrite would reference an
            # undefined identifier and break the code it claims to repair.
            replacement = rule.replacement
            recv = sdk + "."
            if replacement.startswith(recv):
                replacement = alias + replacement[len(sdk):]
            out.append(RewriteRule(
                pattern=re.escape(alias) + "\\." + rule.pattern[len(prefix):],
                replacement=replacement,
                file_extensions=list(rule.file_extensions),
                description=f"{rule.description} (alias {alias})",
                is_regex=True,
            ))
    return out


def apply_rewrites(
    repo_dir: str,
    rules: List[RewriteRule],
    dry_run: bool = False,
) -> List[PatchResult]:
    """Walk repo_dir and apply regex rewrite rules to matching files.

    Returns one PatchResult per file that was modified (or would be in dry_run).
    Files outside repo_dir are never touched (blast-radius guard).
    """
    repo_dir = os.path.abspath(repo_dir)
    results: List[PatchResult] = []

    ext_to_rules: dict[str, List[RewriteRule]] = {}
    for rule in rules:
        for ext in rule.file_extensions:
            ext_to_rules.setdefault(ext, []).append(rule)

    for dirpath, dirnames, filenames in os.walk(repo_dir, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ext_to_rules:
                continue

            full_path = os.path.join(dirpath, filename)
            result = _rewrite_file(full_path, ext_to_rules[ext], dry_run)
            if result is not None:
                results.append(result)

    return results


def _rewrite_file(
    file_path: str,
    rules: List[RewriteRule],
    dry_run: bool,
) -> Optional[PatchResult]:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            original = f.read()
    except OSError as exc:
        return PatchResult(
            file_path=file_path,
            success=False,
            lines_changed=0,
            unified_diff="",
            error=str(exc),
        )

    current = original
    applied: List[str] = []

    for rule in rules:
        if rule.is_regex:
            try:
                new_text = re.sub(rule.pattern, rule.replacement, current)
            except re.error:
                continue
        else:
            new_text = current.replace(rule.pattern, rule.replacement)

        if new_text != current:
            applied.append(rule.description)
            current = new_text

    if current == original:
        return None

    original_lines = original.splitlines(keepends=True)
    new_lines = current.splitlines(keepends=True)
    rel_path = os.path.relpath(file_path)

    diff = "".join(difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
        lineterm="",
    ))

    lines_changed = sum(
        1 for line in diff.splitlines()
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
    )

    if not dry_run:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(current)
        except OSError as exc:
            return PatchResult(
                file_path=file_path,
                success=False,
                lines_changed=0,
                unified_diff="",
                rules_applied=applied,
                error=str(exc),
            )

    return PatchResult(
        file_path=file_path,
        success=True,
        lines_changed=lines_changed,
        unified_diff=diff,
        rules_applied=applied,
    )
