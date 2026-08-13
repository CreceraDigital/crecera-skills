#!/usr/bin/env python3
"""
Rebuild skills/ from a local Claude Code skills directory, with client-identifying
and machine-specific detail stripped out.

    python scripts/scrub.py              # rebuild every skill listed in scrub-rules.json
    python scripts/scrub.py humanizer    # rebuild just one
    python scripts/scrub.py --check      # scan the current skills/ tree, copy nothing

skills/ is generated output. Edit scripts/scrub-rules.json (or the source skill),
never the files under skills/ — this script overwrites them.

Exits non-zero if any leak_patterns survive into the output, so it is safe to wire
into CI or a pre-push hook.
"""

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_PATH = Path(__file__).resolve().parent / "scrub-rules.json"
DEST_ROOT = ROOT / "skills"

# Extensions we never rewrite in place (copied byte-for-byte, still leak-scanned
# if they happen to be decodable).
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz",
    ".woff", ".woff2", ".ttf", ".otf", ".mp4", ".mov", ".xlsx", ".docx",
}


def glob_to_re(pattern: str) -> re.Pattern:
    """Translate a git-style glob into a regex matched against a posix relpath.

    A trailing '/' means "this directory and everything beneath it".
    """
    dir_only = pattern.endswith("/")
    if dir_only:
        pattern = pattern[:-1]

    out, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1

    body = "".join(out)
    # A directory pattern also matches everything under that directory.
    suffix = "(?:/.*)?" if dir_only else ""
    return re.compile(f"^{body}{suffix}$")


def matches_any(relpath: str, patterns) -> bool:
    return any(p.search(relpath) for p in patterns)


def load_rules():
    with RULES_PATH.open(encoding="utf-8") as fh:
        rules = json.load(fh)

    rules["_exclude"] = [glob_to_re(g) for g in rules.get("exclude_globs", [])]
    rules["_leaks"] = [(p, re.compile(p)) for p in rules.get("leak_patterns", [])]

    compiled = []
    for r in rules.get("replacements", []):
        if r.get("regex"):
            pat = re.compile(r["pattern"])
        else:
            pat = re.compile(re.escape(r["pattern"]))
        scope = glob_to_re(r["scope"]) if r.get("scope") else None
        compiled.append((pat, r["replace"], scope))
    rules["_replacements"] = compiled
    return rules


# A '~'-rooted path that still carries Windows separators, e.g. the tail left
# behind after 'C:\Users\me\.claude\plans\' becomes '~\.claude\plans\'.
HOME_PATH_RE = re.compile(r"~(?:[\\/][A-Za-z0-9._<>*+-]+)+[\\/]?")


def normalise_home_paths(text: str) -> tuple[str, int]:
    """Rewrite backslashes to forward slashes inside '~'-rooted paths only.

    Runs after the configured replacements, which turn absolute user paths into
    '~'. Left alone, those tails read as '~/.claude\\plans\\' on every platform.
    """
    count = 0

    def sub(m):
        nonlocal count
        original = m.group(0)
        fixed = original.replace("\\", "/")
        if fixed != original:
            count += 1
        return fixed

    return HOME_PATH_RE.sub(sub, text), count


def scrub_text(text: str, relpath: str, replacements) -> tuple[str, int]:
    total = 0
    for pat, repl, scope in replacements:
        if scope is not None and not scope.search(relpath):
            continue
        text, n = pat.subn(repl, text)
        total += n
    text, n = normalise_home_paths(text)
    return text, total + n


def build_skill(name: str, rules) -> dict:
    src_root = Path(os.path.expanduser(rules["source_dir"])) / name
    if not src_root.is_dir():
        raise SystemExit(f"source skill not found: {src_root}")

    dest_root = DEST_ROOT / name
    if dest_root.exists():
        shutil.rmtree(dest_root)

    stats = {"files": 0, "skipped": 0, "edits": 0}

    for src in sorted(src_root.rglob("*")):
        if not src.is_file():
            continue
        rel_in_skill = src.relative_to(src_root).as_posix()
        rel_in_repo = f"{name}/{rel_in_skill}"

        if matches_any(rel_in_skill, rules["_exclude"]) or matches_any(
            rel_in_repo, rules["_exclude"]
        ):
            stats["skipped"] += 1
            continue

        dest = dest_root / rel_in_skill
        dest.parent.mkdir(parents=True, exist_ok=True)

        if src.suffix.lower() in BINARY_EXT:
            shutil.copy2(src, dest)
            stats["files"] += 1
            continue

        raw = src.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            shutil.copy2(src, dest)
            stats["files"] += 1
            continue

        text, n = scrub_text(text, rel_in_repo, rules["_replacements"])
        dest.write_text(text, encoding="utf-8", newline="")
        stats["files"] += 1
        stats["edits"] += n

    return stats


def check_leaks(rules) -> list:
    findings = []
    if not DEST_ROOT.is_dir():
        return findings

    for path in sorted(DEST_ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() in BINARY_EXT:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(ROOT).as_posix()
        for lineno, line in enumerate(text.splitlines(), 1):
            for pattern_src, pat in rules["_leaks"]:
                if pat.search(line):
                    findings.append((rel, lineno, pattern_src, line.strip()[:120]))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skills", nargs="*",
                    help="skill names to rebuild (default: all in scrub-rules.json)")
    ap.add_argument("--check", action="store_true",
                    help="only scan the existing skills/ tree for leaks")
    args = ap.parse_args()

    rules = load_rules()

    if not args.check:
        targets = args.skills or rules["skills"]
        unknown = [s for s in targets if s not in rules["skills"]]
        if unknown:
            raise SystemExit(
                f"not listed in scrub-rules.json: {', '.join(unknown)}\n"
                f"Add it to the \"skills\" array first.")

        DEST_ROOT.mkdir(parents=True, exist_ok=True)
        for name in targets:
            st = build_skill(name, rules)
            print(f"  {name:<26} {st['files']:>3} files  "
                  f"{st['skipped']:>3} skipped  {st['edits']:>3} redactions")

    findings = check_leaks(rules)
    print()
    if findings:
        print(f"LEAK CHECK FAILED — {len(findings)} hit(s):\n")
        for rel, lineno, pattern_src, line in findings[:40]:
            print(f"  {rel}:{lineno}\n    pattern: {pattern_src}\n    {line}\n")
        if len(findings) > 40:
            print(f"  ... and {len(findings) - 40} more")
        print("Add a rule to scrub-rules.json, then re-run.")
        return 1

    print("Leak check passed — no client names, credentials, or local paths found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
