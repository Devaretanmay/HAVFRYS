# Copyright 2026 Compart Authors
# SPDX-License-Identifier: Apache-2.0
"""Compart Intelligence — invisible smart routing (blueprint box 5).

Single brain. User never picks --ai vs deterministic.
Decision = knowledge match → DIRECT (0 tokens) else AI if creds else QUARANTINE.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from compart.change_source import ChangeSource
from compart.credentials import has_valid_credentials
from compart.knowledge import direct_rewrites_for
from compart.providers.registry import find_migration_for, get_default_registry


@dataclass
class Decision:
    strategy: str  # DIRECT | AI | HYBRID | QUARANTINE (internal only, never a CLI flag)
    reason: str
    elapsed_ms: int = 0
    provider: str = ""
    from_version: str = ""
    to_version: str = ""
    confidence: float = 0.0
    estimated_tokens: Optional[int] = None  # None = unknown; 0 = verified zero-token path
    expected_blast_radius: List[str] = field(default_factory=list)
    verification_required: bool = True


def resolve_migration(provider: str, from_version: Optional[str] = None, to_version: Optional[str] = None):
    """Pick the registry migration matching the requested versions, else first. Returns (from, to, migration|None)."""
    migration = find_migration_for(ChangeSource.sdk(
        provider or "", version_from=from_version or "unknown", version_to=to_version or "unknown"))
    if migration is None:
        return (from_version or "unknown", to_version or "unknown", None)
    return (from_version or migration.from_version, to_version or migration.to_version, migration)


class CompartIntelligence:
    """Reason over change + repo knowledge base, pick cheapest safe path."""

    def decide(
        self,
        repo_dir: str,
        provider: str,
        from_version: Optional[str] = None,
        to_version: Optional[str] = None,
        has_rewrites: bool = False,
        kb_hit: Optional[bool] = None,
    ) -> Decision:
        t0 = time.time()
        registry = get_default_registry()
        p_spec = registry.get(provider) if provider else None
        if not p_spec:
            return Decision(strategy="QUARANTINE", reason="unknown provider", elapsed_ms=int((time.time()-t0)*1000), provider=provider or "", from_version=from_version or "", to_version=to_version or "")

        actual_from, actual_to, _mig = resolve_migration(provider, from_version, to_version)

        hit = kb_hit
        if hit is None:
            hit = len(direct_rewrites_for(repo_dir, provider, actual_from, actual_to)) > 0

        if hit or has_rewrites:
            elapsed = int((time.time() - t0) * 1000)
            reason = "kb_hit" if hit else "registry_rewrite"
            return Decision(strategy="DIRECT", reason=reason, elapsed_ms=elapsed, provider=provider, from_version=actual_from, to_version=actual_to,
                            confidence=0.95, estimated_tokens=0)

        if has_valid_credentials():
            elapsed = int((time.time() - t0) * 1000)
            return Decision(strategy="AI", reason="novel_no_kb_match", elapsed_ms=elapsed, provider=provider, from_version=actual_from, to_version=actual_to,
                            confidence=0.5, estimated_tokens=None)

        elapsed = int((time.time() - t0) * 1000)
        return Decision(strategy="QUARANTINE", reason="no_credentials_for_ai", elapsed_ms=elapsed, provider=provider, from_version=actual_from, to_version=actual_to,
                        confidence=0.0, estimated_tokens=None)

    def decide_for_source(self, repo_dir: str, source: ChangeSource) -> Decision:
        """Generalized entry point: route any change source, not just vendor SDKs."""
        t0 = time.time()
        migration = find_migration_for(source)
        if migration is None:
            # No registry connector for this kind — AI if possible, else quarantine.
            if has_valid_credentials():
                return Decision(strategy="AI", reason=f"no_connector_for_{source.kind}",
                                elapsed_ms=int((time.time() - t0) * 1000),
                                provider=source.provider, from_version=source.version_from,
                                to_version=source.version_to, confidence=0.4, estimated_tokens=None)
            return Decision(strategy="QUARANTINE", reason=f"no_connector_for_{source.kind}",
                            elapsed_ms=int((time.time() - t0) * 1000),
                            provider=source.provider, from_version=source.version_from,
                            to_version=source.version_to, confidence=0.0, estimated_tokens=None)
        return self.decide(repo_dir, source.provider, source.version_from, source.version_to,
                           has_rewrites=bool(migration.rewrites))
