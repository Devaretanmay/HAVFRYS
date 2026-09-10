import ast
import os
import subprocess
import sys

def main():
    print("=== 0. LINT (ruff, entire tree) ===")
    res_lint = subprocess.run(["ruff", "check", "python", "tests"],
                              capture_output=True, text=True)
    if res_lint.returncode != 0:
        print("Ruff found violations:")
        print(res_lint.stdout or res_lint.stderr)
        sys.exit(1)
    print("PASS: ruff clean across python/ and tests/.")

    print("=== 1. VERIFYING CODEBASE HYGIENE RULES ===")

    violations = []
    total_files = 0
    for root_dir in ["src", "python", "tests"]:
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith((".py", ".rs")):
                    total_files += 1
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    tot = len(lines)
                    if tot == 0:
                        continue
                    is_rs = file.endswith('.rs')
                    is_py = file.endswith('.py')
                    comm = 0
                    in_block = False
                    for line in lines:
                        s = line.strip()
                        if is_rs:
                            if in_block:
                                comm += 1
                                if "*/" in s:
                                    in_block = False
                                continue
                            if s.startswith("/*"):
                                comm += 1
                                if "*/" not in s:
                                    in_block = True
                                continue
                            if s.startswith("//") or s.startswith("///") or s.startswith("//!"):
                                comm += 1
                        elif is_py:
                            if s.startswith("#") or " #" in s:
                                comm += 1
                    max_allowed = max(3, (tot * 3) // 100)
                    if comm > max_allowed:
                        violations.append((path, tot, comm, max_allowed))

    print(f"Scanned {total_files} code files.")
    if violations:
        print(f"ERROR: {len(violations)} comment density violations found:")
        for p, tot, comm, max_all in violations:
            print(f"  {p}: {tot} lines, {comm} comments (limit: {max_all})")
        sys.exit(1)
    else:
        print("PASS: 100% of files satisfy <= 3 comments per 100 lines of code.")

    inline_py = []
    for root_dir in ["python", "tests", "scripts"]:
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        code = f.read()
                    try:
                        tree = ast.parse(code, filename=path)
                    except SyntaxError:
                        continue
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                            for stmt in node.body:
                                for subnode in ast.walk(stmt):
                                    if isinstance(subnode, (ast.Import, ast.ImportFrom)):
                                        s = ast.unparse(subnode) if hasattr(ast, "unparse") else "import ..."
                                        inline_py.append((path, getattr(subnode, 'lineno', 0), s))

    if inline_py:
        print(f"ERROR: Found {len(inline_py)} inline Python imports inside functions:")
        for p, lineno, s in inline_py:
            print(f"  {p}:{lineno} -> {s}")
        sys.exit(1)
    else:
        print("PASS: 100% of import statements are at top of files.")

    unnecessary = ["examples", "demo_30s_onboarding.mp4", "demo_30s_onboarding.tape", "demo_30s_onboarding.gif"]
    found_unnecessary = [u for u in unnecessary if os.path.exists(u)]
    if found_unnecessary:
        print(f"ERROR: Unnecessary demo files still exist: {found_unnecessary}")
        sys.exit(1)
    else:
        print("PASS: All unnecessary demo files, recordings, and examples have been removed.")

    print("\n=== 2. RUNNING RUST NATIVE TESTS ===")
    res_rust = subprocess.run(["cargo", "test", "--lib"], capture_output=True, text=True)
    if res_rust.returncode != 0:
        print("Rust tests failed!")
        print(res_rust.stderr or res_rust.stdout)
        sys.exit(1)
    else:
        lines = res_rust.stdout.strip().split("\n")
        summary = [line for line in lines if "test result:" in line]
        print("Rust test suite passed:", summary[-1] if summary else "OK")

    print("\n=== 3. RUNNING PYTHON TEST SUITE ===")
    env = dict(os.environ)
    has_local_core = os.path.exists("python/koyote") and any(f.startswith("_core") for f in os.listdir("python/koyote"))
    if has_local_core:
        env["PYTHONPATH"] = os.path.abspath("python")
    res_py = subprocess.run(["pytest", "tests/", "-q"], capture_output=True, text=True, env=env)
    if res_py.returncode != 0:
        print("Pytest failed!")
        print(res_py.stderr or res_py.stdout)
        sys.exit(1)
    else:
        print("Python test suite passed:", res_py.stdout.strip().split("\n")[-1])

    print("\n============================================================")
    print("      ALL CODEBASE HYGIENE CHECKS & TEST SUITES PASSED      ")
    print("============================================================")

if __name__ == "__main__":
    main()
