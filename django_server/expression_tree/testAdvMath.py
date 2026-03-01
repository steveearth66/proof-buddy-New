"""
Regression tests for AdvMath "rewrite math" rule, including the non-math
abstraction helpers (_fresh_var, _collect_node_names, _abstractedMathStr)
and end-to-end AdvMath.isApplicable() behaviour.

Run from django_server/ with:
    py -m expression_tree.testAdvMath
"""

from .Parser import makeBasicAst
from .Labeler import labelTree
from .ERRuleset import (
    _collect_node_names,
    _fresh_var,
    _abstractedMathStr,
    AdvMath,
)

def parse(s):
    tree, _errs = makeBasicAst(s)
    labelTree(tree, [])
    return tree

def check(label, condition, detail=""):
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}" + (f": {detail}" if detail else ""))

print("\n=== _fresh_var tests ===")

used = {'a', 'b', 'x', 'k'}
v1 = _fresh_var(used)
check("skips taken names, returns c", v1 == 'c', f"got {v1!r}")

v2 = _fresh_var(used)
check("next call returns d", v2 == 'd', f"got {v2!r}")

check("used set updated after each call", 'c' in used and 'd' in used)

used_full = set('abcdefghijklmnopqrstuvwxyz')
v3 = _fresh_var(used_full)
check("falls back to two-letter name when single letters exhausted",
      len(v3) == 2, f"got {v3!r}")

print("\n=== _collect_node_names tests ===")

names = set()
_collect_node_names(parse("(+ (length L) k)"), names)
check("collects leaf names: L", 'L' in names)
check("collects leaf names: k", 'k' in names)
check("collects operator names: +", '+' in names)
check("collects function names: length", 'length' in names)

print("\n=== _abstractedMathStr tests ===")

# pure math — no abstraction should occur
t1 = parse("(+ (* k k) 1)")
pairs1, used1 = [], set()
r1 = _abstractedMathStr(t1, pairs1, used1)
check("pure math produces no abstract pairs", pairs1 == [], f"pairs={pairs1}")
check("pure math result contains k and *", 'k' in r1 and '*' in r1, f"got {r1!r}")

# single non-math call -> gets one placeholder
t2 = parse("(+ (length L) 1)")
pairs2, used2 = [], set()
r2 = _abstractedMathStr(t2, pairs2, used2)
check("single non-math call makes one abstract pair", len(pairs2) == 1,
      f"pairs={[(v) for _,v in pairs2]}")
ph = pairs2[0][1]
check("placeholder appears in result string", ph in r2, f"result={r2!r}, ph={ph!r}")
check("original token 'length' gone from result", 'length' not in r2, f"result={r2!r}")

# two different non-math calls -> two different placeholders
t3 = parse("(+ (length L) (length M))")
pairs3, used3 = [], set()
r3 = _abstractedMathStr(t3, pairs3, used3)
check("two different calls make two abstract pairs", len(pairs3) == 2,
      f"got {len(pairs3)}")
ph_a, ph_b = pairs3[0][1], pairs3[1][1]
check("two different placeholders are distinct", ph_a != ph_b,
      f"both {ph_a!r}")

# same call appearing twice -> reuses same placeholder
t4 = parse("(+ (length L) (length L))")
pairs4, used4 = [], set()
r4 = _abstractedMathStr(t4, pairs4, used4)
check("identical repeated call makes only one abstract pair", len(pairs4) == 1,
      f"got {len(pairs4)}")
ph_rep = pairs4[0][1]
check("placeholder appears twice in result (both occurrences replaced)",
      r4.count(ph_rep) == 2, f"result={r4!r}")

# nested non-math: (f (g L)) should be replaced wholesale, not recursed into
t5 = parse("(+ (f (g L)) 1)")
pairs5, used5 = [], set()
r5 = _abstractedMathStr(t5, pairs5, used5)
check("nested non-math (f (g L)) replaced as single unit -> one pair",
      len(pairs5) == 1, f"got {len(pairs5)}")
check("g not visible in result (subtree not separately abstracted)",
      'g' not in r5, f"result={r5!r}")

# shared pairs list across two expressions (the key feature)
t6 = parse("(+ (+ (length L) (length M)) (length L))")
t7 = parse("(+ (length M) (* 2 (length L)))")
pairs6, used6 = [], set()
_collect_node_names(t6, used6)
_collect_node_names(t7, used6)
main_str = _abstractedMathStr(t6, pairs6, used6)
sub_str  = _abstractedMathStr(t7, pairs6, used6)   # same pairs6!
print(f"  INFO  main abstracted: {main_str}")
print(f"  INFO  sub  abstracted: {sub_str}")
lengthL_var = pairs6[0][1]   # first non-math call encountered is (length L)
check("(length L) placeholder appears twice in main expression",
      main_str.count(lengthL_var) == 2, f"main={main_str!r}, ph={lengthL_var!r}")
check("(length L) placeholder appears in substitution expression",
      lengthL_var in sub_str, f"sub={sub_str!r}, ph={lengthL_var!r}")

print("\n=== AdvMath.isApplicable end-to-end tests ===")

math_rule = AdvMath()

def applicable(src_str, sub_str_expr):
    src  = parse(src_str)
    sub  = parse(sub_str_expr)
    ok, msg = math_rule.isApplicable(src, sub)
    return ok, msg

# --- cases that should PASS ---

ok, _ = applicable("(* k 1)", "(* 1 k)")
check("pure math: (* k 1) equiv (* 1 k)", ok)

ok, _ = applicable("(* 2 (+ x 1))", "(+ 2 (* 2 x))")
check("pure math: (* 2 (+ x 1)) equiv (+ 2 (* 2 x))", ok)

ok, _ = applicable(
    "(+ (+ (length L) (length M)) (length L))",
    "(+ (length M) (* 2 (length L)))"
)
check("mixed: (+ (+ (length L) (length M)) (length L)) equiv (+ (length M) (* 2 (length L)))", ok)

ok, _ = applicable("(+ (f x) (f x))", "(* 2 (f x))")
check("mixed: (+ (f x) (f x)) equiv (* 2 (f x))", ok)

ok, _ = applicable("(+ k 0)", "k")
check("pure math: (+ k 0) equiv k", ok)

# --- cases that should FAIL ---

ok, msg = applicable("(+ (length L) 0)", "(* (length L) 2)")
check("mixed: (+ (length L) 0) NOT equiv (* (length L) 2) -> rejected", not ok,
      f"was incorrectly accepted: {msg}")

ok, msg = applicable("(+ k 1)", "(+ k 2)")
check("pure math: (+ k 1) NOT equiv (+ k 2) -> rejected", not ok,
      f"was incorrectly accepted: {msg}")

ok, msg = applicable("(+ (length L) (length M))", "(+ (length M) (length L))")
check("mixed: (+ (length L) (length M)) equiv (+ (length M) (length L)) by commutativity", ok)

ok, msg = applicable("(+ (length L) (length M))", "(* (length L) (length M))")
check("mixed: (+ (length L) (length M)) NOT equiv (* (length L) (length M)) -> rejected", not ok,
      f"was incorrectly accepted: {msg}")

print("\n=== done ===\n")
