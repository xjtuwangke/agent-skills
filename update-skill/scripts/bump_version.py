#!/usr/bin/env python3
"""
bump_version.py - Bump the version of a skill and enforce monotonicity.

Usage:
    python bump_version.py <skill-dir> --type major|minor|patch
    python bump_version.py <skill-dir> --type minor --dry-run

Exits 0 on success, 1 on failure.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-[\w.]+)?$")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("frontmatter must start with '---' on line 1")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("frontmatter must close with '---' on its own line")
    fm_text = text[4:end]
    body = text[end + len("\n---\n"):]

    try:
        import yaml
        data = yaml.safe_load(fm_text) or {}
        if not isinstance(data, dict):
            raise ValueError("frontmatter must be a YAML mapping")
        return data, body
    except ImportError:
        return _parse_yaml_subset(fm_text), body


def _parse_yaml_subset(text: str) -> dict:
    lines = text.splitlines()
    root: dict = {}
    i = 0
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent != 0:
            i += 1
            continue
        if ":" not in raw:
            raise ValueError(f"malformed line {i+1}: {raw!r}")
        key, _, rest = raw.partition(":")
        key = key.strip()
        rest = rest.strip()

        if rest in (">", "|"):
            i += 1
            buf = []
            while i < len(lines):
                line = lines[i]
                if line.strip() == "" or line.startswith(" "):
                    buf.append(line[2:] if line.startswith("  ") else line.strip())
                    i += 1
                else:
                    break
            joined = ("\n".join(buf) if rest == "|" else " ".join(b for b in buf if b.strip()))
            root[key] = joined.strip()
            continue

        if rest.startswith("[") and rest.endswith("]"):
            inner = rest[1:-1].strip()
            items = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
            root[key] = items
            i += 1
            continue

        if rest == "":
            i += 1
            child = _read_block(lines, i)
            root[key] = child["data"]
            i = child["next_i"]
            continue

        root[key] = _parse_scalar(rest)
        i += 1
    return root


def _read_block(lines: list[str], start: int):
    block_lines = []
    i = start
    while i < len(lines):
        raw = lines[i]
        if raw.strip() == "":
            i += 1
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent < 2:
            break
        block_lines.append(raw[2:])
        i += 1
    if block_lines and block_lines[0].lstrip().startswith("- "):
        items = []
        for line in block_lines:
            if line.strip().startswith("- "):
                items.append(_parse_scalar(line.strip()[2:]))
            elif items and isinstance(items[-1], str):
                items[-1] += " " + line.strip()
        return {"data": items, "next_i": i}
    sub = _parse_yaml_subset("\n".join(block_lines))
    return {"data": sub, "next_i": i}


def _parse_scalar(s: str):
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [x.strip().strip('"').strip("'") for x in inner.split(",")]
    if s.lower() in {"true", "yes", "on"}:
        return True
    if s.lower() in {"false", "no", "off"}:
        return False
    if s.lower() in {"null", "~", ""}:
        return None
    try:
        if "." in s:
            return float(s)
        return int(s)
    except ValueError:
        return s


def bump_version(current: str, bump_type: str) -> str:
    m = SEMVER_RE.match(current)
    if not m:
        raise ValueError(f"version {current!r} is not SemVer 2.0")
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"unknown bump type: {bump_type}")


def compare_versions(a: str, b: str) -> int:
    """Return -1 if a < b, 0 if a == b, 1 if a > b."""
    def _parts(v: str):
        m = SEMVER_RE.match(v)
        if not m:
            raise ValueError(f"invalid version: {v!r}")
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    pa, pb = _parts(a), _parts(b)
    if pa < pb:
        return -1
    elif pa > pb:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", type=Path, help="Path to the skill directory.")
    parser.add_argument("--type", required=True, choices=["major", "minor", "patch"], help="Bump type.")
    parser.add_argument("--dry-run", action="store_true", help="Print new version without writing.")
    args = parser.parse_args()

    skill_dir: Path = args.skill_dir.resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"ERROR: SKILL.md not found at {skill_md}", file=sys.stderr)
        return 1

    text = skill_md.read_text()
    try:
        fm, body = parse_frontmatter(text)
    except ValueError as e:
        print(f"ERROR: frontmatter parse error: {e}", file=sys.stderr)
        return 1

    current = fm.get("version")
    if not current or not isinstance(current, str):
        print("ERROR: version field missing or not a string", file=sys.stderr)
        return 1

    try:
        new_version = bump_version(current, args.type)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    cmp = compare_versions(new_version, current)
    if cmp <= 0:
        print(f"ERROR: new version {new_version} is not greater than current {current}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"{current} → {new_version} (dry run)")
        return 0

    lines = text.splitlines()
    replaced = False
    for i, line in enumerate(lines):
        if line.strip().startswith("version:"):
            prefix = line[:line.index("version:")]
            lines[i] = f'{prefix}version: {new_version}'
            replaced = True
            break

    if not replaced:
        print("ERROR: could not find 'version:' line in frontmatter", file=sys.stderr)
        return 1

    skill_md.write_text("\n".join(lines) + "\n")
    print(f"{current} → {new_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
