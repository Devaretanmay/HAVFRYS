"""Framework integration hooks for Sheepdog.

This package lets AI agents from Category A (coding assistants) and
Category C (data / RAG agents) run their code inside kernel-enforced
:class:`sheepdog.AgentSheepdog` compartments.

Hooks are intentionally dependency-light: each framework (LangChain,
LangGraph, CrewAI, AutoGen) is an optional import, and every hook degrades to a
plain duck-typed object when the framework is absent. The only hard
dependency is the Sheepdog runtime itself.

Available hooks:

* :mod:`sheepdog.hooks.langchain` : ``SheepdogPythonREPLTool``, ``SheepdogGraphNode``
* :mod:`sheepdog.hooks.crewai` : ``SheepdogCodeInterpreterTool``, ``CrewAICodeExecutor``
* :mod:`sheepdog.hooks.autogen` : ``SheepdogCodeExecutor`` (+ ``CodeBlock`` / ``CodeResult``)
* :mod:`sheepdog.hooks.data_agent` : ``DataScienceSandboxHook``, ``DataSandboxConfig``
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
from .langchain import SheepdogGraphNode, SheepdogPythonREPLTool
from .crewai import SheepdogCodeInterpreterTool, CrewAICodeExecutor
from .autogen import SheepdogCodeExecutor, CodeBlock, CodeResult
from .data_agent import DataSandboxConfig, DataScienceSandboxHook

__all__ = [
    "VALID_PERMISSIONS",
    "DEFAULT_PERMISSIONS",
    "ExecutionResult",
    "SandboxRunner",
    "validate_permissions",
    "index_workdir",
    "diff_trees",
    "SheepdogPythonREPLTool",
    "SheepdogGraphNode",
    "SheepdogCodeInterpreterTool",
    "CrewAICodeExecutor",
    "SheepdogCodeExecutor",
    "CodeBlock",
    "CodeResult",
    "DataScienceSandboxHook",
    "DataSandboxConfig",
]