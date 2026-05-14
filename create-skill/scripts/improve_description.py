#!/usr/bin/env python3
"""
improve_description.py - Generate description variants for A/B testing.

Reads the current SKILL.md, extracts the description, and emits 5 candidate
variants for the calling agent to A/B test against evals/evals.json using the
same procedure as scripts/run_eval.py.

This script does NOT call any LLM. It produces *prompt templates* the calling
agent (Claude Code or OpenCode) feeds to itself, plus structural variants
generated locally.

Usage:
    python improve_description.py <skill-dir>
    python improve_description.py <skill-dir> --emit-prompts > prompts.txt
    python improve_description.py <skill-dir> --apply <candidate-file>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def read_skill_md(skill_dir: Path) -> tuple[str, dict, str]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"ERROR: {skill_md} not found", file=sys.stderr)
        sys.exit(1)
    text = skill_md.read_text()
    if not text.startswith("---\n"):
        print(f"ERROR: {skill_md} has no frontmatter", file=sys.stderr)
        sys.exit(1)
    end = text.find("\n---\n", 4)
    if end == -1:
        print(f"ERROR: {skill_md} frontmatter not closed", file=sys.stderr)
        sys.exit(1)
    fm_text = text[4:end]
    body = text[end:]

    m = re.search(r"^description:\s*(>|\|)?\s*$\n((?:  .+\n)+)", fm_text, re.MULTILINE)
    if m:
        kind = m.group(1) or ""
        indented = m.group(2)
        if kind == "|":
            desc = "\n".join(line[2:] for line in indented.splitlines())
        else:
            desc = " ".join(line[2:].strip() for line in indented.splitlines())
    else:
        m = re.search(r"^description:\s*(.+)$", fm_text, re.MULTILINE)
        if not m:
            print("ERROR: could not find description: field", file=sys.stderr)
            sys.exit(1)
        desc = m.group(1).strip()

    return text, {"description": desc}, body


def variant_more_pushy(desc: str) -> str:
    if not desc.lower().startswith("use this skill"):
        return f"Use this skill whenever {desc[0].lower()}{desc[1:]}"
    return desc


def variant_add_negative(desc: str) -> str:
    if "do not use" in desc.lower() or "do not invoke" in desc.lower():
        return desc
    return desc.rstrip(". ") + (
        ". Do NOT use for unrelated tasks or for edits to files outside the "
        "skill's stated scope."
    )


def variant_trigger_list(desc: str) -> str:
    if "triggers include" in desc.lower():
        return desc
    triggers = re.findall(r'"([^"]+)"', desc)
    if not triggers:
        return desc + (
            ' Triggers include any direct mention of the skill\'s topic, '
            'requests to perform its core action, or references to its '
            'primary artifact.'
        )
    return desc + " Triggers include: " + ", ".join(f'"{t}"' for t in triggers) + "."


def variant_shorter(desc: str) -> str:
    sentences = re.split(r"(?<=\.)\s+", desc)
    if len(sentences) <= 2:
        return desc
    return " ".join(sentences[:2])


def variant_imperative(desc: str) -> str:
    return re.sub(
        r"\b(may|might|could|sometimes|perhaps|often|usually|typically)\s+",
        "",
        desc,
    )


def make_variants(desc: str) -> list[dict]:
    variants = [
        {"label": "v0-original", "description": desc},
        {"label": "v1-more-pushy", "description": variant_more_pushy(desc)},
        {"label": "v2-negative-clause", "description": variant_add_negative(desc)},
        {"label": "v3-trigger-list", "description": variant_trigger_list(desc)},
        {"label": "v4-shorter", "description": variant_shorter(desc)},
        {"label": "v5-imperative", "description": variant_imperative(desc)},
    ]
    seen = set()
    unique = []
    for v in variants:
        if v["description"] in seen:
            continue
        seen.add(v["description"])
        unique.append(v)
    return unique


def emit_prompts(skill_dir: Path, variants: list[dict]) -> str:
    evals_file = skill_dir / "evals" / "evals.json"
    if not evals_file.exists():
        print(f"WARNING: {evals_file} not present", file=sys.stderr)
        cases = []
    else:
        cases = json.loads(evals_file.read_text()).get("cases", [])

    out = []
    out.append("# Description A/B Eval Prompts")
    out.append("")
    out.append(f"# Skill: {skill_dir.name}")
    out.append(f"# Variants: {len(variants)}")
    out.append(f"# Cases:    {len(cases)}")
    out.append("")
    out.append("# For each (variant, case) pair, the calling agent should:")
    out.append("#   1. Replace the SKILL.md description with the variant.")
    out.append("#   2. Spawn a subagent with the case prompt.")
    out.append("#   3. Record whether the subagent loaded the skill.")
    out.append("#   4. Restore the original description before the next variant.")
    out.append("")

    for v in variants:
        out.append("=" * 72)
        out.append(f"VARIANT: {v['label']}")
        out.append("-" * 72)
        out.append(v["description"])
        out.append("=" * 72)
        out.append("")

    out.append("# Cases (run each variant against ALL of these):")
    for c in cases:
        out.append(f"## {c.get('id', '?')} [{c.get('kind', '?')}]: {c.get('prompt', '')}")
        out.append(f"   expected_trigger = {c.get('should_trigger')}")
        out.append("")

    return "\n".join(out)


def apply_candidate(skill_dir: Path, candidate_text: str) -> None:
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text()
    if not text.startswith("---\n"):
        print("ERROR: SKILL.md has no frontmatter", file=sys.stderr)
        sys.exit(1)
    end = text.find("\n---\n", 4)
    fm = text[4:end]
    body = text[end:]

    pattern = re.compile(r"^description:.*?(?=\n[a-z_]+:\s|\Z)", re.MULTILINE | re.DOTALL)
    folded = "description: >\n" + "\n".join("  " + line for line in candidate_text.strip().splitlines())
    new_fm = pattern.sub(folded.rstrip() + "\n", fm, count=1)
    skill_md.write_text("---\n" + new_fm + body)
    print(f"Updated description in {skill_md}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", help="Path to the skill directory.")
    parser.add_argument("--emit-prompts", action="store_true",
                        help="Print A/B test prompts to stdout.")
    parser.add_argument("--apply", metavar="FILE",
                        help="Replace the description with the text in FILE.")
    parser.add_argument("--list-variants", action="store_true",
                        help="Print only the variant table (default if no other action).")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    if not skill_dir.is_dir():
        print(f"ERROR: {skill_dir} is not a directory", file=sys.stderr)
        return 1

    if args.apply:
        cand = Path(args.apply).read_text()
        apply_candidate(skill_dir, cand)
        return 0

    _, fm, _ = read_skill_md(skill_dir)
    variants = make_variants(fm["description"])

    if args.emit_prompts:
        print(emit_prompts(skill_dir, variants))
        return 0

    print(f"{len(variants)} candidate descriptions for {skill_dir.name}:")
    print()
    for v in variants:
        print(f"--- {v['label']} ({len(v['description'])} chars) ---")
        print(v["description"])
        print()
    print("Next: write each variant to a file, run the eval loop, then:")
    print(f"  python {Path(__file__).name} {skill_dir} --apply best.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
