#!/usr/bin/env python3
"""
install_to_platform.py - Install a skill into one or more agent platforms.

Default behavior is symlink (-s). On --target claude-strict, the SKILL.md is
COPIED with frontmatter rewritten so version / author / tags / requires /
related are nested under `metadata` (Anthropic's quick_validate.py rejects
those top-level keys).

Usage:
    python install_to_platform.py <skill-dir> --target opencode
    python install_to_platform.py <skill-dir> --target claude-strict
    python install_to_platform.py <skill-dir> --target opencode --target claude-strict
    python install_to_platform.py <skill-dir> --target opencode --copy
    python install_to_platform.py <skill-dir> --target opencode --uninstall

Targets:
    opencode         -> ~/.config/opencode/skills/<name>/
    opencode-project -> ./.opencode/skills/<name>/   (current working directory)
    claude           -> ~/.claude/skills/<name>/      (literal copy)
    claude-strict    -> ~/.claude/skills/<name>/      (frontmatter rewritten)
    claude-project   -> ./.claude/skills/<name>/      (literal copy)
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path


TARGETS = {
    "opencode":         lambda name: Path.home() / ".config" / "opencode" / "skills" / name,
    "opencode-project": lambda name: Path.cwd() / ".opencode" / "skills" / name,
    "claude":           lambda name: Path.home() / ".claude" / "skills" / name,
    "claude-strict":    lambda name: Path.home() / ".claude" / "skills" / name,
    "claude-project":   lambda name: Path.cwd() / ".claude" / "skills" / name,
}

STRICT_TARGETS = {"claude-strict"}

TOP_LEVEL_KEYS_TO_NEST = ("version", "author", "tags", "requires", "related")


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg: str) -> None:
    print(f"  {msg}")


def read_skill_md(skill_dir: Path) -> tuple[str, str]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        die(f"SKILL.md not found at {skill_md}")
    text = skill_md.read_text()
    if not text.startswith("---\n"):
        die("SKILL.md has no frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        die("SKILL.md frontmatter is not closed")
    return text[4:end], text[end + len("\n---\n"):]


def rewrite_strict(fm_text: str) -> str:
    lines = fm_text.splitlines()
    extracted: dict[str, list[str]] = {}
    keep: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        match = re.match(r"^([a-z_-]+):\s*(.*)$", stripped)
        is_top_level = match and (len(line) - len(stripped) == 0)
        if is_top_level and match.group(1) in TOP_LEVEL_KEYS_TO_NEST:
            key = match.group(1)
            block = [line]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() == "" or nxt.startswith(" ") or nxt.startswith("\t"):
                    block.append(nxt)
                    i += 1
                else:
                    break
            extracted[key] = block
            continue
        keep.append(line)
        i += 1

    out = "\n".join(keep)
    if "metadata:" in out:
        new_lines = []
        injected = False
        for line in out.splitlines():
            new_lines.append(line)
            if not injected and line.startswith("metadata:"):
                for k in TOP_LEVEL_KEYS_TO_NEST:
                    block = extracted.get(k)
                    if not block:
                        continue
                    for b in block:
                        new_lines.append("  " + b if b.strip() else b)
                injected = True
        out = "\n".join(new_lines)
    else:
        out = out.rstrip() + "\nmetadata:\n"
        for k in TOP_LEVEL_KEYS_TO_NEST:
            block = extracted.get(k)
            if not block:
                continue
            for b in block:
                out += ("  " + b if b.strip() else b) + "\n"

    return out


def install_symlink(skill_dir: Path, dest: Path, force: bool) -> None:
    if dest.exists() or dest.is_symlink():
        if not force:
            die(f"destination exists: {dest}. Use --force to overwrite.")
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(skill_dir, dest, target_is_directory=True)
    info(f"symlink {dest} -> {skill_dir}")


def install_copy(skill_dir: Path, dest: Path, force: bool, strict: bool) -> None:
    if dest.exists():
        if not force:
            die(f"destination exists: {dest}. Use --force to overwrite.")
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(skill_dir, dest, symlinks=False)

    if strict:
        skill_md = dest / "SKILL.md"
        fm_text, body = read_skill_md(skill_dir)
        new_fm = rewrite_strict(fm_text)
        skill_md.write_text("---\n" + new_fm.rstrip() + "\n---\n" + body)
        info(f"strict copy + frontmatter rewrite -> {dest}")
    else:
        info(f"copy {skill_dir} -> {dest}")


def check_eval_gate(skill_dir: Path) -> None:
    evals_file = skill_dir / "evals" / "evals.json"
    if not evals_file.exists():
        die(
            f"missing {evals_file}. "
            "Every skill must ship evals before install. "
            "Use --skip-eval to override (audited)."
        )
    results = list((skill_dir / "evals").glob("results-*.json"))
    if not results:
        die(
            f"no results-*.json under {skill_dir / 'evals'}. "
            "Run the eval loop first (see SKILL.md stage 5). "
            "Use --skip-eval to override (audited)."
        )


def uninstall(name: str, target: str, force: bool) -> None:
    dest = TARGETS[target](name)
    if not (dest.exists() or dest.is_symlink()):
        info(f"nothing to uninstall at {dest}")
        return
    if not force:
        die(f"refusing to uninstall {dest} without --force")
    if dest.is_symlink() or dest.is_file():
        dest.unlink()
    else:
        shutil.rmtree(dest)
    info(f"removed {dest}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("skill_dir", help="Path to the skill directory.")
    parser.add_argument("--target", action="append", required=True,
                        choices=sorted(TARGETS.keys()),
                        help="Install target. Repeat for multiple.")
    parser.add_argument("--copy", action="store_true",
                        help="Copy instead of symlink (default is symlink).")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing target.")
    parser.add_argument("--skip-eval", action="store_true",
                        help="Skip the eval gate. AUDITED.")
    parser.add_argument("--uninstall", action="store_true",
                        help="Remove the skill from the target(s) instead of installing.")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    if not skill_dir.is_dir():
        die(f"{skill_dir} is not a directory")

    name = skill_dir.name

    if args.uninstall:
        for t in args.target:
            uninstall(name, t, args.force)
        return 0

    if not args.skip_eval:
        check_eval_gate(skill_dir)
    else:
        print("WARN: --skip-eval - bypassing eval gate (this is audited).",
              file=sys.stderr)

    for t in args.target:
        dest = TARGETS[t](name)
        strict = t in STRICT_TARGETS
        if strict or args.copy:
            install_copy(skill_dir, dest, force=args.force, strict=strict)
        else:
            install_symlink(skill_dir, dest, force=args.force)

    print()
    print(f"Done. Installed {name} to {len(args.target)} target(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
