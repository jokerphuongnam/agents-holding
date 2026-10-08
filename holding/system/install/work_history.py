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
Each staff stages into their own index, so two claims in one room stay apart.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
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


def git(store: Path, *args: str, cwd: Path | None = None, worktree: Path | None = None, staff: str | None = None, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
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
        input=input_text,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def git_at(folder: Path, *args: str, staff: str | None = None, index: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Git commands inside a linked room. Do not set GIT_DIR; the room's git file does."""
    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    if index is not None:
        env["GIT_INDEX_FILE"] = str(index)
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


def project_git(source: Path) -> Path | None:
    if not source.is_dir():
        return None
    proc = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "--git-common-dir"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    found = Path(proc.stdout.strip())
    if not found.is_absolute():
        found = (source / found).resolve()
    return found


def mirror_project(store: Path, source: Path) -> str | None:
    """Copy the project branches into refs/heads/mirror/*. Room branches stay put."""
    origin = project_git(source)
    if origin is None or origin.resolve() == store.resolve():
        return None
    require(git(store, "fetch", "--no-tags", str(origin), "+refs/heads/*:refs/heads/mirror/*"))
    head = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if head.returncode != 0:
        return None
    return head.stdout.strip()


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
    mirrored = mirror_project(store, source if source.is_dir() else seed_from or source)
    if not branch_exists(store, branch):
        if mirrored:
            require(git(store, "branch", branch, mirrored))
        elif seed_from is None:
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


def claims_dir(company: Path, room_name: str) -> Path:
    token = branch_name(room_name).split("/", 1)[1].replace("/", "-")
    path = company / "cache" / "work-history-indexes" / token
    path.mkdir(parents=True, exist_ok=True)
    return path


def claim_paths(company: Path, room_name: str, staff: str) -> tuple[Path, Path]:
    name = author(staff)
    root = claims_dir(company, room_name)
    return root / name, root / f"{name}.base"


def claim_pairs(company: Path, room_name: str) -> list[tuple[str, Path, Path]]:
    root = company / "cache" / "work-history-indexes" / branch_name(room_name).split("/", 1)[1].replace("/", "-")
    if not root.is_dir():
        return []
    pairs = []
    for index in sorted(root.iterdir()):
        if not index.is_file() or index.name.endswith(".base") or index.name.endswith(".record"):
            continue
        base = index.with_name(f"{index.name}.base")
        if base.is_file():
            pairs.append((index.name, index, base))
    return pairs


def ensure_claim(room: Path, company: Path, room_name: str, staff: str) -> tuple[Path, Path]:
    index, base = claim_paths(company, room_name, staff)
    if not index.exists():
        head = require(git_at(room, "rev-parse", "HEAD"))
        require(git_at(room, "read-tree", "HEAD", index=index))
        base.write_text(head + "\n", encoding="utf-8")
    return index, base


def clear_claim(index: Path, base: Path) -> None:
    index.unlink(missing_ok=True)
    base.unlink(missing_ok=True)


def room_blob(room: Path, rev: str, path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "-C", str(room), "cat-file", "blob", f"{rev}:{path}"],
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def put_blob(room: Path, index: Path, path: str, data: bytes) -> None:
    hashed = subprocess.run(
        ["git", "-C", str(room), "hash-object", "-w", "--stdin"],
        input=data,
        check=False,
        capture_output=True,
    )
    blob = require(subprocess.CompletedProcess(hashed.args, hashed.returncode, hashed.stdout.decode(), hashed.stderr.decode()))
    mode = "100644"
    require(git_at(room, "update-index", "--add", "--cacheinfo", f"{mode},{blob},{path}", index=index))


def overlay_claim(room: Path, base: str, staff_tree: str, index: Path) -> None:
    """Replay one staff claim onto HEAD. Same lines keep this staff's text."""
    names = git_at(room, "diff", "--name-status", "--no-renames", base, staff_tree)
    require(names)
    for line in names.stdout.splitlines():
        status, path = line.split("\t", 1)
        if status.startswith("D"):
            git_at(room, "update-index", "--force-remove", "--", path, index=index)
            continue
        staff = room_blob(room, staff_tree, path)
        if staff is None:
            continue
        head = room_blob(room, "HEAD", path)
        earlier = room_blob(room, base, path)
        if b"\0" in staff or (head is not None and b"\0" in head) or head is None or earlier is None:
            put_blob(room, index, path, staff)
            continue
        current = tempfile.NamedTemporaryFile(delete=False)
        base_file = tempfile.NamedTemporaryFile(delete=False)
        other = tempfile.NamedTemporaryFile(delete=False)
        try:
            current.write(head)
            base_file.write(earlier)
            other.write(staff)
            current.close()
            base_file.close()
            other.close()
            merged = subprocess.run(
                ["git", "merge-file", "-p", "--theirs", current.name, base_file.name, other.name],
                check=False,
                capture_output=True,
            )
            if merged.returncode not in (0, 1):
                sys.stderr.write(merged.stderr.decode())
                raise SystemExit(merged.returncode or 1)
            put_blob(room, index, path, merged.stdout)
        finally:
            for handle in (current, base_file, other):
                Path(handle.name).unlink(missing_ok=True)


def record(company: Path, room: Path, room_name: str, staff: str, message: str) -> str | None:
    if not message.strip():
        raise SystemExit("message is empty")
    author(staff)
    room = open_room(company, room, room_name)
    index, base_path = claim_paths(company, room_name, staff)
    if not index.is_file() or not base_path.is_file():
        return None
    base = base_path.read_text(encoding="utf-8").strip()
    staff_tree = require(git_at(room, "write-tree", index=index))
    base_tree = require(git_at(room, "rev-parse", f"{base}^{{tree}}"))
    if staff_tree == base_tree:
        clear_claim(index, base_path)
        return None
    merged = index.with_name(f"{index.name}.record")
    merged.unlink(missing_ok=True)
    require(git_at(room, "read-tree", "HEAD", index=merged))
    overlay_claim(room, base, staff_tree, merged)
    result = require(git_at(room, "write-tree", index=merged))
    head_tree = require(git_at(room, "rev-parse", "HEAD^{tree}"))
    if result == head_tree:
        merged.unlink(missing_ok=True)
        clear_claim(index, base_path)
        return None
    require(git_at(room, "commit", "-m", message, staff=staff, index=merged))
    merged.unlink(missing_ok=True)
    clear_claim(index, base_path)
    require(git_at(room, "reset", "-q"))
    return require(git_at(room, "rev-parse", "HEAD"))


def side_branch(prefix: str, room_name: str) -> str:
    return prefix + "/" + branch_name(room_name).split("/", 1)[1]


def write_side(company: Path, room_name: str, prefix: str, filename: str, content: str, who: str, message: str, body: str | None = None) -> str:
    store = ensure_store(company)
    branch = side_branch(prefix, room_name)
    blob = require(git(store, "hash-object", "-w", "--stdin", staff=who, input_text=content))
    tree = require(git(store, "mktree", staff=who, input_text=f"100644 blob {blob}\t{filename}\n"))
    command = ["commit-tree", tree]
    if branch_exists(store, branch):
        command.extend(["-p", require(git(store, "rev-parse", branch))])
    command.extend(["-m", message])
    if body:
        command.extend(["-m", body])
    commit = require(git(store, *command, staff=who))
    require(git(store, "update-ref", f"refs/heads/{branch}", commit))
    return commit


def say(company: Path, room_name: str, who: str, message: str, thread: str = "ceo") -> str:
    if not message.strip():
        raise SystemExit("message is empty")
    who = author(who)
    thread = thread.strip() or "ceo"
    if any(c in thread for c in "<>\n"):
        raise SystemExit("thread name is empty")
    return write_side(company, room_name, "talk", "message", message, who, message, f"thread {thread}")


def talk(company: Path, room_name: str) -> None:
    store = ensure_store(company)
    branch = side_branch("talk", room_name)
    if not branch_exists(store, branch):
        return
    proc = git(store, "log", "--format=---%nhash %H%nauthor %an%nauthor-date %aI%nbody %b%nmessage %s", branch)
    require(proc)
    sys.stdout.write(proc.stdout)


def status_text(company: Path, room_name: str) -> str:
    store = ensure_store(company)
    branch = side_branch("status", room_name)
    if not branch_exists(store, branch):
        return ""
    proc = git(store, "show", f"{branch}:status.tsv")
    if proc.returncode != 0:
        return ""
    return proc.stdout


def set_status(company: Path, room_name: str, staff: str, state: str, message: str) -> None:
    if state not in {"will-do", "doing", "done"}:
        raise SystemExit("state must be will-do, doing, or done")
    staff = author(staff)
    rows: dict[str, tuple[str, str]] = {}
    for line in status_text(company, room_name).splitlines():
        name, current, text = line.split("\t", 2)
        rows[name] = (current, text)
    rows[staff] = (state, message.replace("\n", " ").strip())
    body = "".join(f"{name}\t{current}\t{text}\n" for name, (current, text) in sorted(rows.items()))
    write_side(company, room_name, "status", "status.tsv", body, staff, message.strip() or state)
    print(f"state {staff} {state}")


def claim_worktree(company: Path, room: Path, room_name: str, staff: str) -> None:
    dirty = git_at(room, "diff", "HEAD", "--name-only")
    require(dirty)
    extra = git_at(room, "ls-files", "--others", "--exclude-standard")
    require(extra)
    paths = [line for line in dirty.stdout.splitlines() + extra.stdout.splitlines() if line]
    if not paths:
        return
    index, _base = ensure_claim(room, company, room_name, staff)
    for path in paths:
        _header, parts = file_patch(room, path, False)
        for number in range(len(parts)):
            apply_hunk(room, path, False, number, False, index=index)


def capture(company: Path, room: Path, room_name: str, staff: str, message: str) -> str | None:
    room = open_room(company, room, room_name)
    claim_worktree(company, room, room_name, staff)
    commit = record(company, room, room_name, staff, message)
    spoken = say(company, room_name, staff, message)
    print(f"talk {spoken}")
    return commit


def commit_header(store: Path, commit: str) -> None:
    proc = git(store, "show", "-s", "--format=hash %H%nauthor %an%nauthor-date %aI%nmessage %s", commit)
    text = require(proc)
    if text:
        print(text)


def open_room(company: Path, room: Path, room_name: str) -> Path:
    if not room_of_store(ensure_store(company), room):
        room = ensure_room(company, room if room.is_dir() else room.parent, room_name, room.parent, announce=False)
    branch = branch_name(room_name)
    head = git_at(room, "rev-parse", "--abbrev-ref", "HEAD")
    if head.returncode != 0 or head.stdout.strip() != branch:
        raise SystemExit(f"room is not checked out on {branch}")
    return room


def working(company: Path, room: Path, room_name: str) -> None:
    room = open_room(company, room, room_name)
    print("state")
    text = status_text(company, room_name)
    sys.stdout.write(text or "\n")
    pairs = claim_pairs(company, room_name)
    if not pairs:
        print("staged")
        print()
    for staff, index, base_path in pairs:
        base = base_path.read_text(encoding="utf-8").strip()
        print(f"staged {staff}")
        staged = git_at(room, "diff", "--cached", "--name-status", base, index=index)
        require(staged)
        sys.stdout.write(staged.stdout or "\n")
    print("unstaged")
    dirty = git_at(room, "diff", "HEAD", "--name-status")
    require(dirty)
    sys.stdout.write(dirty.stdout or "\n")
    extra = git_at(room, "ls-files", "--others", "--exclude-standard")
    require(extra)
    for name in extra.stdout.splitlines():
        print(f"??\t{name}")
    print("unstaged-diff")
    diff = git_at(room, "diff", "HEAD")
    require(diff)
    sys.stdout.write(diff.stdout)
    for name in extra.stdout.splitlines():
        fresh = untracked_patch(room, name)
        if fresh:
            sys.stdout.write(fresh)


def patch_parts(text: str) -> tuple[str, list[str]]:
    lines = text.splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.startswith("@@")), None)
    if start is None:
        return text, []
    header = "".join(lines[:start])
    hunks: list[str] = []
    current: list[str] = []
    for line in lines[start:]:
        if line.startswith("@@") and current:
            hunks.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        hunks.append("".join(current))
    return header, hunks


def untracked_patch(room: Path, path: str) -> str:
    target = room / path
    if not target.is_file():
        return ""
    proc = git_at(room, "diff", "--no-index", "--binary", "--", "/dev/null", path)
    text = proc.stdout
    if not text.strip():
        return ""
    rewritten = []
    for line in text.splitlines(keepends=True):
        if line.startswith("diff --git "):
            rewritten.append(f"diff --git a/{path} b/{path}\n")
        elif line.startswith("--- "):
            rewritten.append("--- /dev/null\n")
        elif line.startswith("+++ "):
            rewritten.append(f"+++ b/{path}\n")
        else:
            rewritten.append(line)
    return "".join(rewritten)


def file_patch(room: Path, path: str, staged: bool, index: Path | None = None, base: str | None = None) -> tuple[str, list[str]]:
    if staged:
        if index is None or base is None:
            return "", []
        proc = git_at(room, "diff", "--cached", "--binary", base, "--", path, index=index)
        require(proc)
        return patch_parts(proc.stdout)
    proc = git_at(room, "diff", "HEAD", "--binary", "--", path)
    require(proc)
    if proc.stdout.strip():
        return patch_parts(proc.stdout)
    return patch_parts(untracked_patch(room, path))


def show_hunks(label: str, parts: list[str]) -> None:
    for number, hunk in enumerate(parts):
        first = next((line for line in hunk.splitlines() if line.startswith("@@")), "@@")
        print(f"{label} {number} {first}")


def hunks(company: Path, room: Path, room_name: str, path: str, staff: str | None) -> None:
    room = open_room(company, room, room_name)
    _header, parts = file_patch(room, path, False)
    show_hunks("unstaged", parts)
    pairs = claim_pairs(company, room_name)
    if staff:
        pairs = [item for item in pairs if item[0] == author(staff)]
    for name, index, base_path in pairs:
        base = base_path.read_text(encoding="utf-8").strip()
        _header, claimed = file_patch(room, path, True, index, base)
        show_hunks(f"staged {name}", claimed)


def apply_hunk(room: Path, path: str, staged: bool, number: int, reverse: bool, index: Path | None = None, base: str | None = None) -> None:
    header, parts = file_patch(room, path, staged, index, base)
    if number < 0 or number >= len(parts):
        raise SystemExit(f"hunk {number} is not in {path}")
    patch = header + parts[number]
    if not patch.endswith("\n"):
        patch += "\n"
    if reverse and staged:
        require(subprocess_apply(room, ["apply", "-R", "--cached", "--binary"], patch, index=index))
        require(subprocess_apply(room, ["apply", "-R", "--binary"], patch))
        return
    if reverse:
        require(subprocess_apply(room, ["apply", "-R", "--binary"], patch))
        return
    if staged:
        raise SystemExit("that hunk is already staged")
    require(subprocess_apply(room, ["apply", "--cached", "--binary"], patch, index=index))


def accept(company: Path, room: Path, room_name: str, path: str, hunk: int, staff: str) -> None:
    room = open_room(company, room, room_name)
    index, _base = ensure_claim(room, company, room_name, staff)
    apply_hunk(room, path, False, hunk, False, index=index)
    print(f"accepted {path} {hunk}")
    print(f"staff {author(staff)}")


def discard(company: Path, room: Path, room_name: str, path: str, hunk: int, staged: bool, staff: str | None) -> None:
    room = open_room(company, room, room_name)
    index = None
    base = None
    if staged:
        if not staff:
            raise SystemExit("staged discard needs a staff")
        index, base_path = claim_paths(company, room_name, staff)
        if not index.is_file() or not base_path.is_file():
            raise SystemExit(f"hunk {hunk} is not in {path}")
        base = base_path.read_text(encoding="utf-8").strip()
    apply_hunk(room, path, staged, hunk, True, index=index, base=base)
    print(f"discarded {path} {hunk}")


def drop_path_from_claims(room: Path, company: Path, room_name: str, path: str) -> None:
    for _staff, index, base_path in claim_pairs(company, room_name):
        base = base_path.read_text(encoding="utf-8").strip()
        git_at(room, "rm", "--cached", "--ignore-unmatch", "--", path, index=index)
        tracked = git_at(room, "cat-file", "-e", f"{base}:{path}")
        if tracked.returncode == 0:
            require(git_at(room, "restore", "--source", base, "--staged", "--", path, index=index))


def fallback(company: Path, room: Path, room_name: str, path: str | None) -> None:
    """Put in-progress edits back to the last commit. Later commits stay."""
    room = open_room(company, room, room_name)
    if path:
        tracked = git_at(room, "cat-file", "-e", f"HEAD:{path}")
        if tracked.returncode == 0:
            require(git_at(room, "restore", "--source=HEAD", "--staged", "--worktree", "--", path))
        else:
            target = room / path
            if target.is_file() or target.is_symlink():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(target)
            else:
                raise SystemExit(f"path is not in the room: {path}")
        drop_path_from_claims(room, company, room_name, path)
        print(f"fallback {path}")
        return
    require(git_at(room, "reset", "--hard", "HEAD"))
    require(git_at(room, "clean", "-fd"))
    root = company / "cache" / "work-history-indexes" / branch_name(room_name).split("/", 1)[1].replace("/", "-")
    if root.exists():
        shutil.rmtree(root)
    print("fallback HEAD")


def revert(company: Path, room: Path, room_name: str, commit: str, staff: str, message: str) -> None:
    if not message.strip():
        raise SystemExit("message is empty")
    author(staff)
    room = open_room(company, room, room_name)
    require(git_at(room, "reset", "-q"))
    undone = git_at(room, "revert", "--no-commit", "-X", "theirs", commit)
    if undone.returncode != 0:
        git_at(room, "revert", "--abort")
        sys.stderr.write(undone.stderr or undone.stdout)
        raise SystemExit(undone.returncode or 1)
    quiet = git_at(room, "diff", "--cached", "--quiet")
    if quiet.returncode == 0:
        print("commit none")
        return
    require(git_at(room, "commit", "-m", message, staff=staff))
    print(f"commit {require(git_at(room, 'rev-parse', 'HEAD'))}")
    print(f"reverted {commit}")


def log(company: Path, room_name: str) -> None:
    store = ensure_store(company)
    branch = branch_name(room_name)
    proc = git(store, "log", "--format=hash %H%nauthor %an%nauthor-date %aI%nmessage %s%n", branch)
    require(proc)
    sys.stdout.write(proc.stdout)


def subprocess_apply(room: Path, args: list[str], patch: str, index: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("GIT_DIR", None)
    env.pop("GIT_WORK_TREE", None)
    if index is not None:
        env["GIT_INDEX_FILE"] = str(index)
    return subprocess.run(
        ["git", "-C", str(room), *args],
        input=patch,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


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

    copied = sub.add_parser("mirror")
    copied.add_argument("--company", type=Path, required=True)
    copied.add_argument("--source", type=Path, required=True)

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

    doing = sub.add_parser("working")
    doing.add_argument("--company", type=Path, required=True)
    doing.add_argument("--room", type=Path, required=True)
    doing.add_argument("--room-name", required=True)

    pieces = sub.add_parser("hunks")
    pieces.add_argument("--company", type=Path, required=True)
    pieces.add_argument("--room", type=Path, required=True)
    pieces.add_argument("--room-name", required=True)
    pieces.add_argument("--path", required=True)
    pieces.add_argument("--staff")

    taken = sub.add_parser("accept")
    taken.add_argument("--company", type=Path, required=True)
    taken.add_argument("--room", type=Path, required=True)
    taken.add_argument("--room-name", required=True)
    taken.add_argument("--path", required=True)
    taken.add_argument("--hunk", type=int, required=True)
    taken.add_argument("--staff", required=True)

    dropped = sub.add_parser("discard")
    dropped.add_argument("--company", type=Path, required=True)
    dropped.add_argument("--room", type=Path, required=True)
    dropped.add_argument("--room-name", required=True)
    dropped.add_argument("--path", required=True)
    dropped.add_argument("--hunk", type=int, required=True)
    dropped.add_argument("--staged", action="store_true")
    dropped.add_argument("--staff")

    undone = sub.add_parser("revert")
    undone.add_argument("--company", type=Path, required=True)
    undone.add_argument("--room", type=Path, required=True)
    undone.add_argument("--room-name", required=True)
    undone.add_argument("--commit", required=True)
    undone.add_argument("--staff", required=True)
    undone.add_argument("--message", required=True)

    back_file = sub.add_parser("fallback")
    back_file.add_argument("--company", type=Path, required=True)
    back_file.add_argument("--room", type=Path, required=True)
    back_file.add_argument("--room-name", required=True)
    back_file.add_argument("--path")

    history = sub.add_parser("log")
    history.add_argument("--company", type=Path, required=True)
    history.add_argument("--room-name", required=True)

    spoken = sub.add_parser("say")
    spoken.add_argument("--company", type=Path, required=True)
    spoken.add_argument("--room-name", required=True)
    spoken.add_argument("--who", required=True)
    spoken.add_argument("--message", required=True)
    spoken.add_argument("--thread", default="ceo")

    transcript = sub.add_parser("talk")
    transcript.add_argument("--company", type=Path, required=True)
    transcript.add_argument("--room-name", required=True)

    marked = sub.add_parser("status")
    marked.add_argument("--company", type=Path, required=True)
    marked.add_argument("--room-name", required=True)
    marked.add_argument("--staff", required=True)
    marked.add_argument("--state", required=True)
    marked.add_argument("--message", default="")

    taken_all = sub.add_parser("capture")
    taken_all.add_argument("--company", type=Path, required=True)
    taken_all.add_argument("--room", type=Path, required=True)
    taken_all.add_argument("--room-name", required=True)
    taken_all.add_argument("--staff", required=True)
    taken_all.add_argument("--message", required=True)

    args = parser.parse_args()
    if args.cmd == "ensure-room":
        ensure_room(args.company, args.source, args.room_name, args.dest_parent, args.join_only)
    elif args.cmd == "mirror":
        store = ensure_store(args.company)
        head = mirror_project(store, args.source)
        if head:
            print(f"mirror {head}")
        else:
            print("mirror none")
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
    elif args.cmd == "rollback":
        rollback(args.company, args.room, args.room_name, args.commit)
    elif args.cmd == "working":
        working(args.company, args.room, args.room_name)
    elif args.cmd == "hunks":
        hunks(args.company, args.room, args.room_name, args.path, args.staff)
    elif args.cmd == "accept":
        accept(args.company, args.room, args.room_name, args.path, args.hunk, args.staff)
    elif args.cmd == "discard":
        discard(args.company, args.room, args.room_name, args.path, args.hunk, args.staged, args.staff)
    elif args.cmd == "revert":
        revert(args.company, args.room, args.room_name, args.commit, args.staff, args.message)
    elif args.cmd == "fallback":
        fallback(args.company, args.room, args.room_name, args.path)
    elif args.cmd == "say":
        print(f"talk {say(args.company, args.room_name, args.who, args.message, args.thread)}")
    elif args.cmd == "talk":
        talk(args.company, args.room_name)
    elif args.cmd == "status":
        set_status(args.company, args.room_name, args.staff, args.state, args.message)
    elif args.cmd == "capture":
        commit = capture(args.company, args.room, args.room_name, args.staff, args.message)
        if commit:
            print(f"commit {commit}")
            print(f"branch {branch_name(args.room_name)}")
            print(f"author {args.staff}")
        else:
            print("commit none")
    else:
        log(args.company, args.room_name)


if __name__ == "__main__":
    main()
