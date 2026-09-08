"""Framework integration hooks for Volf.

This package lets AI agents from Category A (coding assistants) and
Category C (data / RAG agents) run their code inside kernel-enforced
:class:`volf.AgentVolf` compartments.

Hooks are intentionally dependency-light: each framework (LangChain,
LangGraph, CrewAI, AutoGen) is an optional import, and every hook degrades to a
plain duck-typed object when the framework is absent. The only hard
dependency is the Volf runtime itself.

Available hooks:

* :mod:`volf.hooks.langchain` : ``VolfPythonREPLTool``, ``VolfGraphNode``
* :mod:`volf.hooks.crewai` : ``VolfCodeInterpreterTool``, ``CrewAICodeExecutor``
* :mod:`volf.hooks.autogen` : ``VolfCodeExecutor`` (+ ``CodeBlock`` / ``CodeResult``)
* :mod:`volf.hooks.data_agent` : ``DataScienceSandboxHook``, ``DataSandboxConfig``
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
from .langchain import VolfGraphNode, VolfPythonREPLTool
from .crewai import VolfCodeInterpreterTool, CrewAICodeExecutor
from .autogen import VolfCodeExecutor, CodeBlock, CodeResult
from .data_agent import DataSandboxConfig, DataScienceSandboxHook

__all__ = [
    "VALID_PERMISSIONS",
    "DEFAULT_PERMISSIONS",
    "ExecutionResult",
    "SandboxRunner",
    "validate_permissions",
    "index_workdir",
    "diff_trees",
    "VolfPythonREPLTool",
    "VolfGraphNode",
    "VolfCodeInterpreterTool",
    "CrewAICodeExecutor",
    "VolfCodeExecutor",
    "CodeBlock",
    "CodeResult",
    "DataScienceSandboxHook",
    "DataSandboxConfig",
]