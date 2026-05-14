#!/usr/bin/env python3
"""
init_skill.py - Scaffold a new skill from templates.

Usage:
    python init_skill.py <skill-name> [options]
    python init_skill.py --interactive
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ROLE_TAGS = {"DEV", "QA", "BA", "DEVOPS"}
DOMAIN_TAGS = {
    "api", "database", "backend", "infra",
    "auth", "cli", "data", "ml", "meta",
}

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
TEMPLATES_DIR = SKILL_ROOT / "templates"
DEFAULT_OUTPUT_DIR = SKILL_ROOT.parent


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def info(msg: str) -> None:
    print(f"  {msg}")


def validate_name(name: str) -> str:
    if not NAME_RE.match(name):
        die(
            f"invalid skill name: {name!r}. "
            "Must match ^[a-z0-9]+(-[a-z0-9]+)*$ (kebab-case)."
        )
    if len(name) > 64:
        die(f"skill name too long ({len(name)} chars, max 64)")
    return name


def validate_role(role: str) -> str:
    if role not in ROLE_TAGS:
        die(f"invalid role tag {role!r}. Allowed: {sorted(ROLE_TAGS)}")
    return role


def validate_domain(domain: str) -> str:
    if domain not in DOMAIN_TAGS:
        die(f"invalid domain tag {domain!r}. Allowed: {sorted(DOMAIN_TAGS)}")
    return domain


def to_title(name: str) -> str:
    return " ".join(part.capitalize() for part in name.split("-"))


def render(template: str, values: dict[str, str]) -> str:
    out = template
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", val)
    return out


def prompt(question: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        answer = input(f"{question}{suffix}: ").strip()
        if answer:
            return answer
        if default is not None:
            return default
        print("  (required, please answer)")


def interactive_inputs() -> dict[str, str]:
    print("Interactive skill scaffolding. Press Ctrl-C to cancel.\n")
    name = validate_name(prompt("Skill name (kebab-case)"))
    title = to_title(name)
    action = prompt(
        "Action phrase (fills 'Use this skill whenever the user wants to ___')"
    )
    trigger_1 = prompt("Trigger phrase 1 (literal user wording)")
    trigger_2 = prompt("Trigger phrase 2")
    trigger_3 = prompt("Trigger phrase 3")
    outcome = prompt("Outcome phrase (fills 'or requests to ___')")
    secondary = prompt(
        "Secondary use case (fills 'Also use when ___')",
        default="the user references a similar artifact",
    )
    anti_1 = prompt("Anti-trigger 1 (when this skill should NOT fire)")
    anti_2 = prompt("Anti-trigger 2", default="unrelated tasks")

    author = prompt("Author", default=os.environ.get("USER", "unknown"))
    version = prompt("Initial version", default="0.1.0")
    license_name = prompt("License", default="MIT")
    role = validate_role(prompt(f"Role tag {sorted(ROLE_TAGS)}", default="DEV"))
    domain = validate_domain(
        prompt(f"Domain tag {sorted(DOMAIN_TAGS)}", default="backend")
    )

    pos_1 = prompt("Positive eval prompt 1 (a realistic prompt that should trigger)")
    pos_2 = prompt("Positive eval prompt 2")
    pos_3 = prompt("Positive eval prompt 3")
    neg_1 = prompt("Negative eval prompt 1 (looks similar but should NOT trigger)")
    neg_2 = prompt("Negative eval prompt 2")
    edge_1 = prompt(
        "Edge case prompt (ambiguous, either behavior defensible)",
        default="<replace with an ambiguous edge case>",
    )

    return {
        "NAME": name,
        "TITLE": title,
        "ACTION_PHRASE": action,
        "TRIGGER_1": trigger_1,
        "TRIGGER_2": trigger_2,
        "TRIGGER_3": trigger_3,
        "OUTCOME": outcome,
        "SECONDARY_USE_CASE": secondary,
        "ANTI_TRIGGER_1": anti_1,
        "ANTI_TRIGGER_2": anti_2,
        "AUTHOR": author,
        "VERSION": version,
        "LICENSE": license_name,
        "ROLE_TAG": role,
        "DOMAIN_TAG": domain,
        "POSITIVE_PROMPT_1": pos_1,
        "POSITIVE_PROMPT_2": pos_2,
        "POSITIVE_PROMPT_3": pos_3,
        "NEGATIVE_PROMPT_1": neg_1,
        "NEGATIVE_PROMPT_2": neg_2,
        "EDGE_PROMPT_1": edge_1,
        "REQUIREMENT_1": "<fill in>",
        "ANTI_REQUIREMENT_1": "<fill in>",
        "RECOMMENDATION_1": "<fill in>",
        "CHECK_1": "<fill in>",
        "CHECK_2": "<fill in>",
        "CHECK_3": "<fill in>",
        "PITFALL_NAME_1": "<fill in>",
        "DESCRIPTION_1": "<fill in>",
        "FIX_1": "<fill in>",
        "PITFALL_NAME_2": "<fill in>",
        "DESCRIPTION_2": "<fill in>",
        "FIX_2": "<fill in>",
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Scaffold a new skill from templates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("name", nargs="?", help="Skill name (kebab-case). Required unless --interactive.")
    p.add_argument("--description", help="Full description for the SKILL.md frontmatter.")
    p.add_argument("--action", help="Verb phrase: fills 'Use this skill whenever the user wants to ___'.")
    p.add_argument("--trigger", action="append", default=[], help="Trigger phrase. Repeat for multiple.")
    p.add_argument("--anti-trigger", action="append", default=[], help="Anti-trigger. Repeat for multiple.")
    p.add_argument("--outcome", default="package this workflow", help="Fills 'or requests to ___'.")
    p.add_argument("--secondary", default="the user references a similar artifact",
                   help="Fills 'Also use when ___'.")
    p.add_argument("--author", default=os.environ.get("USER", "unknown"))
    p.add_argument("--version", default="0.1.0")
    p.add_argument("--license", default="MIT")
    p.add_argument("--role", default="DEV", help=f"Role tag, one of {sorted(ROLE_TAGS)}.")
    p.add_argument("--domain", default="backend", help=f"Domain tag, one of {sorted(DOMAIN_TAGS)}.")
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR),
                   help="Where to create the skill directory.")
    p.add_argument("--interactive", "-i", action="store_true", help="Interactive prompting mode.")
    p.add_argument("--force", action="store_true", help="Overwrite existing skill directory.")
    return p


def values_from_args(args: argparse.Namespace) -> dict[str, str]:
    if not args.name:
        die("skill name is required (or use --interactive)")
    name = validate_name(args.name)
    role = validate_role(args.role)
    domain = validate_domain(args.domain)
    triggers = args.trigger + [""] * max(0, 3 - len(args.trigger))
    antis = args.anti_trigger + ["unrelated tasks"] * max(0, 2 - len(args.anti_trigger))

    action = args.action or f"work with {name}"

    return {
        "NAME": name,
        "TITLE": to_title(name),
        "ACTION_PHRASE": action,
        "TRIGGER_1": triggers[0] or f"{name}",
        "TRIGGER_2": triggers[1] or f"use {name}",
        "TRIGGER_3": triggers[2] or f"run {name}",
        "OUTCOME": args.outcome,
        "SECONDARY_USE_CASE": args.secondary,
        "ANTI_TRIGGER_1": antis[0],
        "ANTI_TRIGGER_2": antis[1],
        "AUTHOR": args.author,
        "VERSION": args.version,
        "LICENSE": args.license,
        "ROLE_TAG": role,
        "DOMAIN_TAG": domain,
        "POSITIVE_PROMPT_1": "<replace with a realistic positive prompt>",
        "POSITIVE_PROMPT_2": "<replace with a realistic positive prompt>",
        "POSITIVE_PROMPT_3": "<replace with a realistic positive prompt>",
        "NEGATIVE_PROMPT_1": "<replace with a realistic negative prompt>",
        "NEGATIVE_PROMPT_2": "<replace with a realistic negative prompt>",
        "EDGE_PROMPT_1": "<replace with an ambiguous edge case>",
        "REQUIREMENT_1": "<fill in>",
        "ANTI_REQUIREMENT_1": "<fill in>",
        "RECOMMENDATION_1": "<fill in>",
        "CHECK_1": "<fill in>",
        "CHECK_2": "<fill in>",
        "CHECK_3": "<fill in>",
        "PITFALL_NAME_1": "<fill in>",
        "DESCRIPTION_1": "<fill in>",
        "FIX_1": "<fill in>",
        "PITFALL_NAME_2": "<fill in>",
        "DESCRIPTION_2": "<fill in>",
        "FIX_2": "<fill in>",
    }


def scaffold(values: dict[str, str], output_dir: Path, force: bool) -> Path:
    skill_dir = output_dir / values["NAME"]
    if skill_dir.exists():
        if not force:
            die(f"directory exists: {skill_dir}. Use --force to overwrite.")
        info(f"overwriting existing directory: {skill_dir}")

    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "assets").mkdir(exist_ok=True)
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir(exist_ok=True)

    skill_template = (TEMPLATES_DIR / "SKILL.md.tmpl").read_text()
    (skill_dir / "SKILL.md").write_text(render(skill_template, values))
    info(f"wrote {skill_dir / 'SKILL.md'}")

    evals_template = (TEMPLATES_DIR / "evals.json.tmpl").read_text()
    (evals_dir / "evals.json").write_text(render(evals_template, values))
    info(f"wrote {evals_dir / 'evals.json'}")

    for sub in ("references", "scripts", "assets"):
        gitkeep = skill_dir / sub / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")

    return skill_dir


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.interactive:
        values = interactive_inputs()
    else:
        values = values_from_args(args)

    output_dir = Path(args.output_dir).resolve()
    if not output_dir.exists():
        die(f"output directory does not exist: {output_dir}")

    skill_dir = scaffold(values, output_dir, force=args.force)

    print()
    print(f"Skill scaffolded at {skill_dir}")
    print()
    print("Next steps:")
    print(f"  1. Edit  {skill_dir / 'SKILL.md'}  (fill the <fill in> placeholders)")
    print(f"  2. Edit  {skill_dir / 'evals' / 'evals.json'}  (replace prompts)")
    print(f"  3. Run   python {SCRIPT_DIR / 'validate_skill.py'} {skill_dir}")
    print(f"  4. Run   python {SCRIPT_DIR / 'run_eval.py'} {skill_dir}  (after evals filled)")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
