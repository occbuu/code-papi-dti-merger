"""Assemble a public GitHub package from the Paper 3 project root.

Run from anywhere:
  python path/to/code-papi-dti-merger/build_public_package.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent
PKG = ROOT  # package root is this folder

COPY_FILES = [
    "P3_analysis_final.py",
    "P3_analysis_upgrade.py",
    "verify_sources_upgrade.py",
    "build_manuscript_upgrade.py",
    "build_visual_upgrade.py",
    "enhance_manuscript_visual.py",
    "check_upgrade.py",
    "check_visual_upgrade.py",
    "finalize_upgrade_package.py",
    "requirements-upgrade.txt",
    "REVISION_LOG_2026-10-09.md",
    "VISUAL_LITERATURE_REVISION_2026-10-09.md",
]

COPY_DIRS = [
    ("DataPaper3/data", "DataPaper3/data"),
    ("DataPaper3/raw", "DataPaper3/raw"),
    ("results_upgrade", "results_upgrade"),
    ("figures_upgrade", "figures_upgrade"),
    ("Paper3_DeTaiThayHien", "manuscript"),
]

SKIP_NAME_PARTS = {
    "__pycache__",
    ".ipynb_checkpoints",
    "PRE_REVISION",
}


def should_skip(path: Path) -> bool:
    return any(part in path.parts or part in path.name for part in SKIP_NAME_PARTS)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path) -> int:
    n = 0
    if not src.exists():
        raise FileNotFoundError(src)
    for f in src.rglob("*"):
        if not f.is_file() or should_skip(f):
            continue
        rel = f.relative_to(src)
        copy_file(f, dst / rel)
        n += 1
    return n


def main() -> int:
    print(f"Source: {SRC}")
    print(f"Package: {PKG}")
    copied = 0
    for name in COPY_FILES:
        src = SRC / name
        if not src.exists():
            print(f"SKIP missing file: {name}")
            continue
        copy_file(src, PKG / name)
        copied += 1
        print(f"file  {name}")
    for src_rel, dst_rel in COPY_DIRS:
        n = copy_tree(SRC / src_rel, PKG / dst_rel)
        copied += n
        print(f"dir   {src_rel} -> {dst_rel} ({n} files)")
    # Canonical requirements name for GitHub
    req = PKG / "requirements-upgrade.txt"
    if req.exists():
        copy_file(req, PKG / "requirements.txt")
    print(f"Done. Copied/updated {copied} file entries.")
    print("Next: python scripts/init_and_push_github.py --dry-run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
