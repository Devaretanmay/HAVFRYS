# Execution-Evidence Compression & Failure Summarization

Sandboxed test suites, build runs, and compiler outputs can easily produce tens of thousands of lines of terminal text. Koyote includes high-speed native Rust compression engines (`src/engines/compression/`) to distill verbose test logs down to high-signal failure traces, stack traces, and verification evidence for LLM maintenance agents and Developer Trust PR receipts without exceeding context limits.

---

## 1. Core Compression Engines

The Koyote Rust core includes four specialized evidence compression engines:

1. **LogCompressor & Stack Trace Isolator**: Strips noisy repetitive progress loops, polling logs, and build progress bars while preserving critical error tracebacks, panic messages, failing assertion lines, and exit statuses.
2. **SmartCrusher (JSON & Contract Compaction)**: Compacts large OpenAPI schemas, dependency trees, and payload arrays into structural schemas and representative records.
3. **DiffCompressor**: Trims massive multi-file diffs to highlight modified AST nodes while preserving file boundaries and syntax integrity.
4. **TextCrusher**: Extractive summarizer for verbose terminal logs.

---

## 2. Dynamic Content Routing (`route_and_compress`)

Koyote automatically detects the content type of execution output (build logs, JSON, diffs, raw text) and applies the optimal engine:

```python
from koyote._core import route_and_compress

# Route and compress execution output (test logs, build traces, diffs)
raw_log = """
==================================== ERRORS ====================================
_______________________ test_stripe_charges_v4_migration _______________________
TypeError: Stripe.Charge.create() missing 1 required positional argument: 'params'
...
=========================== short test summary info ============================
FAILED tests/test_stripe.py::test_stripe_charges_v4_migration - TypeError
"""

compressed_log = route_and_compress(raw_log)

print(f"Raw Log: {len(raw_log)} bytes -> Compressed Evidence: {len(compressed_log)} bytes")
print(compressed_log)
```

---

## 3. Why This Matters for Autonomous Maintenance

* **Scalable Evidence Bundles**: Test failure outputs are attached to GitHub PRs and issues without hitting character limits.
* **Efficient Agent Loops**: When test verification diagnoses a test failure, it feeds high-signal stack traces directly to `AIPatchPlanner` without blowing token context budgets.
* **Deterministic Compression**: Fast, reproducible Rust execution ensures evidence is compressed identically across runs.
