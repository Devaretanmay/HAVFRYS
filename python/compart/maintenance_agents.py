from dataclasses import dataclass, field
from typing import Any, Dict, List

from compart.change_source import ChangeSource
from compart.graph import build_dependency_graph


@dataclass
class ImpactAnalysisResult:
    provider: str
    affected_files: List[str]
    callsites_count: int
    wrapper_files: List[str]
    callsites: List[Dict[str, Any]] = field(default_factory=list)


class ImpactAnalyst:
    def analyze_impact(self, repo_dir: str, provider_name: str) -> ImpactAnalysisResult:
        """Provider path preserved: vendors match by SDK name (one branch of the general matcher)."""
        return self.analyze_impact_for(repo_dir, ChangeSource.sdk(provider_name))

    def analyze_impact_for(self, repo_dir: str, source: Any) -> ImpactAnalysisResult:
        """General matcher: identity against wrapper metadata, callsite patterns, and file paths."""
        identity = (getattr(source, "identity", "") or "").lower()
        provider_name = (getattr(source, "provider", "") or identity) or ""
        graph = build_dependency_graph(repo_dir)
        affected_files = set()
        wrappers = []
        matched_callsites = []

        for w in graph.get("wrappers", []):
            hay = f"{w.get('wrapper_file', '')} {w.get('wraps_provider', '')}".lower()
            if identity and identity in hay:
                wrappers.append(w.get("wrapper_file"))
                affected_files.add(w.get("wrapper_file"))

        for c in graph.get("callsites", []):
            hay = f"{c.get('function_name', '')} {c.get('matched_pattern', '')} {c.get('file_path', '')}".lower()
            if identity and identity in hay:
                matched_callsites.append(c)
                affected_files.add(c.get("file_path"))

        return ImpactAnalysisResult(
            provider=provider_name,
            affected_files=sorted(list(affected_files)),
            callsites_count=len(matched_callsites),
            wrapper_files=wrappers,
            callsites=matched_callsites,
        )
