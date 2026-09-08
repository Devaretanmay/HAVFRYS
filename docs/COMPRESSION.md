# Execution-Evidence Compression & Failure Summarization

Sandboxed test suites, build runs, and compiler outputs can easily produce tens of thousands of lines of terminal text. Volf includes high-speed native Rust compression engines (`src/engines/compression/`) to distill verbose test logs down to high-signal failure traces, stack traces, and verification evidence for LLM maintenance agents and Developer Trust PR receipts without exceeding context limits.

---

## 1. Core Compression Engines

The Volf Rust core includes four specialized evidence compression engines:

1. **LogCompressor & Stack Trace Isolator**: Strips noisy repetitive progress loops, polling logs, and build progress bars while preserving critical error tracebacks, panic messages, failing assertion lines, and exit statuses.
2. **SmartCrusher (JSON & Contract Compaction)**: Compacts large OpenAPI schemas, dependency trees, and payload arrays into structural schemas and representative records.
3. **DiffCompressor**: Trims massive multi-file diffs to highlight modified AST nodes while preserving file boundaries and syntax integrity.
4. **TextCrusher**: Extractive summarizer for verbose terminal logs.

---

## 2. Dynamic Content Routing (`route_and_compress`)

Volf automatically detects the content type of execution output (build logs, JSON, diffs, raw text) and applies the optimal engine:

```python
from volf.maintenance_agents import PatchVerifier

verifier = PatchVerifier()
result = verifier.verify(repo_dir=".", test_cmd="npm test")

print(f"Raw Log: {result.raw_log_bytes} bytes -> Compressed Evidence: {result.compressed_log_bytes} bytes")
print(result.compressed_execution_log)
```

---

## 3. Why This Matters for Autonomous Maintenance

* **Scalable Evidence Bundles**: Test failure outputs are attached to GitHub PRs and issues without hitting character limits.
* **Efficient Agent Loops**: When `PatchVerifier` diagnoses a test failure, it feeds high-signal stack traces directly to `PatchPlanner` without blowing token context budgets.
* **Deterministic Compression**: Fast, reproducible Rust execution ensures evidence is compressed identically across runs.
