# Sheepdog Framework Integration Hooks

Run AI agent code inside kernel-enforced compartments from any major agent framework. Sheepdog provides lightweight, drop-in tool wrappers for popular Python agent frameworks.

---

## 1. LangGraph Integration

Wrap any LangGraph node execution inside an isolated compartment:

```python
from sheepdog.hooks import SheepdogGraphNode
from langgraph.graph import StateGraph, START, END

def data_processing_node(state, ctx):
    # This code executes inside an isolated kernel compartment
    with open(f"{ctx.workdir}/output.txt", "w") as f:
        f.write(state["value"].upper())
    return {"status": "complete"}

node = SheepdogGraphNode(data_processing_node, workdir=".")

builder = StateGraph(dict)
builder.add_node("process", node.attach(builder))
builder.add_edge(START, "process")
builder.add_edge("process", END)
```

---

## 2. LangChain Integration

Replace standard Python REPL tools with a kernel-enforced sandboxed version:

```python
from sheepdog.hooks import SheepdogPythonREPLTool

# Create a sandboxed Python REPL tool
tool = SheepdogPythonREPLTool(permissions=["fs_read", "fs_write"])

# Execute agent-generated code safely
result = tool.invoke("print(21 * 2)")
print(result)
```

---

## 3. CrewAI Integration

Replace Docker-based code execution in CrewAI with native sub-millisecond Sheepdog sandboxing:

```python
from crewai import Agent
from sheepdog.hooks import SheepdogCodeInterpreterTool

# Initialize agent with Sheepdog code interpreter
agent = Agent(
    role="Data Analyst",
    goal="Analyze logs safely",
    tools=[SheepdogCodeInterpreterTool(permissions=["fs_read"])]
)
```

---

## 4. AutoGen Integration

Sandbox multi-turn code block execution in AutoGen conversations:

```python
from sheepdog.hooks import SheepdogCodeExecutor, CodeBlock

executor = SheepdogCodeExecutor(permissions=["fs_read", "fs_write", "fs_exec"])
result = executor.execute_code_blocks([
    CodeBlock("python", "print('Hello from AutoGen inside Sheepdog')")
])

print(f"Exit code: {result.exit_code}")
print(f"Output: {result.output}")
```

---

## 5. Data Science & RAG Agent Integration

Mount read-only datasets, enforce default-deny network rules to prevent data exfiltration, and track pandas file diffs:

```python
from sheepdog.hooks import DataScienceSandboxHook

hook = DataScienceSandboxHook(workdir=".")
hook.mount_dataset("sales_data.csv")

# Run agent analysis
result = hook.run("""
import pandas as pd
df = pd.read_csv('sales_data.csv')
print(f"Dataset shape: {df.shape}")
""")

print("File Diffs:", result.diffs)
```
