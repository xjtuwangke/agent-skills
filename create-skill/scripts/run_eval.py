#!/usr/bin/env python3
"""
run_eval.py - Aggregate skill evaluation results.

Reads every `results-*.json` file under <skill-dir>/evals/ and prints a
report with positive_recall, negative_precision, and per-case detail.

Usage:
    python run_eval.py <skill-dir>
    python run_eval.py <skill-dir> --latest
    python run_eval.py <skill-dir> --split

The actual run is driven by the calling agent (Claude Code or OpenCode), which
spawns subagents per case and writes result files. This script only aggregates.

Result file schema is in create-skill/references/eval-methodology.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CaseResult:
    case_id: str
    kind: str
    with_skill_triggered: bool
    baseline_triggered: bool
    latency_delta_ms: float | None
    tokens_in_delta: int | None
    tokens_out_delta: int | None


def load_evals(skill_dir: Path) -> dict:
    evals_file = skill_dir / "evals" / "evals.json"
    if not evals_file.exists():
        print(f"ERROR: {evals_file} not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(evals_file.read_text())


def discover_results(skill_dir: Path, latest_only: bool) -> list[Path]:
    evals_dir = skill_dir / "evals"
    files = sorted(evals_dir.glob("results-*.json"))
    if not files:
        return []
    if latest_only:
        return [files[-1]]
    return files


def split_cases(cases: list[dict], split_ratio: float = 0.7) -> tuple[set[str], set[str]]:
    train, test = set(), set()
    for c in cases:
        cid = c.get("id", "")
        h = int(hashlib.sha1(cid.encode()).hexdigest(), 16)
        if (h % 100) / 100.0 < split_ratio:
            train.add(cid)
        else:
            test.add(cid)
    return train, test


def parse_result_file(path: Path) -> list[CaseResult]:
    data = json.loads(path.read_text())
    out: list[CaseResult] = []
    for run in data.get("runs", []):
        ws = run.get("with_skill", {}) or {}
        bs = run.get("baseline", {}) or {}

        def diff(a: dict, b: dict, key: str):
            av, bv = a.get(key), b.get(key)
            if av is None or bv is None:
                return None
            return av - bv

        out.append(CaseResult(
            case_id=run.get("case_id", "?"),
            kind=run.get("kind", "?"),
            with_skill_triggered=bool(ws.get("triggered", False)),
            baseline_triggered=bool(bs.get("triggered", False)),
            latency_delta_ms=diff(ws, bs, "latency_ms"),
            tokens_in_delta=diff(ws, bs, "tokens_in"),
            tokens_out_delta=diff(ws, bs, "tokens_out"),
        ))
    return out


def compute_metrics(results: list[CaseResult], evals: dict, subset: set[str] | None = None) -> dict:
    cases_by_id = {c["id"]: c for c in evals.get("cases", [])}

    pos_total = 0
    pos_triggered = 0
    neg_total = 0
    neg_not_triggered = 0
    latency_deltas: list[float] = []
    tokens_in_deltas: list[int] = []
    tokens_out_deltas: list[int] = []

    for r in results:
        if subset is not None and r.case_id not in subset:
            continue
        case = cases_by_id.get(r.case_id, {})
        kind = case.get("kind", r.kind)
        if kind == "positive":
            pos_total += 1
            if r.with_skill_triggered:
                pos_triggered += 1
        elif kind == "negative":
            neg_total += 1
            if not r.with_skill_triggered:
                neg_not_triggered += 1
        if r.latency_delta_ms is not None:
            latency_deltas.append(r.latency_delta_ms)
        if r.tokens_in_delta is not None:
            tokens_in_deltas.append(r.tokens_in_delta)
        if r.tokens_out_delta is not None:
            tokens_out_deltas.append(r.tokens_out_delta)

    def safe_div(n, d):
        return (n / d) if d else None

    def mean(xs):
        return sum(xs) / len(xs) if xs else None

    return {
        "positive_recall": safe_div(pos_triggered, pos_total),
        "negative_precision": safe_div(neg_not_triggered, neg_total),
        "n_positive": pos_total,
        "n_negative": neg_total,
        "mean_latency_delta_ms": mean(latency_deltas),
        "mean_tokens_in_delta": mean(tokens_in_deltas),
        "mean_tokens_out_delta": mean(tokens_out_deltas),
    }


def fmt(metric: float | None, suffix: str = "") -> str:
    if metric is None:
        return "n/a"
    if isinstance(metric, float):
        if suffix == "%":
            return f"{metric:.2%}"
        return f"{metric:.2f}{suffix}"
    return f"{metric}{suffix}"


def render_report(skill_dir: Path, evals: dict, result_file: Path,
                  results: list[CaseResult], split: bool) -> None:
    print(f"Skill:    {evals.get('skill_name', skill_dir.name)}")
    print(f"Version:  {evals.get('skill_version', '?')}")
    print(f"Source:   {result_file}")
    print()

    thresholds = evals.get("thresholds", {})
    pos_min = thresholds.get("positive_recall_min", 0.80)
    neg_min = thresholds.get("negative_precision_min", 0.80)

    if split:
        train, test = split_cases(evals.get("cases", []))
        print(f"Train set ({len(train)} cases):")
        m_train = compute_metrics(results, evals, train)
        print_metric_block(m_train, pos_min, neg_min, indent="  ")
        print()
        print(f"Test set ({len(test)} cases):")
        m_test = compute_metrics(results, evals, test)
        print_metric_block(m_test, pos_min, neg_min, indent="  ")
        print()
        gap = (m_train["positive_recall"] or 0) - (m_test["positive_recall"] or 0)
        if gap > 0.20:
            print("  ! Train-test recall gap > 0.20 (likely over-fit to train wording)")
    else:
        m = compute_metrics(results, evals)
        print_metric_block(m, pos_min, neg_min)
        print()

    print("Per-case detail:")
    cases_by_id = {c["id"]: c for c in evals.get("cases", [])}
    for r in results:
        case = cases_by_id.get(r.case_id, {})
        kind = case.get("kind", r.kind)
        expected = case.get("should_trigger")
        actual = r.with_skill_triggered
        ok = (expected is None) or (expected == actual)
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {r.case_id:<12} kind={kind:<8} "
              f"expected={expected}  actual={actual}")


def print_metric_block(m: dict, pos_min: float, neg_min: float, indent: str = "") -> None:
    pr = m["positive_recall"]
    np_ = m["negative_precision"]
    pr_ok = pr is not None and pr >= pos_min
    np_ok = np_ is not None and np_ >= neg_min
    print(f"{indent}positive_recall      = {fmt(pr, '%')}   ({'PASS' if pr_ok else 'FAIL'}, target >= {pos_min:.0%})")
    print(f"{indent}negative_precision   = {fmt(np_, '%')}   ({'PASS' if np_ok else 'FAIL'}, target >= {neg_min:.0%})")
    print(f"{indent}n_positive           = {m['n_positive']}")
    print(f"{indent}n_negative           = {m['n_negative']}")
    if m["mean_latency_delta_ms"] is not None:
        print(f"{indent}mean_latency_delta   = {m['mean_latency_delta_ms']:+.0f} ms (with-skill - baseline)")
    if m["mean_tokens_in_delta"] is not None:
        print(f"{indent}mean_tokens_in_delta = {m['mean_tokens_in_delta']:+.0f}")
    if m["mean_tokens_out_delta"] is not None:
        print(f"{indent}mean_tokens_out_delta= {m['mean_tokens_out_delta']:+.0f}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", help="Path to the skill directory.")
    parser.add_argument("--latest", action="store_true",
                        help="Only aggregate the most recent results-*.json.")
    parser.add_argument("--split", action="store_true",
                        help="Report train/test split (70/30, deterministic by case_id hash).")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    if not skill_dir.is_dir():
        print(f"ERROR: {skill_dir} is not a directory", file=sys.stderr)
        return 1

    evals = load_evals(skill_dir)
    result_files = discover_results(skill_dir, latest_only=args.latest)
    if not result_files:
        print(f"ERROR: no results-*.json under {skill_dir / 'evals'}", file=sys.stderr)
        print("Run the eval loop first (see SKILL.md stage 5).", file=sys.stderr)
        return 1

    all_results: list[CaseResult] = []
    for f in result_files:
        all_results.extend(parse_result_file(f))

    render_report(skill_dir, evals, result_files[-1], all_results, split=args.split)
    return 0


if __name__ == "__main__":
    sys.exit(main())
