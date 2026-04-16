#!/usr/bin/env python3
"""Quant-specific golden rules for quant-team-creator projects.

Pre-installed by quant-team-creator skill. Copied to <project>/scripts/ during
Step 3.6 (Harness Setup). Imported by run_ci.py as part of the CI pipeline.

Provides 5 quant-specific checks (Q-1 through Q-5):
  Q-1: Timestamp monotonicity (parquet + pkl.gz across configured data paths)
  Q-2: Unseeded randomness (numpy.random / random / torch imports without seed)
  Q-3: Stdlib name shadowing (filenames matching stdlib module names)
  Q-4: Type annotation imports (every typing name used in annotation is imported)
  Q-5: pd.read_csv without dtype argument (WARN)

Error messages follow agent-readable format:
    [Q-N TAG] <what's wrong>
      File: <path:line>
      FIX: <exactly how to fix it>

Usage:
    # Standalone
    python quant_golden_rules.py

    # From run_ci.py
    from quant_golden_rules import check_all
    sys.exit(check_all())

Configuration: see "Project configuration" block near the bottom of this file.
Customize for each project during Step 3.6.
"""
from __future__ import annotations

import argparse
import ast
import gzip
import pickle
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

# ---------------------------------------------------------------------------
# Result collector
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
  fails: int = 0
  warns: int = 0
  skips: int = 0

  def fail(self, tag: str, msg: str, fix: str) -> None:
    self.fails += 1
    print(f"  [FAIL] [{tag}] {msg}")
    print(f"    FIX: {fix}\n")

  def warn(self, tag: str, msg: str, fix: str) -> None:
    self.warns += 1
    print(f"  [WARN] [{tag}] {msg}")
    print(f"    FIX: {fix}\n")

  def skip(self, tag: str, msg: str) -> None:
    self.skips += 1
    print(f"  [SKIP] [{tag}] {msg}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EXCLUDE_DIRS = {
  "__pycache__",
  ".git",
  ".venv",
  "venv",
  "env",
  "node_modules",
  "build",
  "dist",
  ".plans",
  "archive",
  ".pytest_cache",
  ".mypy_cache",
  ".ruff_cache",
  "artifacts",
}


def iter_py_files(src_dirs: Sequence[str], exempt_dirs: Sequence[str] = ()) -> Iterable[Path]:
  """Yield `.py` files under src_dirs, skipping excluded and exempt dirs.

  Args:
    src_dirs: Directories to scan.
    exempt_dirs: Extra dir name components to skip (e.g., `tests`, `notebooks`).

  Yields:
    Path objects.
  """
  exempt_set = set(EXCLUDE_DIRS) | set(exempt_dirs)
  for src_dir in src_dirs:
    root = Path(src_dir)
    if not root.exists():
      continue
    for f in root.rglob("*.py"):
      if any(part in exempt_set for part in f.parts):
        continue
      yield f


# ---------------------------------------------------------------------------
# Q-1: Timestamp Monotonicity (parquet + pkl.gz)
# ---------------------------------------------------------------------------


def _load_parquet_ts(path: Path, ts_col: str):
  """Load only the Ts column from a parquet file. Returns None on failure."""
  try:
    import pyarrow.parquet as pq  # pylint: disable=import-outside-toplevel
  except ImportError:
    return None
  try:
    table = pq.read_table(str(path), columns=[ts_col])
    return table.column(ts_col).to_pylist()
  except Exception:  # pylint: disable=broad-except
    return None


def _load_pkl_gz_ts(path: Path, ts_col: str):
  """Load the Ts column from a gzipped pickle. Returns None on failure."""
  try:
    with gzip.open(str(path), "rb") as fh:
      obj = pickle.load(fh)
  except Exception:  # pylint: disable=broad-except
    return None
  # Try DataFrame / dict / ndarray
  try:
    import pandas as pd  # pylint: disable=import-outside-toplevel
    if isinstance(obj, pd.DataFrame) and ts_col in obj.columns:
      return obj[ts_col].tolist()
  except ImportError:
    pass
  if isinstance(obj, dict) and ts_col in obj:
    seq = obj[ts_col]
    try:
      return list(seq)
    except TypeError:
      return None
  return None


def check_timestamp_monotonicity(
  data_paths: Sequence[dict],
  result: CheckResult,
  sample_rate: int = 1,
) -> None:
  """Verify `Ts` is non-decreasing per file across configured data paths.

  Each entry in `data_paths`:
      {"path": "<dir>", "format": "parquet" | "pkl.gz", "ts_col": "Ts"}

  Args:
    data_paths: List of data-path configs.
    result: Collector.
    sample_rate: Files to sample per date per path. 0 = all.
  """
  print("[Q-1] Timestamp Monotonicity Check")
  if not data_paths:
    result.skip("Q-1 TIMESTAMP", "No DATA_PATHS configured; skipping.")
    print()
    return

  any_checked = False
  any_fail = False
  for entry in data_paths:
    path = Path(entry["path"])
    fmt = entry.get("format", "parquet")
    ts_col = entry.get("ts_col", "Ts")
    if not path.exists():
      result.skip("Q-1 TIMESTAMP", f"Path not found: {path}  (data dir not mounted?)")
      continue

    pattern = "*.parquet" if fmt == "parquet" else "*.pkl.gz"
    # Scan up to 2 levels of date subdirs
    date_dirs = sorted([d for d in path.iterdir() if d.is_dir()])
    if not date_dirs:
      # Files at top level
      date_dirs = [path]

    for date_dir in date_dirs:
      files = sorted(date_dir.rglob(pattern))
      if not files:
        continue
      if sample_rate > 0:
        files = files[:sample_rate]
      for f in files:
        any_checked = True
        ts = _load_parquet_ts(f, ts_col) if fmt == "parquet" else _load_pkl_gz_ts(f, ts_col)
        if ts is None:
          result.warn(
            "Q-1 TIMESTAMP",
            f"{f} — could not load `{ts_col}` column",
            "Verify file format + schema. Ensure the Ts column exists and pyarrow is installed.",
          )
          continue
        if len(ts) < 2:
          continue
        for i in range(1, len(ts)):
          if ts[i] < ts[i - 1]:
            result.fail(
              "Q-1 TIMESTAMP",
              f"{f}:row={i} — Ts={ts[i]} < prev={ts[i - 1]} (non-monotonic)",
              "Sort by Ts before writing. If instruments are interleaved, sort "
              "by (InstrumentID, Ts) or split per-instrument before writing.",
            )
            any_fail = True
            break  # one failure per file is enough
  if not any_checked:
    result.skip("Q-1 TIMESTAMP", "No data files found under configured paths.")
    print()
    return
  if not any_fail:
    print("  [OK] Timestamps monotonic across sampled files.\n")


# ---------------------------------------------------------------------------
# Q-2: Unseeded Randomness
# ---------------------------------------------------------------------------

RANDOM_IMPORT_PATTERNS = [
  (re.compile(r"^\s*import\s+random\b"), "random", "random.seed("),
  (re.compile(r"^\s*from\s+random\s+import"), "random", "random.seed("),
  (re.compile(r"^\s*import\s+numpy(\s+as\s+\w+)?\b"), "numpy.random", "np.random.seed( or np.random.default_rng(seed="),
  (re.compile(r"^\s*from\s+numpy(\.random)?\s+import"), "numpy.random", "np.random.seed( or default_rng(seed="),
  (re.compile(r"^\s*import\s+torch\b"), "torch", "torch.manual_seed("),
  (re.compile(r"^\s*import\s+pytorch_lightning"), "pytorch_lightning", "pl.seed_everything("),
]

SEED_CALL_PATTERNS = [
  re.compile(r"\brandom\.seed\s*\("),
  re.compile(r"\bnp(?:\w*)?\.random\.seed\s*\("),
  re.compile(r"\bdefault_rng\s*\(\s*\w*\s*=?\s*\w+"),
  re.compile(r"\btorch\.manual_seed\s*\("),
  re.compile(r"\btorch\.cuda\.manual_seed(?:_all)?\s*\("),
  re.compile(r"\bseed_everything\s*\("),
  re.compile(r"\bset_seed\s*\("),
]


def check_unseeded_randomness(
  research_dirs: Sequence[str],
  result: CheckResult,
  exempt_dirs: Sequence[str] = ("tests", "notebooks"),
) -> None:
  """Flag research code that imports a random source without a matching seed call.

  Args:
    research_dirs: Dirs where research code lives (features, signals, models, research).
    result: Collector.
    exempt_dirs: Dir name components to skip.
  """
  print("[Q-2] Unseeded Randomness Check")
  found = False
  any_checked = False
  for f in iter_py_files(research_dirs, exempt_dirs=exempt_dirs):
    any_checked = True
    try:
      content = f.read_text(encoding="utf-8", errors="ignore")
    except OSError:
      continue

    detected_imports = []
    for line in content.splitlines():
      for pat, name, fix_hint in RANDOM_IMPORT_PATTERNS:
        if pat.search(line):
          detected_imports.append((name, fix_hint))
          break

    if not detected_imports:
      continue

    has_seed_call = any(p.search(content) for p in SEED_CALL_PATTERNS)
    if has_seed_call:
      continue

    # Build a list of imports found
    import_names = sorted(set(n for n, _ in detected_imports))
    fix_hints = sorted(set(h for _, h in detected_imports))
    result.fail(
      "Q-2 UNSEEDED-RNG",
      f"{f} imports {import_names} but no seed call in the same file",
      "Add seed call(s): " + "  |  ".join(fix_hints) + " at module init or test fixture. "
      "Required by INV-R1 (reproducibility).",
    )
    found = True
  if not any_checked:
    result.skip("Q-2 UNSEEDED-RNG", "No research dirs configured or no .py files found.")
    print()
    return
  if not found:
    print("  [OK] All research files with random imports are seeded.\n")


# ---------------------------------------------------------------------------
# Q-3: Stdlib Name Shadowing
# ---------------------------------------------------------------------------

FORBIDDEN_FILENAMES = {
  "io.py",
  "types.py",
  "collections.py",
  "random.py",
  "statistics.py",
  "math.py",
  "datetime.py",
  "logging.py",
  "csv.py",
  "json.py",
  "time.py",
  "copy.py",
  "queue.py",
  "socket.py",
  "threading.py",
  "subprocess.py",
  "argparse.py",
  "enum.py",
  "abc.py",
}


def check_stdlib_shadowing(src_dirs: Sequence[str], result: CheckResult) -> None:
  """Flag .py files whose name shadows a stdlib module.

  Args:
    src_dirs: Package dirs to scan.
    result: Collector.
  """
  print("[Q-3] Stdlib Name Shadowing Check")
  found = False
  for f in iter_py_files(src_dirs):
    if f.name in FORBIDDEN_FILENAMES:
      result.fail(
        "Q-3 STDLIB-SHADOW",
        f"{f} — filename shadows a stdlib module",
        f"Rename to a descriptive name (e.g., data_types.py instead of types.py, "
        f"file_io.py instead of io.py). Required by INV-C2.",
      )
      found = True
  if not found:
    print("  [OK] No stdlib name shadowing detected.\n")


# ---------------------------------------------------------------------------
# Q-4: Type Annotation Imports
# ---------------------------------------------------------------------------

TYPING_NAMES = {
  "Any",
  "Optional",
  "Callable",
  "Union",
  "Dict",
  "List",
  "Tuple",
  "Set",
  "FrozenSet",
  "Sequence",
  "Iterable",
  "Iterator",
  "Mapping",
  "MutableMapping",
  "MutableSequence",
  "Generator",
  "AsyncGenerator",
  "Awaitable",
  "Coroutine",
  "Type",
  "TypeVar",
  "Generic",
  "Literal",
  "Final",
  "Protocol",
  "ClassVar",
  "NoReturn",
  "Never",
  "Self",
  "NewType",
  "cast",
  "overload",
  "TypedDict",
}


def _collect_annotation_names(tree: ast.AST) -> set:
  """Walk AST, collect all names used as type annotations."""
  used: set = set()

  class AnnotationVisitor(ast.NodeVisitor):
    def _collect_from(self, node):
      if node is None:
        return
      for n in ast.walk(node):
        if isinstance(n, ast.Name):
          used.add(n.id)
        elif isinstance(n, ast.Attribute):
          if isinstance(n.value, ast.Name):
            used.add(n.value.id)

    def visit_FunctionDef(self, node):  # noqa: N802
      for arg in node.args.args + node.args.kwonlyargs + node.args.posonlyargs:
        self._collect_from(arg.annotation)
      if node.args.vararg:
        self._collect_from(node.args.vararg.annotation)
      if node.args.kwarg:
        self._collect_from(node.args.kwarg.annotation)
      self._collect_from(node.returns)
      self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):  # noqa: N802
      self.visit_FunctionDef(node)

    def visit_AnnAssign(self, node):  # noqa: N802
      self._collect_from(node.annotation)
      self.generic_visit(node)

  AnnotationVisitor().visit(tree)
  return used


def _collect_imported_names(tree: ast.AST) -> set:
  """Walk AST, collect all names brought into scope via import statements."""
  imported: set = set()
  for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom):
      for alias in node.names:
        imported.add(alias.asname or alias.name)
      # Also add module-level alias for things like `import typing as t`
    elif isinstance(node, ast.Import):
      for alias in node.names:
        imported.add(alias.asname or alias.name.split(".")[0])
  return imported


def check_typing_imports(src_dirs: Sequence[str], result: CheckResult) -> None:
  """Verify every typing name used as annotation is imported.

  Parses each .py file with AST, collects all names used in annotations,
  checks each typing-originating name is present in the imports.

  Args:
    src_dirs: Package dirs to scan.
    result: Collector.
  """
  print("[Q-4] Type Annotation Imports Check")
  found = False
  for f in iter_py_files(src_dirs):
    try:
      source = f.read_text(encoding="utf-8", errors="ignore")
      tree = ast.parse(source)
    except (SyntaxError, OSError):
      continue

    used_annotations = _collect_annotation_names(tree)
    imported_names = _collect_imported_names(tree)

    missing = {name for name in used_annotations if name in TYPING_NAMES and name not in imported_names}
    for name in sorted(missing):
      result.fail(
        "Q-4 TYPING-IMPORT",
        f"{f} uses `{name}` in an annotation but `{name}` is not imported",
        f"Add `{name}` to the existing `from typing import ...` statement, "
        f"OR add a new line: `from typing import {name}`. Required by INV-C1.",
      )
      found = True
  if not found:
    print("  [OK] All typing annotations have matching imports.\n")


# ---------------------------------------------------------------------------
# Q-5: pd.read_csv without dtype (AST-based — string literals are safe)
# ---------------------------------------------------------------------------


def _call_name(func: ast.AST) -> str:
  """Extract the dotted call name from a Call.func node. Returns '' if unknown."""
  if isinstance(func, ast.Attribute):
    value = func.value
    if isinstance(value, ast.Name):
      return f"{value.id}.{func.attr}"
    if isinstance(value, ast.Attribute):
      return f"{_call_name(value)}.{func.attr}"
  elif isinstance(func, ast.Name):
    return func.id
  return ""


def check_read_csv_dtype(src_dirs: Sequence[str], result: CheckResult) -> None:
  """WARN on `pd.read_csv(...)` calls that omit `dtype=`.

  AST-based: only real Call nodes are checked, so docstrings / string literals
  containing the text `pd.read_csv(...)` do not trigger false positives.

  Args:
    src_dirs: Dirs to scan.
    result: Collector.
  """
  print("[Q-5] pd.read_csv without dtype")
  found = False
  for f in iter_py_files(src_dirs):
    try:
      source = f.read_text(encoding="utf-8", errors="ignore")
      tree = ast.parse(source)
    except (SyntaxError, OSError):
      continue
    for node in ast.walk(tree):
      if not isinstance(node, ast.Call):
        continue
      name = _call_name(node.func)
      # Accept pd.read_csv, pandas.read_csv, and any alias like mypd.read_csv
      if not (name == "pd.read_csv" or name.endswith(".read_csv") and "read_csv" in name):
        continue
      # Strict: only flag calls where the base name is clearly pandas
      if not (name == "pd.read_csv" or name == "pandas.read_csv"):
        continue
      has_dtype = any(kw.arg == "dtype" for kw in node.keywords)
      if has_dtype:
        continue
      result.warn(
        "Q-5 READ-CSV-DTYPE",
        f"{f}:{node.lineno} — pd.read_csv(...) without explicit dtype=",
        "Pass `dtype={'col_name': dtype, ...}` to avoid silent type inference bugs. "
        "Especially important for price / volume / ID columns with leading zeros.",
      )
      found = True
  if not found:
    print("  [OK] All pd.read_csv calls have explicit dtype=.\n")


# ---------------------------------------------------------------------------
# ============================================================================
# PROJECT CONFIGURATION (edit this block at project setup)
# ============================================================================

# Python package directories to scan for Q-3 / Q-4 / Q-5 / CI file listing
SRC_DIRS: List[str] = ["."]

# Research / signal / feature / model dirs — scanned for Q-2 (unseeded RNG)
RESEARCH_DIRS: List[str] = ["research", "features", "signals", "models"]

# Data paths for Q-1 (timestamp monotonicity).
# Format options: "parquet" or "pkl.gz".
# Leave empty to disable Q-1 (or set Q1_ENABLED=False).
DATA_PATHS: List[dict] = [
  # Example entries — customize per project:
  # {"path": "/mnt/data/stock_data/OrgData", "format": "parquet", "ts_col": "Ts"},
  # {"path": "/mnt/data/stock_data/MarketData", "format": "parquet", "ts_col": "Ts"},
  # {"path": "/mnt/data/stock_data/Detailed_Level2_Data", "format": "pkl.gz", "ts_col": "Ts"},
  # {"path": "/mnt/data/stock_data/Resampled_Data", "format": "pkl.gz", "ts_col": "Ts"},
  # {"path": "/mnt/data/stock_data/Level2_Data", "format": "parquet", "ts_col": "Ts"},
]

Q1_SAMPLE_RATE: int = 1  # Files to sample per date per path (0 = all)
Q1_ENABLED: bool = True

# ============================================================================


def check_all() -> int:
  """Run all quant-specific checks.

  Returns:
    Exit code: 0 if no FAIL, 1 otherwise.
  """
  result = CheckResult()

  if Q1_ENABLED:
    check_timestamp_monotonicity(DATA_PATHS, result, sample_rate=Q1_SAMPLE_RATE)
  else:
    print("[Q-1] Timestamp Monotonicity — disabled via Q1_ENABLED=False\n")

  check_unseeded_randomness(RESEARCH_DIRS, result)
  check_stdlib_shadowing(SRC_DIRS, result)
  check_typing_imports(SRC_DIRS, result)
  check_read_csv_dtype(SRC_DIRS, result)

  print("=" * 60)
  print(f"Summary: {result.fails} FAIL, {result.warns} WARN, {result.skips} SKIP")
  print("=" * 60)
  return 0 if result.fails == 0 else 1


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Quant-specific golden rules (Q-1 to Q-5).")
  parser.parse_args()
  sys.exit(check_all())
