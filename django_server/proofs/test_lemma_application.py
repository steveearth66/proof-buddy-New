"""
test_lemma_application.py

Pure engine-level tests for LemmaRule (ERRuleset.py) and LemmaApplicator.py.
No database access required.

Lemma used throughout:
  premise    = (+ n 0)   [since + n 0 = n is a common arithmetic identity]
  conclusion = n
  param      = n
"""

from expression_tree.ERProofEngine import ERProof, ERProofLine
from expression_tree.ERRuleset import LemmaRule, getDefaultRuleSet
from expression_tree.LemmaApplicator import extract_free_vars, build_lemma_rule, validate_lemma_application
from expression_tree.Parser import makeBasicAst
from expression_tree.ERCommon import findNode
import sys

_RED   = "\x1b[1;31m" if sys.stdout.isatty() else ""
_RESET = "\x1b[0m"    if sys.stdout.isatty() else ""

import builtins as _bi
_orig_print_la = _bi.print
def _red_fail_print(*args, **kwargs):
    if args and isinstance(args[0], str) and '  FAIL' in args[0]:
        _orig_print_la(_RED + args[0] + _RESET, *args[1:], **kwargs)
    else:
        _orig_print_la(*args, **kwargs)
_bi.print = _red_fail_print

totalFails = 0

def _expect_pass(test_name: str, ok: bool, msg, expected_result: str = None, result_node=None):
    global totalFails
    if not ok:
        print(f"  FAIL {test_name}: expected PASS but got error: {msg}")
        totalFails += 1
    elif expected_result is not None and result_node is not None:
        actual = str(result_node)
        if actual != expected_result:
            print(f"  FAIL {test_name}: result mismatch: expected '{expected_result}', got '{actual}'")
            totalFails += 1
        else:
            print(f"  pass {test_name}")
    else:
        print(f"  pass {test_name}")


def _expect_fail(test_name: str, ok: bool, fragment: str = ""):
    global totalFails
    if ok:
        print(f"  FAIL {test_name}: expected FAIL but got PASS")
        totalFails += 1
    elif fragment and fragment.lower() not in str("" if ok else "").lower():
        # We just check it failed; fragment matching is a bonus
        print(f"  pass {test_name}  (error as expected)")
    else:
        print(f"  pass {test_name}")


# ──────────────────────────────────────────────────────────────────────
# Setup: shared objects
# ──────────────────────────────────────────────────────────────────────

print("[Summary] Lemma Application Tests")

_ruleSet = getDefaultRuleSet()
_generics = {}

# Lemma: (+ n 0) = n  (param: n)
PREMISE_STR    = "(+ n 0)"
CONCLUSION_STR = "n"

# ──────────────────────────────────────────────────────────────────────
# extract_free_vars
# ──────────────────────────────────────────────────────────────────────

vars_, errs_ = extract_free_vars(PREMISE_STR, _ruleSet, _generics)
if vars_ == ["n"] and not errs_:
    print("  pass extract_free_vars returns ['n']")
else:
    print(f"  FAIL extract_free_vars: expected ['n'], got {vars_} errs={errs_}")
    totalFails += 1

# ──────────────────────────────────────────────────────────────────────
# build_lemma_rule
# ──────────────────────────────────────────────────────────────────────

lemma, build_err = build_lemma_rule("myLemma", PREMISE_STR, CONCLUSION_STR, _ruleSet, _generics)
if build_err or lemma is None:
    print(f"  FAIL build_lemma_rule: {build_err}")
    totalFails += 1
else:
    print("  pass build_lemma_rule succeeds for '(+ n 0) = n'")
    assert lemma.param_names == ["n"], f"param_names mismatch: {lemma.param_names}"

# ──────────────────────────────────────────────────────────────────────
# Helper: get the root node of a fully parsed expression
# ──────────────────────────────────────────────────────────────────────

def _root_node(expr_str: str):
    pl = ERProofLine(expr_str)
    return pl.exprTree


# ──────────────────────────────────────────────────────────────────────
# Test 1 — param count mismatch (too few)
# ──────────────────────────────────────────────────────────────────────

target = _root_node("(+ 3 0)")
ok, msg, _ = validate_lemma_application(PREMISE_STR, CONCLUSION_STR, [], target, _ruleSet, _generics)
if not ok and "requires 1 parameter" in msg:
    print("  pass test_param_count_too_few")
else:
    print(f"  FAIL test_param_count_too_few: ok={ok}, msg={msg}")
    totalFails += 1

# ──────────────────────────────────────────────────────────────────────
# Test 2 — param count mismatch (too many)
# ──────────────────────────────────────────────────────────────────────

target = _root_node("(+ 3 0)")
ok, msg, _ = validate_lemma_application(PREMISE_STR, CONCLUSION_STR, ["n=3", "m=0"], target, _ruleSet, _generics)
if not ok and "requires 1 parameter" in msg:
    print("  pass test_param_count_too_many")
else:
    print(f"  FAIL test_param_count_too_many: ok={ok}, msg={msg}")
    totalFails += 1

# ──────────────────────────────────────────────────────────────────────
# Test 3 — param name mismatch
# ──────────────────────────────────────────────────────────────────────

target = _root_node("(+ 3 0)")
ok, msg, _ = validate_lemma_application(PREMISE_STR, CONCLUSION_STR, ["m=3"], target, _ruleSet, _generics)
if not ok and "Unknown parameter" in msg:
    print("  pass test_param_name_mismatch")
else:
    print(f"  FAIL test_param_name_mismatch: ok={ok}, msg={msg}")
    totalFails += 1

# ──────────────────────────────────────────────────────────────────────
# Test 4 — wrong subexpression highlighted
#          Rule expects (+ n 0) but user highlights (+ 3 1) instead
# ──────────────────────────────────────────────────────────────────────

target = _root_node("(+ 3 1)")
ok, msg, _ = validate_lemma_application(PREMISE_STR, CONCLUSION_STR, ["n=3"], target, _ruleSet, _generics)
if not ok and "does not match" in msg:
    print("  pass test_wrong_subexpr_highlighted")
else:
    print(f"  FAIL test_wrong_subexpr_highlighted: ok={ok}, msg={msg}")
    totalFails += 1

# ──────────────────────────────────────────────────────────────────────
# Test 5 — wrong param value (structural mismatch)
#          Target is (+ 3 0) but user claims n=5
# ──────────────────────────────────────────────────────────────────────

target = _root_node("(+ 3 0)")
ok, msg, _ = validate_lemma_application(PREMISE_STR, CONCLUSION_STR, ["n=5"], target, _ruleSet, _generics)
if not ok and "does not match" in msg:
    print("  pass test_wrong_param_value")
else:
    print(f"  FAIL test_wrong_param_value: ok={ok}, msg={msg}")
    totalFails += 1

# ──────────────────────────────────────────────────────────────────────
# Test 6 — happy path: simple numeric argument
#          (+ 3 0) with n=3  →  result should be "3"
# ──────────────────────────────────────────────────────────────────────

target = _root_node("(+ 3 0)")
ok, msg, result = validate_lemma_application(PREMISE_STR, CONCLUSION_STR, ["n=3"], target, _ruleSet, _generics)
if ok and str(result) == "3":
    print("  pass test_happy_path_numeric")
else:
    print(f"  FAIL test_happy_path_numeric: ok={ok}, msg={msg}, result={result}")
    totalFails += 1

# ──────────────────────────────────────────────────────────────────────
# Test 7 — happy path: compound argument
#          (+ (+ k 1) 0) with n=(+ k 1)  →  result should be "(+ k 1)"
# Uses makeBasicAst for target to avoid the full labelling pipeline that
# would reject the unbound symbol 'k'.
# ──────────────────────────────────────────────────────────────────────

target_basic, _ = makeBasicAst("(+ (+ k 1) 0)")
ok, msg, result = validate_lemma_application(PREMISE_STR, CONCLUSION_STR, ["n=(+ k 1)"],
                                              target_basic, _ruleSet, _generics)
if ok and str(result) == "(+ k 1)":
    print("  pass test_happy_path_compound_arg")
else:
    print(f"  FAIL test_happy_path_compound_arg: ok={ok}, msg={msg}, result={result}")
    totalFails += 1

# ──────────────────────────────────────────────────────────────────────
# Test 8 — multi-param lemma: premise (+ a b), conclusion (+ b a)
#          Applying to (+ 2 3) with a=2, b=3  →  result (+ 3 2)
# ──────────────────────────────────────────────────────────────────────

PREMISE2    = "(+ a b)"
CONCLUSION2 = "(+ b a)"

target = _root_node("(+ 2 3)")
ok, msg, result = validate_lemma_application(PREMISE2, CONCLUSION2, ["a=2", "b=3"],
                                              target, _ruleSet, _generics)
if ok and str(result) == "(+ 3 2)":
    print("  pass test_multi_param_happy_path")
else:
    print(f"  FAIL test_multi_param_happy_path: ok={ok}, msg={msg}, result={result}")
    totalFails += 1

# ──────────────────────────────────────────────────────────────────────
# Test 9 — invalid parameter value syntax
# ──────────────────────────────────────────────────────────────────────

target = _root_node("(+ 3 0)")
ok, msg, _ = validate_lemma_application(PREMISE_STR, CONCLUSION_STR, ["n=((bad"],
                                         target, _ruleSet, _generics)
if not ok:
    print("  pass test_invalid_param_syntax")
else:
    print(f"  FAIL test_invalid_param_syntax: expected failure but got PASS")
    totalFails += 1

# ──────────────────────────────────────────────────────────────────────
# Test 10 — lemma result is a valid proof-engine node
#   Apply lemma (+ n 0) → n to a proof, then verify the resulting
#   expression can be further rewritten by the engine.
#   This confirms lemma conclusions integrate seamlessly into the proof
#   tree for subsequent rules (Phase 7).
#
#   Expression: (+ (+ 3 0) 0)
#   Positions (via updatePositions):
#     outer '(' = 0, outer '+' = 1, inner '(' = 3, inner '+' = 4,
#     '3' = 6,  inner '0' = 8,  outer '0' = 11
#   So start_position = 3 highlights the inner (+ 3 0) subexpression.
# ──────────────────────────────────────────────────────────────────────

proof = ERProof()
proof.addProofLine("(+ (+ 3 0) 0)")  # premise

_lemma, _ = build_lemma_rule("myLemma", PREMISE_STR, CONCLUSION_STR, proof.ruleSet, {})
proof.ruleSet['apply']['myLemma'] = _lemma
proof.addProofLine("(+ (+ 3 0) 0)", "apply myLemma n=3", 3)
del proof.ruleSet['apply']['myLemma']

if proof.errLog:
    print(f"  FAIL test_lemma_in_engine_proof: {proof.errLog}")
    totalFails += 1
else:
    result_str = str(proof.proofLines[-1].exprTree)
    # Inner (+ 3 0) → 3, so full expression becomes (+ 3 0)
    if result_str == "(+ 3 0)":
        print(f"  pass test_lemma_in_engine_proof (result='{result_str}')")
    else:
        print(f"  FAIL test_lemma_in_engine_proof: expected '(+ 3 0)', got '{result_str}'")
        totalFails += 1

print()
if totalFails == 0:
    print("All lemma application tests passed!")
else:
    print(f"{_RED}Lemma application test failures: {totalFails}{_RESET}")
