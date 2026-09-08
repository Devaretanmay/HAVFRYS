import hashlib
import json
import os
import shutil
import subprocess

try:
    import blake3

    def _blake3_digest(data: bytes) -> str:
        return blake3.blake3(data).hexdigest()
except ImportError:
    def _blake3_digest(data: bytes) -> str:
        return hashlib.blake2b(data, digest_size=16).hexdigest()


def _detect_test_command(repo_dir: str) -> str:
    if os.path.exists(os.path.join(repo_dir, "test", "run.js")):
        return "node test/run.js"
    pkg_json_path = os.path.join(repo_dir, "package.json")
    if os.path.exists(pkg_json_path):
        try:
            with open(pkg_json_path) as f:
                data = json.load(f)
            scripts = data.get("scripts", {})
            for candidate in ("test", "test:unit", "test:ci", "type-check", "build"):
                if candidate in scripts:
                    return f"npm run {candidate}" if candidate != "test" else "npm test"
        except Exception:
            pass
    if os.path.exists(os.path.join(repo_dir, "pytest.ini")) or os.path.exists(os.path.join(repo_dir, "tests")):
        return "pytest -q"
    if os.path.exists(os.path.join(repo_dir, "Cargo.toml")):
        return "cargo test"
    return ""


def _compute_lockfile_hash(repo_dir: str) -> str:
    candidates = (
        "pnpm-lock.yaml",
        "package-lock.json",
        "yarn.lock",
        "bun.lockb",
        "Cargo.lock",
        "poetry.lock",
        "Pipfile.lock",
        "package.json",
        "Cargo.toml",
    )
    for c in candidates:
        fp = os.path.join(repo_dir, c)
        if os.path.isfile(fp):
            try:
                with open(fp, "rb") as f:
                    return _blake3_digest(f.read())
            except Exception:
                pass
    return _blake3_digest(repo_dir.encode("utf-8"))


def _run_install(repo_dir: str, timeout: int = 120) -> subprocess.CompletedProcess:
    # multi-ecosystem: prefer the manifest actually present
    if os.path.exists(os.path.join(repo_dir, "Cargo.toml")) and shutil.which("cargo"):
        return subprocess.run(["cargo", "fetch"], cwd=repo_dir, capture_output=True, text=True, timeout=timeout)
    if (os.path.exists(os.path.join(repo_dir, "requirements.txt")) or os.path.exists(os.path.join(repo_dir, "pyproject.toml"))) and shutil.which("pip"):
        req = os.path.join(repo_dir, "requirements.txt")
        cmd = ["pip", "install", "-r", req] if os.path.exists(req) else ["pip", "install", "-e", "."]
        try:
            return subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True, timeout=timeout)
        except Exception:
            pass
    if shutil.which("pnpm") and os.path.exists(os.path.join(repo_dir, "pnpm-lock.yaml")):
        cmd = ["pnpm", "install", "--frozen-lockfile=false"]
    elif shutil.which("yarn") and os.path.exists(os.path.join(repo_dir, "yarn.lock")):
        cmd = ["yarn", "install"]
    elif shutil.which("npm") and os.path.exists(os.path.join(repo_dir, "package.json")):
        cmd = ["npm", "install"]
    else:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="no install needed", stderr="")
    return subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True, timeout=timeout)


def _run_tests(repo_dir: str, test_cmd: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        test_cmd,
        shell=True,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
