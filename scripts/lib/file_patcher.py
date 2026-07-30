"""Shared utilities for safe, idempotent file patching."""

import os
import re
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List


class PatchResult:
    def __init__(self, file_path: str, changed: bool, detail: str = ""):
        self.file_path = file_path
        self.changed = changed
        self.detail = detail

    def __repr__(self):
        status = "CHANGED" if self.changed else "UNCHANGED"
        return f"[{status}] {self.file_path} {self.detail}"


def read_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    dir_name = os.path.dirname(file_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, file_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def patch_text(content: str, old: str, new: str, count: int = 0) -> tuple:
    """Replace `old` with `new` in `content`. Returns (new_content, num_replacements).
    If count > 0, only replace that many occurrences."""
    if old not in content:
        return content, 0
    if count == 0:
        n = content.count(old)
        return content.replace(old, new), n
    return content.replace(old, new, count), count


def patch_regex(content: str, pattern: str, replacement: str, count: int = 0) -> tuple:
    """Replace regex `pattern` with `replacement` in `content`. Returns (new_content, num_replacements)."""
    compiled = re.compile(pattern)
    if count == 0:
        new_content, n = compiled.subn(replacement, content)
    else:
        new_content, n = compiled.subn(replacement, content, count=count)
    return new_content, n


def patch_file(file_path: str, old: str, new: str, count: int = 0) -> PatchResult:
    """Replace literal `old` with `new` in a file. Idempotent."""
    if not os.path.exists(file_path):
        return PatchResult(file_path, False, "file not found")
    content = read_file(file_path)
    new_content, n = patch_text(content, old, new, count)
    if n == 0:
        return PatchResult(file_path, False, "pattern not found")
    write_file(file_path, new_content)
    return PatchResult(file_path, True, f"replaced {n} occurrence(s)")


def patch_file_regex(file_path: str, pattern: str, replacement: str, count: int = 0) -> PatchResult:
    """Replace regex `pattern` with `replacement` in a file. Idempotent."""
    if not os.path.exists(file_path):
        return PatchResult(file_path, False, "file not found")
    content = read_file(file_path)
    new_content, n = patch_regex(content, pattern, replacement, count)
    if n == 0:
        return PatchResult(file_path, False, "pattern not found")
    write_file(file_path, new_content)
    return PatchResult(file_path, True, f"replaced {n} occurrence(s)")


def patch_lines(file_path: str, line_start: int, line_end: int, new_lines: str) -> PatchResult:
    """Replace lines [line_start, line_end) (1-indexed) with new_lines string."""
    if not os.path.exists(file_path):
        return PatchResult(file_path, False, "file not found")
    content = read_file(file_path)
    lines = content.split("\n")
    if line_start < 1 or line_end > len(lines) + 1:
        return PatchResult(file_path, False, "line range out of bounds")
    new_content = "\n".join(lines[:line_start - 1] + new_lines.split("\n") + lines[line_end:])
    write_file(file_path, new_content)
    return PatchResult(file_path, True, f"replaced lines {line_start}-{line_end}")


def insert_after(file_path: str, marker: str, new_lines: str) -> PatchResult:
    """Insert new_lines after the first line containing marker."""
    if not os.path.exists(file_path):
        return PatchResult(file_path, False, "file not found")
    content = read_file(file_path)
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if marker in line:
            insert_block = new_lines.split("\n")
            new_content = "\n".join(lines[:i + 1] + insert_block + lines[i + 1:])
            write_file(file_path, new_content)
            return PatchResult(file_path, True, f"inserted after line {i + 1}")
    return PatchResult(file_path, False, f"marker '{marker}' not found")


def insert_before(file_path: str, marker: str, new_lines: str) -> PatchResult:
    """Insert new_lines before the first line containing marker."""
    if not os.path.exists(file_path):
        return PatchResult(file_path, False, "file not found")
    content = read_file(file_path)
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if marker in line:
            insert_block = new_lines.split("\n")
            new_content = "\n".join(lines[:i] + insert_block + lines[i + 1:])
            write_file(file_path, new_content)
            return PatchResult(file_path, True, f"inserted before line {i + 1}")
    return PatchResult(file_path, False, f"marker '{marker}' not found")


def verify_contains(file_path: str, expected: str) -> bool:
    """Check if file contains expected text."""
    if not os.path.exists(file_path):
        return False
    return expected in read_file(file_path)


def verify_not_contains(file_path: str, stale: str) -> bool:
    """Check if file does NOT contain stale text."""
    if not os.path.exists(file_path):
        return True
    return stale not in read_file(file_path)


def find_files(root: str, patterns: List[str], excludes: Optional[List[str]] = None) -> List[str]:
    """Find files matching any of the glob patterns, excluding any matching exclude patterns."""
    import fnmatch
    results = []
    excludes = excludes or []
    for dirpath, dirnames, filenames in os.walk(root):
        for skip in [".git", "node_modules", "__pycache__", ".cache"]:
            if skip in dirnames:
                dirnames.remove(skip)
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if any(fnmatch.fnmatch(full_path, pat) or fnmatch.fnmatch(filename, pat) for pat in patterns):
                if not any(ex in full_path for ex in excludes):
                    results.append(full_path)
    return sorted(results)


def replace_in_files(file_paths: List[str], old: str, new: str) -> List[PatchResult]:
    """Apply a literal replacement across multiple files."""
    return [patch_file(fp, old, new) for fp in file_paths if os.path.exists(fp)]


def replace_in_files_regex(file_paths: List[str], pattern: str, replacement: str) -> List[PatchResult]:
    """Apply a regex replacement across multiple files."""
    return [patch_file_regex(fp, pattern, replacement) for fp in file_paths if os.path.exists(fp)]
