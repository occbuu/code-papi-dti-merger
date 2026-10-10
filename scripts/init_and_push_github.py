"""Initialise git in code-papi-dti-merger and optionally create/push a GitHub repo.

Examples
--------
# Dry-run: show what would happen
python scripts/init_and_push_github.py --dry-run

# Init local git + commit only
python scripts/init_and_push_github.py --commit-only

# Create public GitHub repo with gh and push
python scripts/init_and_push_github.py --repo papi-dti-merger --public

# Use an existing remote URL
python scripts/init_and_push_github.py --remote https://github.com/USER/papi-dti-merger.git
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]


def run(cmd: list[str], dry: bool) -> None:
    print("+", " ".join(cmd))
    if dry:
        return
    subprocess.run(cmd, cwd=PKG, check=True)


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def git_initialized() -> bool:
    return (PKG / ".git").exists()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="papi-dti-merger", help="GitHub repository name")
    ap.add_argument("--public", action="store_true", help="Create public repo (default private if using gh)")
    ap.add_argument("--private", action="store_true", help="Force private repo with gh")
    ap.add_argument("--remote", default="", help="Existing git remote URL")
    ap.add_argument("--commit-only", action="store_true", help="Init + commit; do not create/push remote")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--message", default="Initial public replication package for PAPI x DTI merger study")
    ap.add_argument("--author-name", default="Hieu Le Ngoc",
                    help="One-shot commit author name (does not write git config)")
    ap.add_argument("--author-email", default="lnhieu@ptit.edu.vn",
                    help="One-shot commit author email (does not write git config)")
    args = ap.parse_args()
    dry = args.dry_run

    if not have("git"):
        print("ERROR: git is not on PATH. Install Git for Windows / git, then retry.", file=sys.stderr)
        return 1

    if not (PKG / "P3_analysis_final.py").exists() or not (PKG / "DataPaper3" / "data").exists():
        print("Package looks incomplete. Run: python build_public_package.py", file=sys.stderr)
        return 1

    if not git_initialized():
        run(["git", "init", "-b", "main"], dry)
    else:
        print("git already initialised")

    run(["git", "add", "-A"], dry)
    # Commit only if there is something to commit.
    # Use one-shot -c identity so we never modify git config.
    commit_cmd = [
        "git",
        "-c", f"user.name={args.author_name}",
        "-c", f"user.email={args.author_email}",
        "commit", "-m", args.message,
    ]
    if dry:
        print("+", " ".join(commit_cmd))
    else:
        st = subprocess.run(["git", "status", "--porcelain"], cwd=PKG, capture_output=True, text=True)
        if st.stdout.strip():
            subprocess.run(commit_cmd, cwd=PKG, check=True)
        else:
            print("Nothing new to commit")

    if args.commit_only:
        print("Local repository ready at", PKG)
        return 0

    remote = args.remote
    if not remote:
        if have("gh"):
            visibility = "private" if args.private or not args.public else "public"
            # Create repo from current directory and push
            cmd = [
                "gh", "repo", "create", args.repo,
                f"--{visibility}",
                "--source=.",
                "--remote=origin",
                "--push",
                "--description",
                "Replication: Viet Nam PAPI x DTI and 63-to-34 provincial merger measurement study",
            ]
            run(cmd, dry)
            if not dry:
                url = subprocess.run(
                    ["gh", "repo", "view", "--json", "url", "-q", ".url"],
                    cwd=PKG, capture_output=True, text=True, check=True,
                ).stdout.strip()
                print("Published:", url)
            return 0
        print(
            "\nGitHub CLI (gh) not found. Local commit is ready.\n"
            "Manual steps:\n"
            "  1) Create an empty repo on https://github.com/new\n"
            f"     Suggested name: {args.repo}\n"
            "  2) Then run:\n"
            f"     cd \"{PKG}\"\n"
            "     git remote add origin https://github.com/<USER>/<REPO>.git\n"
            "     git push -u origin main\n"
            "\nOr install GitHub CLI: https://cli.github.com/ then re-run with --public\n"
        )
        return 0

    # Existing remote URL provided
    # Replace origin if present
    if dry:
        print("+ git remote add/set-url origin", remote)
        print("+ git push -u origin main")
        return 0
    remotes = subprocess.run(["git", "remote"], cwd=PKG, capture_output=True, text=True, check=True).stdout.split()
    if "origin" in remotes:
        run(["git", "remote", "set-url", "origin", remote], dry)
    else:
        run(["git", "remote", "add", "origin", remote], dry)
    run(["git", "push", "-u", "origin", "main"], dry)
    print("Pushed to", remote)
    return 0


if __name__ == "__main__":
    sys.exit(main())
