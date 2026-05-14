#!/usr/bin/env python3
"""
validate_skill.py - Validate a skill against the project's frontmatter spec
and structural rules. Exits 0 on pass, 1 on failure.

Usage:
    python validate_skill.py <skill-dir>
    python validate_skill.py <skill-dir-1> <skill-dir-2> ...
    python validate_skill.py --all <repo-root>

Rules are documented in create-skill/references/frontmatter-spec.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[\w.]+)?$")

# Dependency syntax: "<name>" or "<name> <op><semver>[, <op><semver>]*"
# Operators allowed: == != >= <= > < ~= (PEP 440 subset).
DEP_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
DEP_OP_RE = re.compile(r"(==|!=|>=|<=|~=|>|<)\s*(\d+\.\d+\.\d+(-[\w.]+)?)")

ROLE_TAGS = {"DEV", "QA", "BA", "DEVOPS"}
DOMAIN_TAGS = {
    "api", "database", "backend", "infra",
    "auth", "cli", "data", "ml", "meta",
}
LAYER_TAGS = {"workflow", "knowledge", "template", "eval", "automation"}
MATURITY_TAGS = {"experimental", "stable", "deprecated"}

KNOWN_TOOLS = {
    "bash", "read", "write", "edit", "grep", "glob",
    "webfetch", "websearch", "task", "todowrite",
}

REQUIRED_TOP_LEVEL = {
    "name", "description", "version", "author", "license", "tags",
    "requires", "related",
}
REQUIRES_KEYS = {"skills", "mcps", "tools"}
RELATED_KEYS = {"skills", "commands", "mcps"}
SUGGESTS_KEYS = {"tools", "runtimes", "mcps"}

MAX_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 1024
MAX_SKILL_MD_LINES = 500


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("frontmatter must start with '---' on line 1")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("frontmatter must close with '---' on its own line")
    fm_text = text[4:end]
    body = text[end + len("\n---\n"):]

    try:
        import yaml  # type: ignore
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


@dataclass
class Report:
    skill_dir: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors

    def render(self) -> str:
        lines = [f"[{self.skill_dir}]"]
        if self.ok and not self.warnings:
            lines.append("  PASS")
            return "\n".join(lines)
        if self.ok:
            lines.append("  PASS (with warnings)")
        else:
            lines.append("  FAIL")
        for e in self.errors:
            lines.append(f"  ERROR   {e}")
        for w in self.warnings:
            lines.append(f"  WARN    {w}")
        return "\n".join(lines)


def validate_dep_string(s: str) -> tuple[bool, str]:
    s = s.strip()
    if not s:
        return False, "empty dependency string"
    parts = s.split(None, 1)
    name = parts[0]
    if not DEP_NAME_RE.match(name):
        return False, f"invalid dependency name {name!r}"
    if len(parts) == 1:
        return True, ""
    spec = parts[1].strip()
    for piece in spec.split(","):
        piece = piece.strip()
        m = DEP_OP_RE.match(piece)
        if not m or m.end() != len(piece):
            return False, f"invalid version constraint {piece!r}"
    return True, ""


def validate_frontmatter(fm: dict, report: Report) -> None:
    for key in REQUIRED_TOP_LEVEL:
        if key not in fm:
            report.err(f"missing required field: {key}")

    name = fm.get("name")
    if name is not None:
        if not isinstance(name, str):
            report.err(f"name must be a string, got {type(name).__name__}")
        elif not NAME_RE.match(name):
            report.err(f"name {name!r} does not match ^[a-z0-9]+(-[a-z0-9]+)*$")
        elif len(name) > MAX_NAME_LEN:
            report.err(f"name longer than {MAX_NAME_LEN} chars")
        elif report.skill_dir.name != name:
            report.err(
                f"name {name!r} does not match directory name "
                f"{report.skill_dir.name!r}"
            )

    desc = fm.get("description")
    if desc is not None:
        if not isinstance(desc, str):
            report.err("description must be a string")
        else:
            if "<" in desc or ">" in desc:
                report.err("description must not contain '<' or '>'")
            if len(desc) > MAX_DESCRIPTION_LEN:
                report.err(
                    f"description is {len(desc)} chars (max {MAX_DESCRIPTION_LEN})"
                )
            if len(desc) < 30:
                report.warn(
                    "description is very short (<30 chars); will likely under-trigger"
                )
            lower = desc.lower()
            if "use this skill" not in lower and "use when" not in lower and "use whenever" not in lower:
                report.warn(
                    "description does not start with 'Use this skill...' "
                    "(see description-patterns.md)"
                )
            if "do not use" not in lower and "do not invoke" not in lower:
                report.warn(
                    "description has no 'Do NOT use for...' clause "
                    "(see description-patterns.md)"
                )

    ver = fm.get("version")
    if ver is not None:
        if not isinstance(ver, str) or not SEMVER_RE.match(ver):
            report.err(f"version {ver!r} is not SemVer 2.0 (e.g., 1.0.0)")

    author = fm.get("author")
    if author is not None:
        if not isinstance(author, str) or not author.strip():
            report.err("author must be a non-empty string")

    lic = fm.get("license")
    if lic is not None and (not isinstance(lic, str) or not lic.strip()):
        report.err("license must be a non-empty string")

    tags = fm.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            report.err("tags must be a list of strings")
        else:
            roles = [t for t in tags if t in ROLE_TAGS]
            domains = [t for t in tags if t in DOMAIN_TAGS]
            if not roles:
                report.err(
                    f"tags must include >=1 role tag (UPPERCASE). "
                    f"Allowed: {sorted(ROLE_TAGS)}"
                )
            if not domains:
                report.err(
                    f"tags must include >=1 domain tag (lowercase). "
                    f"Allowed: {sorted(DOMAIN_TAGS)}"
                )
            for t in tags:
                if t in ROLE_TAGS:
                    continue
                if t != t.lower():
                    report.warn(f"non-role tag {t!r} should be lowercase")

    req = fm.get("requires")
    if req is not None:
        if not isinstance(req, dict):
            report.err("requires must be a mapping")
        else:
            for k in REQUIRES_KEYS:
                if k not in req:
                    report.err(f"requires.{k} missing (use [] if empty)")
                elif not isinstance(req[k], list):
                    report.err(f"requires.{k} must be a list")
                else:
                    for item in req[k]:
                        if not isinstance(item, str):
                            report.err(f"requires.{k} entries must be strings")
                            continue
                        if k == "tools":
                            tool_name = item.split()[0] if item.split() else item
                            if tool_name not in KNOWN_TOOLS:
                                report.warn(
                                    f"requires.tools entry {item!r} is not a "
                                    f"known built-in tool"
                                )
                        else:
                            ok, msg = validate_dep_string(item)
                            if not ok:
                                report.err(f"requires.{k}: {msg}")
            extra = set(req.keys()) - REQUIRES_KEYS
            if extra:
                report.warn(f"requires has unknown keys: {sorted(extra)}")

    rel = fm.get("related")
    if rel is not None:
        if not isinstance(rel, dict):
            report.err("related must be a mapping")
        else:
            for k in RELATED_KEYS:
                if k not in rel:
                    report.err(f"related.{k} missing (use [] if empty)")
                elif not isinstance(rel[k], list):
                    report.err(f"related.{k} must be a list")
            if "tools" in rel:
                report.err(
                    "related.tools is not allowed - built-in tools are either "
                    "in requires.tools or irrelevant"
                )

    sug = fm.get("suggests")
    if sug is not None:
        if not isinstance(sug, dict):
            report.err("suggests must be a mapping")
        else:
            for k, v in sug.items():
                if k not in SUGGESTS_KEYS:
                    report.warn(f"suggests has unknown key: {k}")
                elif not isinstance(v, list):
                    report.err(f"suggests.{k} must be a list")
                else:
                    for item in v:
                        if not isinstance(item, str):
                            report.err(f"suggests.{k} entries must be strings")


def validate_skill(skill_dir: Path) -> Report:
    report = Report(skill_dir=skill_dir)

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        report.err(f"SKILL.md not found at {skill_md}")
        return report

    text = skill_md.read_text()
    try:
        fm, body = parse_frontmatter(text)
    except ValueError as e:
        report.err(f"frontmatter parse error: {e}")
        return report

    validate_frontmatter(fm, report)

    body_lines = body.splitlines()
    if len(body_lines) > MAX_SKILL_MD_LINES:
        report.err(
            f"SKILL.md body is {len(body_lines)} lines (max {MAX_SKILL_MD_LINES}). "
            "Move detail into references/."
        )

    evals_file = skill_dir / "evals" / "evals.json"
    if not evals_file.exists():
        report.warn("evals/evals.json not present - required before install")
    else:
        try:
            data = json.loads(evals_file.read_text())
            cases = data.get("cases", [])
            pos = [c for c in cases if c.get("kind") == "positive"]
            neg = [c for c in cases if c.get("kind") == "negative"]
            if len(pos) < 3:
                report.warn(f"evals: only {len(pos)} positive cases (recommend >=3)")
            if len(neg) < 2:
                report.warn(f"evals: only {len(neg)} negative cases (recommend >=2)")
        except json.JSONDecodeError as e:
            report.err(f"evals/evals.json is not valid JSON: {e}")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", help="Skill directories to validate.")
    parser.add_argument(
        "--all",
        metavar="ROOT",
        help="Validate every immediate subdirectory of ROOT that contains a SKILL.md.",
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress warnings.")
    args = parser.parse_args()

    targets: list[Path] = []
    if args.all:
        root = Path(args.all).resolve()
        if not root.is_dir():
            print(f"ERROR: --all root is not a directory: {root}", file=sys.stderr)
            return 1
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / "SKILL.md").exists():
                targets.append(child)
    targets.extend(Path(t).resolve() for t in args.targets)

    if not targets:
        parser.print_help(sys.stderr)
        return 1

    failed = 0
    for t in targets:
        report = validate_skill(t)
        if args.quiet:
            report.warnings = []
        print(report.render())
        if not report.ok:
            failed += 1

    print()
    print(f"{len(targets) - failed} passed, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
