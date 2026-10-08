#!/usr/bin/env python3
"""Work history for one company.

The history lives at ``<company>/cache/work-history``. It is not the
project repository. A room is one branch in that history. Each command
points the history at one room folder.

One room name is one branch. One staff is one author. One user message
is one commit for each staff who staged files. The commit message is the
user's message. ``record`` commits only the index. Unstaged edits stay in
the room. A staff who staged nothing gets no commit.

Reads and writes go through ordinary git commands in the room folder
(``git status``, ``git show``, ``git diff``, ``git commit``, ``git reset``).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def git_dir(company: Path) -> Path:
    return company / "cache" / "work-history"


def branch_name(room_name: str) -> str:
    cleaned = []
    for ch in room_name.strip():
        cleaned.append(ch if ch.isalnum() or ch in "._/-" else "-")
    name = "".join(cleaned).strip("-/")
    if not name or name.endswith(".lock"):
        raise SystemExit("room name is empty")
    return "room/" + name


def author(staff: str) -> str:
    staff = staff.strip()
    if not staff or any(c in staff for c in "<>\n"):
        raise SystemExit("staff name is empty or contains <>")
    return staff


def ensure_store(company: Path) -> Path:
    store = git_dir(company)
    store.parent.mkdir(parents=True, exist_ok=True)
    if not (store / "HEAD").is_file():
        subprocess.run(["git", "init", "--bare", str(store)], check=True, capture_output=True)
    subprocess.run(["git", "--git-dir", str(store), "config", "core.bare", "false"], check=True, capture_output=True)
    exclude = store / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    line = "cache/work-history"
    text = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
    if line not in text.splitlines():
        exclude.write_text(text + ("\n" if text and not text.endswith("\n") else "") + line + "\n", encoding="utf-8")
    return store


def git(store: Path, *args: str, cwd: Path | None = None, worktree: Path | None = None, staff: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GIT_DIR"] = str(store)
    if worktree is not None:
        env["GIT_WORK_TREE"] = str(worktree)
    if staff is not None:
        env["GIT_AUTHOR_NAME"] = staff
        env["GIT_AUTHOR_EMAIL"] = f"{staff}@chat.company"
        env["GIT_COMMITTER_NAME"] = staff
        env["GIT_COMMITTER_EMAIL"] = f"{staff}@chat.company"
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def git_at(folder: Path, *args: str, staff: str | None = None) -> subprocess.CompletedProcess[str]:
    """Git commands inside a linked room. Do not set GIT_DIR; the room's git file does."""
    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    if staff is not None:
        env["GIT_AUTHOR_NAME"] = staff
        env["GIT_AUTHOR_EMAIL"] = f"{staff}@chat.company"
        env["GIT_COMMITTER_NAME"] = staff
        env["GIT_COMMITTER_EMAIL"] = f"{staff}@chat.company"
    return subprocess.run(
        ["git", "-C", str(folder), *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def require(proc: subprocess.CompletedProcess[str]) -> str:
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout)
        raise SystemExit(proc.returncode or 1)
    return proc.stdout.strip()


def branch_exists(store: Path, branch: str) -> bool:
    proc = git(store, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}")
    return proc.returncode == 0


def room_of_store(store: Path, folder: Path) -> bool:
    if not folder.is_dir():
        return False
    proc = subprocess.run(
        ["git", "-C", str(folder), "rev-parse", "--git-common-dir"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return False
    common = Path(proc.stdout.strip())
    if not common.is_absolute():
        common = (folder / common).resolve()
    return common.resolve() == store.resolve()


def seed_branch(store: Path, source: Path, branch: str, staff: str, message: str) -> None:
    require(git(store, "symbolic-ref", "HEAD", f"refs/heads/{branch}"))
    require(git(store, "add", "-A", worktree=source, staff=staff))
    quiet = git(store, "diff", "--cached", "--quiet", worktree=source)
    if quiet.returncode == 0:
        require(git(store, "commit", "--allow-empty", "-m", message, worktree=source, staff=staff))
    elif quiet.returncode != 1:
        require(quiet)
    else:
        require(git(store, "commit", "-m", message, worktree=source, staff=staff))
    # The seed used the store as its checkout. Point that checkout elsewhere
    # so `git worktree add` can take the room branch.
    require(git(store, "symbolic-ref", "HEAD", "refs/heads/__room_idle"))


def ensure_room(company: Path, source: Path, room_name: str, dest_parent: Path, join_only: bool = False, announce: bool = True) -> Path:
    """Create the work history and the room folder when they are missing."""
    del join_only  # a missing room is set up, not rejected
    store = ensure_store(company)
    branch = branch_name(room_name)
    dest = dest_parent / room_name
    if room_of_store(store, dest):
        if announce:
            print(dest)
        return dest
    dest_parent.mkdir(parents=True, exist_ok=True)
    if dest.is_dir():
        seed_from = dest
    elif source.is_dir() and source.resolve() != dest_parent.resolve():
        seed_from = source
    else:
        seed_from = None
    if not branch_exists(store, branch):
        if seed_from is None:
            seed_from = dest_parent / ".empty-room-seed"
            seed_from.mkdir(exist_ok=True)
            seed_branch(store, seed_from, branch, "company", "room start")
            seed_from.rmdir()
        else:
            seed_branch(store, seed_from, branch, "company", "room start")
    aside = None
    if dest.exists():
        aside = dest_parent / f".{room_name}.before-room"
        if aside.exists():
            shutil.rmtree(aside)
        dest.rename(aside)
    added = git(store, "worktree", "add", str(dest), branch)
    if added.returncode != 0:
        if aside is not None and not dest.exists():
            aside.rename(dest)
        used = "already used by worktree at '"
        err = added.stderr or ""
        if used in err:
            start = err.index(used) + len(used)
            end = err.find("'", start)
            existing = Path(err[start:end])
            if existing.is_dir():
                if announce:
                    print(existing)
                return existing
        sys.stderr.write(err)
        raise SystemExit(added.returncode or 1)
    if aside is not None and aside.exists():
        shutil.rmtree(aside)
    if announce:
        print(dest)
    return dest


def record(company: Path, room: Path, room_name: str, staff: str, message: str) -> str | None:
    if not message.strip():
        raise SystemExit("message is empty")
    author(staff)
    if not room_of_store(ensure_store(company), room):
        room = ensure_room(company, room if room.is_dir() else room.parent, room_name, room.parent, announce=False)
    branch = branch_name(room_name)
    head = git_at(room, "rev-parse", "--abbrev-ref", "HEAD")
    if head.returncode != 0 or head.stdout.strip() != branch:
        raise SystemExit(f"room is not checked out on {branch}")
    quiet = git_at(room, "diff", "--cached", "--quiet")
    if quiet.returncode == 0:
        return None
    if quiet.returncode != 1:
        require(quiet)
    require(git_at(room, "commit", "-m", message, staff=staff))
    return require(git_at(room, "rev-parse", "HEAD"))


def commit_header(store: Path, commit: str) -> None:
    proc = git(store, "show", "-s", "--format=author %an%nauthor-date %aI", commit)
    text = require(proc)
    if text:
        print(text)


def files(company: Path, commit: str) -> None:
    store = ensure_store(company)
    commit_header(store, commit)
    proc = git(store, "show", "--name-status", "--pretty=format:", commit)
    require(proc)
    sys.stdout.write(proc.stdout)
    if proc.stdout and not proc.stdout.endswith("\n"):
        sys.stdout.write("\n")


def diff(company: Path, commit: str, path: str | None) -> None:
    store = ensure_store(company)
    commit_header(store, commit)
    args = ["show", "--pretty=format:", "--patch", commit]
    if path:
        args.extend(["--", path])
    proc = git(store, *args)
    require(proc)
    sys.stdout.write(proc.stdout)


def rollback(company: Path, room: Path, room_name: str, commit: str) -> None:
    if not room.is_dir():
        raise SystemExit(f"room is not a directory: {room}")
    ensure_store(company)
    branch = branch_name(room_name)
    require(git_at(room, "reset", "--hard", commit))
    print(f"rollback {require(git_at(room, 'rev-parse', 'HEAD'))}")
    print(f"branch {branch}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Company work history")
    sub = parser.add_subparsers(dest="cmd", required=True)

    room = sub.add_parser("ensure-room")
    room.add_argument("--company", type=Path, required=True)
    room.add_argument("--source", type=Path, required=True)
    room.add_argument("--room-name", required=True)
    room.add_argument("--dest-parent", type=Path, required=True)
    room.add_argument("--join-only", action="store_true")

    rec = sub.add_parser("record")
    rec.add_argument("--company", type=Path, required=True)
    rec.add_argument("--room", type=Path, required=True)
    rec.add_argument("--room-name", required=True)
    rec.add_argument("--staff", required=True)
    rec.add_argument("--message", required=True)

    listed = sub.add_parser("files")
    listed.add_argument("--company", type=Path, required=True)
    listed.add_argument("--commit", required=True)

    shown = sub.add_parser("diff")
    shown.add_argument("--company", type=Path, required=True)
    shown.add_argument("--commit", required=True)
    shown.add_argument("--path")

    back = sub.add_parser("rollback")
    back.add_argument("--company", type=Path, required=True)
    back.add_argument("--room", type=Path, required=True)
    back.add_argument("--room-name", required=True)
    back.add_argument("--commit", required=True)

    args = parser.parse_args()
    if args.cmd == "ensure-room":
        ensure_room(args.company, args.source, args.room_name, args.dest_parent, args.join_only)
    elif args.cmd == "record":
        commit = record(args.company, args.room, args.room_name, args.staff, args.message)
        if commit:
            print(f"commit {commit}")
            print(f"branch {branch_name(args.room_name)}")
            print(f"author {args.staff}")
        else:
            print("commit none")
    elif args.cmd == "files":
        files(args.company, args.commit)
    elif args.cmd == "diff":
        diff(args.company, args.commit, args.path)
    else:
        rollback(args.company, args.room, args.room_name, args.commit)


if __name__ == "__main__":
    main()
