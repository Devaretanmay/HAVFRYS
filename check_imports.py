import ast
import os
import sys

inline_py = []
for root, dirs, files in os.walk("python"):
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
                    for subnode in ast.walk(node):
                        if isinstance(subnode, (ast.Import, ast.ImportFrom)):
                            inline_py.append((path, subnode.lineno, ast.unparse(subnode)))

if inline_py:
    print(f"ERROR: Found {len(inline_py)} inline Python imports inside functions:")
    for p, l, s in inline_py:
        print(f"  {p}:{l} -> {s}")
    sys.exit(1)
else:
    print("PASS: 100% of import statements are at top of files.")
