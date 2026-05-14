# Evaluation Methodology

Skills do not pass validation simply by parsing correctly. They have to *fire
at the right time*. This document describes how to measure that.

---

## What We Measure

Two metrics, both bounded in `[0, 1]`:

| Metric | Definition | Target |
|---|---|---|
| **Positive recall** | Fraction of `kind: positive` cases where the agent loads the skill. | `>= 0.80` |
| **Negative precision** | Fraction of `kind: negative` cases where the agent does NOT load the skill. | `>= 0.80` |

A skill that scores high on one but low on the other is broken:

- High recall + low precision: over-triggers, will fire on unrelated tasks.
- Low recall + high precision: under-triggers, the user has to invoke it
  manually every time.

Both targets are deliberately set at `0.80`, not `1.00`. A skill that fires
correctly on 4 out of 5 ambiguous prompts is doing its job. Chasing 100%
typically requires making the description so narrow that real users miss it.

---

## Test Case Schema

Each entry in `evals/evals.json` has this shape:

```json
{
  "id": "pos-001",
  "kind": "positive | negative | edge",
  "prompt": "User input as it would appear in a chat.",
  "should_trigger": true,
  "assertions": ["Free-form check the grader applies."],
  "notes": "Optional context for the grader or human reviewer."
}
```

`should_trigger` is the ground truth:

- `true` for positives.
- `false` for negatives.
- `null` for edge cases (either behavior defensible; not counted in recall or
  precision).

---

## The Eval Loop (Agent-Driven)

The eval is driven by whichever agent is currently running this skill (Claude
Code or OpenCode). Python scripts only aggregate the results.

Procedure:

1. Read `evals/evals.json`.
2. For each case, spawn two parallel subagents:
   - `with-skill`: receives the prompt with `<name>/SKILL.md` available.
   - `baseline`: receives the prompt with NO custom skill loaded.
3. For each subagent, record:
   - `triggered`: did it load the skill? (`true` only meaningful for
     `with-skill`)
   - `output`: the response text
   - `tokens_in`, `tokens_out`, `latency_ms` (if the host exposes them)
4. Write a result file:
   ```
   <skill-dir>/evals/results-YYYYMMDD-HHMMSS.json
   ```
5. Run `python scripts/run_eval.py <skill-dir>` to compute the metrics.

---

## Result File Schema

```json
{
  "skill_name": "rate-limiter",
  "skill_version": "0.2.0",
  "timestamp": "2026-05-14T10:32:01Z",
  "host": "opencode",
  "runs": [
    {
      "case_id": "pos-001",
      "kind": "positive",
      "with_skill": {
        "triggered": true,
        "tokens_in": 1230,
        "tokens_out": 412,
        "latency_ms": 4521,
        "output": "..."
      },
      "baseline": {
        "triggered": false,
        "tokens_in": 1180,
        "tokens_out": 387,
        "latency_ms": 4123,
        "output": "..."
      }
    }
  ]
}
```

`run_eval.py` reads any results file matching `results-*.json` and computes:

- positive_recall = triggered_positives / total_positives
- negative_precision = (1 - triggered_negatives / total_negatives)
- mean_latency_delta_ms
- mean_tokens_delta_in
- mean_tokens_delta_out

---

## Train / Test Split (for Description Optimization)

When using `improve_description.py` to A/B test description variants, split the
cases:

- 70% **train** - used to score and pick the candidate.
- 30% **test** - used for the final reported score.

This prevents the description from over-fitting to the exact wording of the
train cases. If train_recall is 1.00 but test_recall is 0.40, the description
has memorized the train prompts and will fail on real users.

`run_eval.py --split` performs the split deterministically by hashing
`case_id`, so the same split is used across rounds.

---

## When to Stop Iterating

- 3 rounds of `improve_description.py` did not move the metrics by `>=0.05`.
- Both `positive_recall` and `negative_precision` are `>=0.80`.
- The skill has been re-tested on a held-out set the description has never
  seen.

If iteration plateaus below target, the problem is the **charter** (Stage 1),
not the description. Return to the user with this finding rather than continue
spinning.

---

## Common Result Patterns

| Pattern | Diagnosis | Fix |
|---|---|---|
| Recall < 0.50 across all positives | Description is too vague or missing trigger phrases | Add explicit "Triggers include" phrases |
| Recall high, precision < 0.50 | Description matches too many prompts (e.g. matches every markdown edit) | Add "Do NOT use for ..." clause; narrow trigger phrases |
| Train high, test low (>0.20 gap) | Over-fit on train wording | Generate more candidate descriptions, re-run held-out |
| Latency delta > 2x baseline | Skill is doing too much in-context work | Split body into references/ (loaded on demand) |
| Token-out delta negative (skill *reduces* output) | Skill is correctly cutting off rambling | Good - keep |

---

## Cost Awareness

Each eval round costs roughly:

```
N_cases * 2 subagents * mean_response_tokens
```

For a skill with 10 cases at ~500 tokens per response: about 10000 tokens per
round, 30000 tokens for 3 rounds of description optimization. Budget
accordingly; for cheap drafts, drop edge cases and reduce to 5 cases.

---

## Minimum Bar Before Install

`install_to_platform.py` refuses to install unless:

- `evals/evals.json` exists with `>=3 positive` and `>=2 negative` cases.
- At least one `results-*.json` file exists in `evals/`.
- The most recent result file shows `positive_recall >= 0.80` AND
  `negative_precision >= 0.80`.

Override with `--skip-eval` (printed warning, audited) for trivial knowledge
skills that don't need triggering metrics.
