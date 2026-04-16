#!/usr/bin/env python3
"""Universal code health checks for quant-team-creator projects.

Pre-installed by quant-team-creator skill. Copied to <project>/scripts/ during
Step 3.6 (Harness Setup). Imported by run_ci.py as part of the CI pipeline.

Provides 4 universal checks (U-1 through U-4):
  U-1: File size (files >800 lines WARN, >1200 FAIL)
  U-2: Hardcoded secrets (regex scan for API keys / tokens / passwords / broker IDs)
  U-3: Debug leftovers (print / breakpoint / pdb.set_trace in production dirs)
  U-4: Doc freshness (docs/ files stale vs source commits)

Error messages follow agent-readable format:
    [U-N TAG] <what's wrong>
      File: <path:line>
      FIX: <exactly how to fix it>

Usage:
    # Standalone
    python common_checks.py src_dir1 src_dir2

    # From run_ci.py
    from common_checks import check_all
    sys.exit(check_all())

Adapted from CCteam-creator golden_rules.py (MIT (c) jessepwj), with:
  - U-3 adapted from JS console.log check to Python debug-statement check
  - Extensions focused on .py / .pyx / .pxd / .cpp / .h / .hpp
  - Data paths (.plans/ and historical data dirs) excluded from scan
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

# ---------------------------------------------------------------------------
# Default configuration (overridable via config block at bottom of file)
# ---------------------------------------------------------------------------

DEFAULT_SRC_DIRS: List[str] = ["."]
DEFAULT_DOCS_DIR: str = ".plans"  # Will scan docs/ under any project subdirs

CODE_EXTENSIONS = {".py", ".pyx", ".pxd", ".cpp", ".cc", ".h", ".hpp"}

EXCLUDE_DIRS = {
  "__pycache__",
  ".git",
  ".venv",
  "venv",
  "env",
  ".env",
  "node_modules",
  "build",
  "dist",
  ".plans",
  "archive",
  ".pytest_cache",
  ".mypy_cache",
  ".ruff_cache",
  "htmlcov",
  ".ipynb_checkpoints",
  "artifacts",
}

# Dirs exempt from U-3 debug-statement check
EXEMPT_FROM_DEBUG_CHECK = {"tests", "test", "notebooks", "scripts", "examples"}

# ---------------------------------------------------------------------------
# Result collector
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
  fails: int = 0
  warns: int = 0

  def fail(self, tag: str, msg: str, fix: str) -> None:
    self.fails += 1
    print(f"  [FAIL] [{tag}] {msg}")
    print(f"    FIX: {fix}\n")

  def warn(self, tag: str, msg: str, fix: str) -> None:
    self.warns += 1
    print(f"  [WARN] [{tag}] {msg}")
    print(f"    FIX: {fix}\n")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def iter_code_files(src_dirs: Sequence[str]) -> Iterable[Path]:
  """Yield code files under src_dirs, skipping excluded dirs and generated files.

  Args:
    src_dirs: Directories to scan.

  Yields:
    Path objects for each matched code file.
  """
  for src_dir in src_dirs:
    root = Path(src_dir)
    if not root.exists():
      continue
    for f in root.rglob("*"):
      if not f.is_file():
        continue
      if f.suffix not in CODE_EXTENSIONS:
        continue
      if any(part in EXCLUDE_DIRS for part in f.parts):
        continue
      yield f


def _is_in_exempt_dir(path: Path) -> bool:
  """Return True if path is inside a dir exempt from debug-statement checks."""
  return any(part in EXEMPT_FROM_DEBUG_CHECK for part in path.parts)


# ---------------------------------------------------------------------------
# U-1: File Size
# ---------------------------------------------------------------------------


def check_file_size(
  src_dirs: Sequence[str],
  result: CheckResult,
  warn_limit: int = 800,
  fail_limit: int = 1200,
) -> None:
  """Flag files that exceed line-count thresholds.

  Args:
    src_dirs: Directories to scan.
    result: Collector for findings.
    warn_limit: Lines above this emit WARN.
    fail_limit: Lines above this emit FAIL.

  Returns:
    None. Results accumulated in `result`.
  """
  print("[U-1] File Size Check")
  found = False
  for f in iter_code_files(src_dirs):
    try:
      lines = len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
      continue
    if lines > fail_limit:
      result.fail(
        "U-1 FILE-SIZE",
        f"{f} — {lines} lines (hard limit: {fail_limit})",
        "Split into smaller modules. Extract helper functions / classes.",
      )
      found = True
    elif lines > warn_limit:
      result.warn(
        "U-1 FILE-SIZE",
        f"{f} — {lines} lines (soft limit: {warn_limit})",
        "Consider splitting. Files over 800 lines are hard for agents to navigate.",
      )
      found = True
  if not found:
    print("  [OK] All files within size limits.\n")


# ---------------------------------------------------------------------------
# U-2: Hardcoded Secrets
# ---------------------------------------------------------------------------

SECRET_PATTERNS: List[tuple] = [
  (r"""['"]sk-[a-zA-Z0-9]{20,}['"]""", "Possible OpenAI / Stripe API key"),
  (r"""['"]ghp_[a-zA-Z0-9]{30,}['"]""", "Possible GitHub personal access token"),
  (r"""['"]AKIA[A-Z0-9]{16}['"]""", "Possible AWS access key"),
  (r"""['"]xox[baprs]-[a-zA-Z0-9-]{20,}['"]""", "Possible Slack token"),
  (
    r"""(?i)(password|passwd|secret|api_key|apikey|access_token|auth_token|private_key)\s*[:=]\s*['"][^'"]{8,}['"]""",
    "Possible hardcoded secret",
  ),
  (
    r"""(?i)(broker_id|account_id|trading_account|investor_id|client_id)\s*[:=]\s*['"][A-Za-z0-9]{6,}['"]""",
    "Possible hardcoded broker / account credential",
  ),
]

EXAMPLE_MARKERS = (
  "example",
  "placeholder",
  "your_key_here",
  "your-key-here",
  "xxx",
  "changeme",
  "<your",
  "dummy",
  "fake_",
  "test_",
  "sample",
)


def check_secrets(src_dirs: Sequence[str], result: CheckResult) -> None:
  """Scan source files for hardcoded secrets using regex patterns.

  Args:
    src_dirs: Directories to scan.
    result: Collector for findings.

  Returns:
    None. Results accumulated in `result`.
  """
  print("[U-2] Hardcoded Secrets Check")
  found = False
  for f in iter_code_files(src_dirs):
    try:
      content = f.read_text(encoding="utf-8", errors="ignore")
    except OSError:
      continue
    for i, line in enumerate(content.splitlines(), 1):
      stripped = line.strip()
      if stripped.startswith("#") or stripped.startswith("//"):
        continue
      if any(marker in stripped.lower() for marker in EXAMPLE_MARKERS):
        continue
      for pattern, desc in SECRET_PATTERNS:
        if re.search(pattern, line):
          result.fail(
            "U-2 SECRET",
            f"{f}:{i} — {desc}",
            "Move to an environment variable or a gitignored config file. "
            "Never commit real credentials.",
          )
          found = True
          break
  if not found:
    print("  [OK] No hardcoded secrets detected.\n")


# ---------------------------------------------------------------------------
# U-3: Debug Leftovers
# ---------------------------------------------------------------------------

DEBUG_PATTERNS = [
  # Python
  (re.compile(r"(?<![\w.])print\s*\("), "print() call", ".py"),
  (re.compile(r"(?<![\w.])breakpoint\s*\("), "breakpoint() call", ".py"),
  (re.compile(r"(?<![\w.])pdb\.set_trace\s*\("), "pdb.set_trace() call", ".py"),
  (re.compile(r"(?<![\w.])ipdb\.set_trace\s*\("), "ipdb.set_trace() call", ".py"),
  (re.compile(r"(?<![\w.])pudb\.set_trace\s*\("), "pudb.set_trace() call", ".py"),
  # C++
  (re.compile(r"(?<![\w])std::cout\s*<<"), "std::cout debug output", ".cpp"),
  (re.compile(r"(?<![\w])std::cerr\s*<<"), "std::cerr debug output", ".cpp"),
  (re.compile(r"(?<![\w])printf\s*\("), "printf debug output", ".cpp"),
]


def check_debug_leftovers(src_dirs: Sequence[str], result: CheckResult) -> None:
  """Detect print / breakpoint / pdb leftovers in production dirs.

  Skips files in tests/, notebooks/, scripts/, examples/.

  Args:
    src_dirs: Directories to scan.
    result: Collector for findings.

  Returns:
    None. Results accumulated in `result`.
  """
  print("[U-3] Debug Leftovers Check")
  found = False
  for f in iter_code_files(src_dirs):
    if _is_in_exempt_dir(f):
      continue
    try:
      content = f.read_text(encoding="utf-8", errors="ignore")
    except OSError:
      continue
    for i, line in enumerate(content.splitlines(), 1):
      stripped = line.strip()
      if stripped.startswith("#") or stripped.startswith("//"):
        continue
      for pattern, desc, ext_hint in DEBUG_PATTERNS:
        if ext_hint == ".py" and f.suffix not in {".py", ".pyx", ".pxd"}:
          continue
        if ext_hint == ".cpp" and f.suffix not in {".cpp", ".cc", ".h", ".hpp"}:
          continue
        if pattern.search(line):
          # Allow logger.print / logger.info patterns
          if re.search(r"(?i)log(?:ger|ging)?\.(?:info|debug|warn|error)", line):
            continue
          result.fail(
            "U-3 DEBUG-LEFTOVER",
            f"{f}:{i} — {desc}  |  {stripped[:80]}",
            f"Remove the debug statement, or move to tests/ / notebooks/. "
            f"For production logging use the project's logger (loguru / logging).",
          )
          found = True
          break
  if not found:
    print("  [OK] No debug leftovers in production dirs.\n")


# ---------------------------------------------------------------------------
# U-4: Doc Freshness
# ---------------------------------------------------------------------------

QUANT_DOC_FILES = {
  "pipeline-flow.md": "pipeline flow",
  "data-schemas.md": "data schemas",
  "strategy-contracts.md": "strategy contracts",
  "invariants.md": "invariants",
}


def check_doc_freshness(
  docs_dir: str,
  src_dirs: Sequence[str],
  result: CheckResult,
  stale_commit_threshold: int = 10,
) -> None:
  """Warn if docs/ files lag behind source by >N commits.

  Requires git. Silently skips if git is not available or docs_dir missing.

  Args:
    docs_dir: Path to the `docs/` directory (typically inside `.plans/<project>/`).
    src_dirs: Source directories to measure against.
    result: Collector for findings.
    stale_commit_threshold: If source has ≥N commits since a doc's last commit, warn.

  Returns:
    None.
  """
  print("[U-4] Doc Freshness Check")
  docs_path = Path(docs_dir)
  if not docs_path.exists():
    # Search for docs/ in any .plans/*/ subdir
    plans_root = Path(".plans")
    if plans_root.exists():
      candidates = list(plans_root.glob("*/docs"))
      if candidates:
        docs_path = candidates[0]
      else:
        print("  [SKIP] No docs/ directory found.\n")
        return
    else:
      print("  [SKIP] docs/ directory not found.\n")
      return

  def _git_commits_since(path: Path) -> Optional[int]:
    try:
      out = subprocess.run(
        ["git", "log", "--oneline", str(path)],
        capture_output=True,
        text=True,
        check=False,
      )
      if out.returncode != 0:
        return None
      return len(out.stdout.splitlines())
    except (subprocess.SubprocessError, FileNotFoundError):
      return None

  src_commit_count = 0
  for src_dir in src_dirs:
    count = _git_commits_since(Path(src_dir))
    if count is not None:
      src_commit_count = max(src_commit_count, count)

  if src_commit_count == 0:
    print("  [SKIP] Git history unavailable.\n")
    return

  found = False
  for doc_name, desc in QUANT_DOC_FILES.items():
    doc_file = docs_path / doc_name
    if not doc_file.exists():
      continue
    doc_commits = _git_commits_since(doc_file) or 0
    lag = src_commit_count - doc_commits
    if lag >= stale_commit_threshold:
      result.warn(
        "U-4 DOC-STALE",
        f"{doc_file} — {lag} source commits since last doc update ({desc})",
        "Review the doc against recent code changes. Update affected sections "
        "and re-commit. Assign to team-lead if unclear.",
      )
      found = True
  if not found:
    print("  [OK] Docs reasonably up to date.\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def check_all(
  src_dirs: Optional[Sequence[str]] = None,
  docs_dir: Optional[str] = None,
) -> int:
  """Run all universal checks.

  Args:
    src_dirs: Directories to scan. Defaults to DEFAULT_SRC_DIRS.
    docs_dir: Docs directory for freshness check. Defaults to DEFAULT_DOCS_DIR.

  Returns:
    Exit code: 0 if no FAIL, 1 otherwise.
  """
  src_dirs = list(src_dirs) if src_dirs else list(DEFAULT_SRC_DIRS)
  docs_dir = docs_dir or DEFAULT_DOCS_DIR

  result = CheckResult()
  check_file_size(src_dirs, result)
  check_secrets(src_dirs, result)
  check_debug_leftovers(src_dirs, result)
  check_doc_freshness(docs_dir, src_dirs, result)

  print("=" * 60)
  print(f"Summary: {result.fails} FAIL, {result.warns} WARN")
  print("=" * 60)
  return 0 if result.fails == 0 else 1


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Universal code health checks (U-1 to U-4).")
  parser.add_argument("src_dirs", nargs="*", help="Source directories to scan")
  parser.add_argument("--docs-dir", default=None, help="Docs directory (for U-4)")
  args = parser.parse_args()
  sys.exit(check_all(args.src_dirs or None, args.docs_dir))
