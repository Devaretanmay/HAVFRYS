"""AI-powered patch generation and self-repair planner using BYOK LLMs."""

import difflib
import os
import re
from typing import List, Optional, Tuple

from compart.llm import LLMClient, resolve_llm_config
from compart.patch_writer import PatchResult


_BLOCK_REGEX = re.compile(
    r"<<<<<<< SEARCH\s*\n(.*?)\n=======\s*\n(.*?)\n>>>>>>> REPLACE",
    re.DOTALL,
)


def parse_search_replace_blocks(text: str) -> List[Tuple[str, str]]:
    """Extract search and replace pairs from model output."""
    matches = _BLOCK_REGEX.findall(text)
    return [(search, replace) for search, replace in matches]


class AIPatchPlanner:
    """Generates surgical code patches using LLMs with self-repair support."""

    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client

    @classmethod
    def from_env(
        cls,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> Optional["AIPatchPlanner"]:
        cfg = resolve_llm_config(api_key=api_key, model=model, base_url=base_url)
        if not cfg:
            return None
        return cls(client=LLMClient(cfg))

    def plan_and_apply(
        self,
        repo_dir: str,
        affected_files: List[str],
        provider_name: str,
        from_version: str,
        to_version: str,
        migration_details: str = "",
        test_error: Optional[str] = None,
        dry_run: bool = False,
    ) -> List[PatchResult]:
        """Generate and apply AI patches for affected files."""
        if not self.client:
            return []

        results = []
        for file_path in affected_files:
            abs_path = file_path if os.path.isabs(file_path) else os.path.join(repo_dir, file_path)
            if not os.path.isfile(abs_path):
                continue

            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                original_content = f.read()

            patch_res = self._patch_file(
                abs_path=abs_path,
                repo_dir=repo_dir,
                original_content=original_content,
                provider_name=provider_name,
                from_version=from_version,
                to_version=to_version,
                migration_details=migration_details,
                test_error=test_error,
                dry_run=dry_run,
            )
            if patch_res:
                results.append(patch_res)

        return results

    def _patch_file(
        self,
        abs_path: str,
        repo_dir: str,
        original_content: str,
        provider_name: str,
        from_version: str,
        to_version: str,
        migration_details: str,
        test_error: Optional[str],
        dry_run: bool,
    ) -> Optional[PatchResult]:
        system_prompt = (
            "You are an expert autonomous software engineer performing external API migrations.\n"
            "Generate surgical code updates to adapt to breaking upstream API changes.\n"
            "Format your patch using search-and-replace blocks:\n"
            "<<<<<<< SEARCH\n"
            "exact lines to replace\n"
            "=======\n"
            "replacement lines\n"
            ">>>>>>> REPLACE\n"
            "Rules:\n"
            "1. Only modify lines directly affected by the API migration.\n"
            "2. Preserve exact formatting, indentation, and unrelated logic.\n"
            "3. Do not include markdown commentary outside the blocks."
        )

        user_content = (
            f"File: {os.path.relpath(abs_path, repo_dir)}\n"
            f"Provider: {provider_name}\n"
            f"Migration: {from_version} -> {to_version}\n"
            f"Migration Context: {migration_details}\n\n"
            f"File Content:\n```\n{original_content}\n```\n"
        )

        if test_error:
            user_content += (
                f"\nNOTE: A previous patch attempt caused test failure:\n"
                f"```\n{test_error[:1500]}\n```\n"
                f"Please fix the code to resolve this test failure."
            )

        messages = [{"role": "user", "content": user_content}]
        try:
            resp = self.client.complete(messages=messages, system_prompt=system_prompt)
        except Exception as exc:
            return PatchResult(
                file_path=abs_path,
                success=False,
                lines_changed=0,
                unified_diff="",
                error=f"LLM call failed: {exc}",
            )

        blocks = parse_search_replace_blocks(resp.content)
        if not blocks:
            return None

        current = original_content
        applied_rules = []
        for search, replace in blocks:
            if search in current:
                current = current.replace(search, replace, 1)
                applied_rules.append(f"AI migration for {provider_name}")

        if current == original_content:
            return None

        orig_lines = original_content.splitlines(keepends=True)
        new_lines = current.splitlines(keepends=True)
        rel_path = os.path.relpath(abs_path, repo_dir)

        diff = "".join(difflib.unified_diff(
            orig_lines,
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
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(current)

        return PatchResult(
            file_path=abs_path,
            success=True,
            lines_changed=lines_changed,
            unified_diff=diff,
            rules_applied=applied_rules,
        )
