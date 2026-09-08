"""Framework integration hooks for Koyote.

This package lets AI agents from Category A (coding assistants) and
Category C (data / RAG agents) run their code inside kernel-enforced
:class:`koyote.AgentKoyote` compartments.

Hooks are intentionally dependency-light: each framework (LangChain,
LangGraph, CrewAI, AutoGen) is an optional import, and every hook degrades to a
plain duck-typed object when the framework is absent. The only hard
dependency is the Koyote runtime itself.

Available hooks:

* :mod:`koyote.hooks.langchain` : ``KoyotePythonREPLTool``, ``KoyoteGraphNode``
* :mod:`koyote.hooks.crewai` : ``KoyoteCodeInterpreterTool``, ``CrewAICodeExecutor``
* :mod:`koyote.hooks.autogen` : ``KoyoteCodeExecutor`` (+ ``CodeBlock`` / ``CodeResult``)
* :mod:`koyote.hooks.data_agent` : ``DataScienceSandboxHook``, ``DataSandboxConfig``
"""

from __future__ import annotations

from .base import (
    DEFAULT_PERMISSIONS,
    VALID_PERMISSIONS,
    ExecutionResult,
    SandboxRunner,
    diff_trees,
    index_workdir,
    validate_permissions,
)
from .langchain import KoyoteGraphNode, KoyotePythonREPLTool
from .crewai import KoyoteCodeInterpreterTool, CrewAICodeExecutor
from .autogen import KoyoteCodeExecutor, CodeBlock, CodeResult
from .data_agent import DataSandboxConfig, DataScienceSandboxHook

__all__ = [
    "VALID_PERMISSIONS",
    "DEFAULT_PERMISSIONS",
    "ExecutionResult",
    "SandboxRunner",
    "validate_permissions",
    "index_workdir",
    "diff_trees",
    "KoyotePythonREPLTool",
    "KoyoteGraphNode",
    "KoyoteCodeInterpreterTool",
    "CrewAICodeExecutor",
    "KoyoteCodeExecutor",
    "CodeBlock",
    "CodeResult",
    "DataScienceSandboxHook",
    "DataSandboxConfig",
]