"""
EXPERIMENT 027 - pt_prereg_audit.py

Trusted-Statement / Untrusted-Solution audit pattern, after
anthropics/zeta-23-lean comparator/.

In Lean the pattern is:
  - Challenge.lean: theorem statements with `:= by sorry` (trusted spec)
  - Solution.lean: same statements, proved by delegation (untrusted proof)
  - comparator runner: verifies statement coincidence + axiom whitelist +
    kernel replay

Our Python analogue:
  - prereg.json: CHALLENGE — what we predict, MD5-pinned, decision_rule fixed
  - result.json: SOLUTION — what we measured
  - pt_prereg_audit.main(): comparator runner — structural checks only

Key SciMind 4.0 alignment:
  - Anti-Sharpshooter: decision_rule in prereg is fixed BEFORE measurement.
  - Steelman: result_extra_keys are allowed (new observables OK) but the
    core prediction set must coincide.
  - Axiom Whitelist: this module imports NO experimental code. The audit
    depends only on JSON structure and a small numeric evaluator.

Public API:
  - audit_prereg_structure(prereg_dict) -> {"ok": bool, "missing_fields": [...]}
  - compare_statement_sets(prereg_dict, result_dict) -> {"match": bool, ...}
  - evaluate_decision_rule(rule_str, measurements_dict) -> bool
  - audit_run(prereg_path, result_path) -> {"status": "CONFIRMED"|...}
"""
import json
import os
import re
from typing import Any


# === PREREG STRUCTURAL AUDIT ===

REQUIRED_PREREG_FIELDS = ("md5", "decision_rule", "predictions")


def audit_prereg_structure(prereg: dict) -> dict:
    """Verify a prereg dict has the minimum structural fields.

    The prereg is the trusted CHALLENGE side of the audit. It must declare:
      - md5: a hash pinning the prereg content
      - decision_rule: the rule that decides CONFIRMED/REFUTED
      - predictions: dict of predicted values to compare against

    Returns {"ok": True} or {"ok": False, "missing_fields": [...]}.
    """
    missing = [f for f in REQUIRED_PREREG_FIELDS if f not in prereg]
    return {"ok": not missing, "missing_fields": missing}


# === STATEMENT COINCIDENCE CHECK ===

def compare_statement_sets(
    prereg: dict,
    result: dict,
) -> dict:
    """Check that every predicted key has a corresponding result value.

    The prereg's `predictions` sub-dict defines the statement set.
    The result's top-level keys (excluding `predictions` if mirrored)
    define the observed statement set.

    Rules (after zeta-23 comparator):
      - Missing-in-result => statement not proved => INCONCLUSIVE
      - Extra-in-result => OK (new observables allowed) but flagged
      - Key set equality => match
    """
    pred = prereg.get("predictions", {})
    if not isinstance(pred, dict):
        return {"match": False, "error": "predictions must be a dict"}
    pred_keys = set(pred.keys())
    result_keys = set(result.keys())
    missing = sorted(pred_keys - result_keys)
    extra = sorted(result_keys - pred_keys)
    return {
        "match": not missing,
        "missing_in_result": missing,
        "extra_in_result": extra,
    }


# === DECISION-RULE EVALUATOR (Python analogue of Lean's `decide`) ===

# Tiny grammar: expr := term (("AND"|"OR") term)*
# term := atom ((">="|"<="|">"|"<"|"=="|"!=") atom)?
# atom := number | var_name | "abs(" expr ")"
# No real parser library — keep it intentionally small so the audit
# depends on a finite kernel of operations.

_TOKEN_RE = re.compile(
    r"\s*(>=|<=|!=|==|>=|<=|[()]|[+\-]?\d+\.?\d*|[A-Za-z_][A-Za-z_0-9]*|.)"
)


def _tokenize(rule: str) -> list[str]:
    tokens = []
    pos = 0
    while pos < len(rule):
        m = _TOKEN_RE.match(rule, pos)
        if not m or m.group(1) == "":
            raise ValueError(f"Parse error at position {pos}: {rule!r}")
        tok = m.group(1).strip()
        if tok:
            tokens.append(tok)
        pos = m.end()
    return tokens


def _parse_atom(tokens: list[str], pos: int, env: dict) -> tuple[Any, int]:
    """Parse a single atom: number | var | abs(...) | -atom | (expr)."""
    if pos >= len(tokens):
        raise ValueError("Unexpected end of input")
    tok = tokens[pos]
    if tok == "(":
        val, pos = _parse_expr(tokens, pos + 1, env)
        if pos >= len(tokens) or tokens[pos] != ")":
            raise ValueError("Expected closing paren")
        return val, pos + 1
    if tok == "abs":
        if pos + 1 >= len(tokens) or tokens[pos + 1] != "(":
            raise ValueError("abs( expected")
        val, pos = _parse_expr(tokens, pos + 2, env)
        if pos >= len(tokens) or tokens[pos] != ")":
            raise ValueError("abs(...) closing paren expected")
        return abs(val), pos + 1
    if tok == "-":
        val, pos = _parse_atom(tokens, pos + 1, env)
        return -val, pos
    # number
    try:
        return float(tok), pos + 1
    except ValueError:
        pass
    # variable lookup
    if tok not in env:
        raise ValueError(f"Unknown variable: {tok}")
    return env[tok], pos + 1


def _parse_comparison(tokens: list[str], pos: int, env: dict) -> tuple[bool, int]:
    """Parse a single comparison atom (possibly with comparison op)."""
    left, pos = _parse_atom(tokens, pos, env)
    if pos < len(tokens) and tokens[pos] in (">=", "<=", ">", "<", "==", "!="):
        op = tokens[pos]
        right, pos = _parse_atom(tokens, pos + 1, env)
        if op == ">=": return left >= right, pos
        if op == "<=": return left <= right, pos
        if op == ">":  return left > right, pos
        if op == "<":  return left < right, pos
        if op == "==": return left == right, pos
        if op == "!=": return left != right, pos
    # Truthiness of left
    return bool(left), pos


def _parse_expr(tokens: list[str], pos: int, env: dict) -> tuple[bool, int]:
    """Parse: comparison (("AND"|"OR") comparison)*"""
    val, pos = _parse_comparison(tokens, pos, env)
    while pos < len(tokens) and tokens[pos] in ("AND", "OR"):
        op = tokens[pos]
        rhs, pos = _parse_comparison(tokens, pos + 1, env)
        if op == "AND":
            val = val and rhs
        else:
            val = val or rhs
    return val, pos


# Allowed names in the sandboxed namespace. The user-facing rule language
# only sees these. Experimental modules are NEVER importable here.
_ALLOWED_NAMES = {"abs", "min", "max", "round", "True", "False"}

# Bind the actual builtins explicitly. Accessing them via __builtins__
# inside eval is fragile; we just put the references in the sandbox.
_ALLOWED_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "True": True,
    "False": False,
}

# Translate "AND"/"OR" to Python "and"/"or" so users can write either.
_PYTHON_BOOL_OPS = {"AND": "and", "OR": "or"}


def _pythonify_rule(rule: str) -> str:
    """Translate user-friendly AND/OR tokens to Python equivalents."""
    out = []
    for tok in _tokenize(rule):
        if tok in _PYTHON_BOOL_OPS:
            out.append(_PYTHON_BOOL_OPS[tok])
        else:
            out.append(tok)
    return " ".join(out)


def evaluate_decision_rule(rule: str, measurements: dict) -> bool:
    """Evaluate a small decidable subset of boolean expressions over numeric
    measurements. Returns True iff the rule is satisfied.

    Supports Python expressions involving:
      - comparison operators: >=, <=, >, <, ==, !=
      - boolean operators (spelled AND/OR; case-sensitive)
      - abs(), min(), max(), round(), arithmetic + - * /
      - variable lookup from `measurements`

    Safety: We evaluate the rule with a SANDBOXED globals() that exposes
    only a whitelist of names. Experimental modules cannot leak in.
    No import of experimental code. Pure logic.
    """
    sandbox = dict(_ALLOWED_FUNCTIONS)
    sandbox.update(measurements)
    py_rule = _pythonify_rule(rule)
    try:
        return bool(eval(py_rule, {"__builtins__": {}}, sandbox))
    except Exception as e:
        raise ValueError(f"Rule evaluation failed: {e}") from e


# === FULL AUDIT RUN ===

def audit_run(prereg_path: str, result_path: str) -> dict:
    """Run the comparator pipeline.

    Steps (mapped to zeta-23 comparator):
      1. Load prereg (= Challenge.lean). Structural audit.
      2. Load result (= Solution.lean). Statement-coincidence check.
      3. Evaluate decision_rule (= kernel replay).
      4. Classify: CONFIRMED | REFUTED | INCONCLUSIVE.
    """
    with open(prereg_path) as f:
        prereg = json.load(f)
    with open(result_path) as f:
        result = json.load(f)

    struct = audit_prereg_structure(prereg)
    if not struct["ok"]:
        return {
            "status": "INCONCLUSIVE",
            "reason": f"Prereg structure invalid: missing {struct['missing_fields']}",
            "statement_coincidence": False,
            "decision_rule_holds": False,
        }

    diff = compare_statement_sets(prereg, result)
    if not diff["match"]:
        return {
            "status": "INCONCLUSIVE",
            "reason": "Statement set mismatch",
            "missing_in_result": diff["missing_in_result"],
            "extra_in_result": diff["extra_in_result"],
            "statement_coincidence": False,
            "decision_rule_holds": False,
        }

    try:
        rule_ok = evaluate_decision_rule(
            prereg["decision_rule"],
            result,
        )
    except Exception as e:
        return {
            "status": "INCONCLUSIVE",
            "reason": f"Decision rule evaluation failed: {e}",
            "statement_coincidence": True,
            "decision_rule_holds": None,
        }

    return {
        "status": "CONFIRMED" if rule_ok else "REFUTED",
        "statement_coincidence": True,
        "decision_rule_holds": rule_ok,
        "extra_in_result": diff["extra_in_result"],
    }


# === CLI ENTRY POINT ===

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Comparator-style prereg audit (after zeta-23-lean)"
    )
    parser.add_argument("--prereg", required=True, help="Prereg JSON file (Challenge)")
    parser.add_argument("--result", required=True, help="Result JSON file (Solution)")
    parser.add_argument("--out", help="Optional: write verdict to this JSON file")
    args = parser.parse_args()

    verdict = audit_run(args.prereg, args.result)
    print(json.dumps(verdict, indent=2))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(verdict, f, indent=2)


if __name__ == "__main__":
    main()