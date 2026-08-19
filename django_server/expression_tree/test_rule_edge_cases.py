"""
Additional edge-case / robustness tests for Rule subclasses and applyRule.

Companion to test_rule_subclasses.py. Documents intended behavior and known gaps
(e.g. bad startPos IndexError, AdvMath numeric false positives, UDF list return).

Run from django_server/:
    py -m expression_tree.test_rule_edge_cases
"""

from __future__ import annotations

from expression_tree.ERProofEngine import ERProof, ERProofLine, TwoSidedProof
from expression_tree.ERRuleset import (
    AdvLogic,
    AdvMath,
    ConsProp,
    FirstProp,
    IH,
    NullQ,
    Plus,
    REWRITE_RULES,
    RestList,
    ZeroQ,
    ZeroQPlus,
    getDefaultRuleSet,
)
from expression_tree.LemmaApplicator import validate_lemma_application
from expression_tree.Parser import makeBasicAst
from expression_tree.Labeler import labelTree
import sys

_RED = "\x1b[1;31m" if sys.stdout.isatty() else ""
_RESET = "\x1b[0m" if sys.stdout.isatty() else ""

total_fails = 0
total_passes = 0


def parse(s: str):
    tree, errs = makeBasicAst(s)
    assert not errs, f"parse failed for {s!r}: {errs}"
    labelTree(tree, [])
    return tree


def make_proof_with_generics(**type_map):
    p = ERProof()
    for label, spec in type_map.items():
        if isinstance(spec, tuple):
            p.addGeneric(label, spec[0], spec[1])
        else:
            p.addGeneric(label, spec)
    assert p.errLog == [], f"addGeneric failed: {p.errLog}"
    return p


def check(label: str, condition: bool, detail: str = ""):
    global total_fails, total_passes
    if condition:
        total_passes += 1
        print(f"  PASS  {label}")
    else:
        total_fails += 1
        print(f"  {_RED}FAIL{_RESET}  {label}" + (f": {detail}" if detail else ""))


def find_data(node, data: str):
    if node.data == data:
        return node
    for child in node.children:
        found = find_data(child, data)
        if found is not None:
            return found
    return None


# ===========================================================================
print("\n=== Engine apply-path robustness ===")
# ===========================================================================

# [error] Bad startPos — findNode returns [] and applyRule indexes [0] → IndexError today
p = ERProof()
p.addProofLine("(+ 1 2)")
crashed = False
try:
    p.addProofLine("(+ 1 2)", "eval +", 99999)
except IndexError:
    crashed = True
check(
    "[error] E1 bad startPos currently raises IndexError (known gap)",
    crashed,
    f"errLog={p.errLog}",
)

# [error] Apply rule on a node inside a quoted list
p = ERProof()
p.addProofLine("(cons 1 '(2 3))")
two = find_data(p.proofLines[0].exprTree, "2")
check("[error] E2a found quoted '2' node", two is not None and "'(" in two.ancestors())
if two is not None:
    p2 = ERProof()
    p2.addProofLine("(cons 1 '(2 3))")
    p2.addProofLine("(cons 1 '(2 3))", "eval null?", two.startPosition)
    check(
        "[error] E2 apply inside quote rejected",
        any("quoted" in e.lower() for e in p2.errLog),
        str(p2.errLog),
    )

# [error] Undefined symbol in highlight — step must not be committed
p = ERProof()
p.addProofLine("(+ foo 1)")
check("[error] E3a (+ foo 1) parses (foo unbound until apply)", p.errLog == [] and len(p.proofLines) == 1)
p.addProofLine("(+ foo 1)", "eval +")
check(
    "[error] E3 undefined label rejects step",
    p.errLog != [] and any("foo" in e for e in p.errLog) and len(p.proofLines) == 1,
    f"errLog={p.errLog} nlines={len(p.proofLines)}",
)

# [error] Empty / incomplete rule strings
p = ERProof()
p.addProofLine("(+ 1 2)")
p.addProofLine("(+ 1 2)", "")
check(
    "[error] E4 empty rule string",
    any("eval" in e.lower() or "rewrite" in e.lower() or "apply" in e.lower() for e in p.errLog),
    str(p.errLog),
)

p = ERProof()
p.addProofLine("(+ 1 2)")
p.addProofLine("(+ 1 2)", "eval")
check("[error] E5 'eval' with no rule name", p.errLog != [], str(p.errLog))

p = ERProof()
p.addProofLine("(+ 1 2)")
p.addProofLine("(+ 1 2)", "   eval   +   ")
# split() collapses whitespace — should still work
check(
    "[edge] E6 whitespace-normalized 'eval +'",
    p.errLog == [] and str(p.proofLines[-1].exprTree) == "3",
    f"errLog={p.errLog} result={str(p.proofLines[-1].exprTree) if p.proofLines else None!r}",
)

# [error] HIGH auto-infer on structurally wrong target
p = TwoSidedProof()
p.LHS.addProofLine("(+ 1 2)")
p.LHS.addProofLine("(+ 1 2)", "rewrite first-cons", 0, auto_infer=True)
check(
    "[error] E7 HIGH infer on wrong structure",
    p.LHS.errLog != [] and any("first-cons" in e or "root operation" in e for e in p.LHS.errLog),
    str(p.LHS.errLog),
)

# [error] Duplicate lemma params leave a required name missing
_rs = getDefaultRuleSet()
target = ERProofLine("(+ 1 2)").exprTree
ok, msg, _ = validate_lemma_application(
    "(+ a b)", "(+ b a)", ["a=1", "a=2"], target, _rs, {}
)
check(
    "[error] E8 duplicate param names (missing b)",
    (not ok) and ("Missing parameter" in msg or "b" in msg),
    msg,
)


# ===========================================================================
print("\n=== BuiltIn / eval edge cases ===")
# ===========================================================================

# [error] Non-boolean if condition — caught at decoration/type time
line = ERProofLine("(if 1 x y)")
check(
    "[error] B_IF1 (if 1 x y) type-rejected at parse",
    line.errLog != [] and any("Boolean" in e or "BOOL" in e or "int" in e.lower() for e in line.errLog),
    str(line.errLog),
)

# [error] Rest on null (full decoration)
rest_line = ERProofLine("(rest null)")
check("[error] B_REST1a decorate (rest null)", rest_line.errLog == [], str(rest_line.errLog))
if rest_line.errLog == []:
    ok, msg = RestList().isApplicable(rest_line.exprTree)
    check("[error] B_REST1 (rest null) rejected", not ok and "non-empty" in msg.lower(), msg)

# [error] Eval + with generic args (allowGenerics=False on Plus)
p = make_proof_with_generics(k="int")
p.addProofLine("(+ k 1)")
ok, msg = Plus().isApplicable(p.proofLines[-1].exprTree)
check("[error] B_PLUS1 Plus rejects generic args", not ok and "generic" in msg.lower(), msg)

# [edge] NullQ on GenericAny — GenericAny.neverNull defaults True → applicable #f
p = make_proof_with_generics(x="any")
p.addProofLine("(null? x)")
ok, msg = NullQ().isApplicable(p.proofLines[-1].exprTree)
check("[edge] B_NULL_ANY NullQ on GenericAny applicable", ok, msg)
if ok:
    check(
        "[edge] B_NULL_ANY result #f",
        str(NullQ().insertSubstitution(p.proofLines[-1].exprTree)) == "#f",
    )

# [error] ZeroQ on GenericAny — cannot determine
p = make_proof_with_generics(x="any")
p.addProofLine("(zero? x)")
ok, msg = ZeroQ().isApplicable(p.proofLines[-1].exprTree)
check("[error] B_ZERO_ANY ZeroQ on GenericAny rejected", not ok and "Cannot determine" in msg, msg)


# ===========================================================================
print("\n=== Axiom edge cases ===")
# ===========================================================================

# [error] Wrong root / insufficient pattern for first-cons
ok, msg = FirstProp().verifyStructure(parse("(+ 1 2)"))
check("[error] A_SHORT first-cons on (+) rejected", not ok, msg)

# [error] cons-first-rest with unresolved list args
ok, msg = ConsProp().isApplicable(
    parse("(cons (first (+ 1 2)) (rest (+ 1 2)))"),
    ["L=(+ 1 2)"],
)
check(
    "[error] A_UNRES cons-first-rest unresolved L",
    not ok and "resolved" in msg.lower(),
    msg,
)

# [error] Commutative zero?+ with wrong explicit assignment (a is 1, not 2)
p = make_proof_with_generics(k="int")
p.addProofLine("(zero? (+ 1 k))")
ok, msg = ZeroQPlus().isApplicable(p.proofLines[-1].exprTree, ["a=2", "k=k"])
check(
    "[error] A_ZQ_WRONG wrong assignment a=2 rejected",
    not ok and "mismatch" in msg.lower(),
    msg,
)


# ===========================================================================
print("\n=== Lemma / IH / UDF edge cases ===")
# ===========================================================================

# [edge] Lemma RHS free var not in premise — currently accepted (known gap)
ok, msg, result = validate_lemma_application(
    "(+ n 0)", "(+ n m)", ["n=3"], ERProofLine("(+ 3 0)").exprTree, _rs, {}
)
check(
    "[edge] LEM_RHS_EXTRA lemma with free var only on RHS currently accepted",
    ok and result is not None and "m" in str(result),
    f"ok={ok} msg={msg} result={result}",
)

# [edge] IH string match is whitespace-normalized by str(Node)
ih = IH(parse("(+ 1 2)"), parse("3"))
line = ERProofLine("(+ 1  2)")  # extra spaces in source
check("[edge] IH_WS parse (+ 1  2)", line.errLog == [], str(line.errLog))
if line.errLog == []:
    ok, msg = ih.isApplicable(line.exprTree)
    check("[edge] IH_WS matches despite source whitespace", ok, msg)

# [error] UDF on non-matching call label
ok, msg = udf.isApplicable(parse("(other 3)"))
# other may return tuple
if isinstance(msg, str):
    check("[error] UDF_LABEL wrong label", not ok and "Cannot apply" in msg, msg)
else:
    check("[error] UDF_LABEL wrong label", not ok, str(msg))


# ===========================================================================
print("\n=== AdvMath / AdvLogic edge cases ===")
# ===========================================================================

am = AdvMath()
al = AdvLogic()

# [edge] Numeric sampling false positive: (quotient k k) ~ 1 for positive k, undefined at 0
ok, msg = am.isApplicable(parse("(quotient k k)"), parse("1"))
check(
    "[edge] AM_FP (quotient k k)~1 accepted via positive sampling (known gap)",
    ok,
    msg,
)

# [edge] Complexity allowed when support_rewrite_complexity=True
big = parse("(+ (+ (+ (+ (+ 1 2) 3) 4) 5) 6)")
big2 = parse("(+ (+ (+ (+ (+ 6 5) 4) 3) 2) 1)")
ok_strict, msg_strict = am.isApplicable(big, big2, False)
ok_relaxed, msg_relaxed = am.isApplicable(big, big2, True)
check("[edge] AM_CX_STRICT complexity False rejects large both sides", not ok_strict, msg_strict)
check(
    "[edge] AM_CX_RELAX complexity True allows equivalent large exprs",
    ok_relaxed,
    msg_relaxed,
)

# [edge] AdvLogic: non-logic *source* with logic substitute — guard only checks subNode
p_bool = make_proof_with_generics(p="bool")
sub = ERProofLine("(and p p)", generics=p_bool.generics)
ok, msg = al.isApplicable(parse("(+ 1 2)"), sub.exprTree)
check(
    "[edge] AL_SRC_NONLOGIC non-logic source fails equivalence (not 'logic operation' guard)",
    (not ok) and "logic operation" not in msg.lower(),
    msg,
)


# ===========================================================================
print("\n=== Shared mutable rule instance ===")
# ===========================================================================

# REWRITE_RULES entries are shared across proofs
r_a = REWRITE_RULES["first-cons"]
r_b = REWRITE_RULES["first-cons"]
check("[edge] SHARE_SAME first-cons is shared singleton", r_a is r_b)

n1 = parse("(first (cons 7 null))")
n2 = parse("(first (cons 8 null))")
ok1, _ = r_a.isApplicable(n1, ["x=7", "L=null"])
ok2, _ = r_b.isApplicable(n2, ["x=8", "L=null"])
check("[edge] SHARE_SEQ sequential isApplicable both succeed", ok1 and ok2)
check(
    "[edge] SHARE_MAP last isApplicable wins mappings",
    str(r_a._paramMappings["x"]) == "8",
    str(r_a._paramMappings),
)

# MinusPlus.insertSubstitution reads _paramMappings — interleaved apply can corrupt
mp = REWRITE_RULES["-+"]
p1 = make_proof_with_generics(k="int", a="int")
p1.addProofLine("(- (+ k a) a)")
p2 = make_proof_with_generics(m="int", b="int")
p2.addProofLine("(- (+ m b) b)")
n_mp1 = p1.proofLines[-1].exprTree
n_mp2 = p2.proofLines[-1].exprTree
ok_m1, msg_m1 = mp.isApplicable(n_mp1, ["a=a", "k=k"])
check("[edge] SHARE_MP1 -+ applicable on first proof", ok_m1, msg_m1)
# Interleave: validate second proof before substituting first
ok_m2, msg_m2 = mp.isApplicable(n_mp2, ["a=b", "k=m"])
check("[edge] SHARE_MP2 -+ applicable on second proof", ok_m2, msg_m2)
# insertSubstitution for first node now uses mappings from second apply
if ok_m1 and ok_m2:
    stolen = mp.insertSubstitution(n_mp1)
    check(
        "[edge] SHARE_MP_CORRUPT interleaved -+ insert uses later mappings (known gap)",
        str(stolen) == "m",  # should have been k if mappings were per-call
        f"got {stolen!r}",
    )


# ===========================================================================
print()
if total_fails == 0:
    print(f"All rule edge-case tests passed ({total_passes} checks).")
else:
    print(f"{_RED}Rule edge-case test failures: {total_fails} (passes: {total_passes}){_RESET}")
    sys.exit(1)
