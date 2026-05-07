"""
Tests for UDFs that call other UDFs in their body.

Verifies that arg-count and type checking use the callee's own signature
rather than the outer UDF's type — a bug that previously caused errors
like 'append only takes 1 argument' when defining reverse.
"""

from expression_tree.ERProofEngine import ERProof, ERProofLine, TwoSidedProof
import sys

_RED   = "\x1b[1;31m" if sys.stdout.isatty() else ""
_RESET = "\x1b[0m"    if sys.stdout.isatty() else ""

totalFails = 0

def _fail(name, detail):
    global totalFails
    print(f"{_RED}  FAIL {name}: {detail}{_RESET}")
    totalFails += 1

def _pass(name):
    print(f"  pass {name}")


print("[Summary] UDF-calls-UDF tests")

# ── shared proof with append already registered ───────────────────────
def _fresh():
    p = ERProof()
    p.addUDF('(append L M)', '(LIST, LIST)>LIST',
             '(if (null? L) M (cons (first L) (append (rest L) M)))')
    p.errLog = []
    return p

# ── 1. defining rev (calls append) produces no errors ─────────────
p = _fresh()
p.addUDF('(rev L)', 'list>list',
         '(if (null? L) null (append (rev (rest L)) (cons (first L) null)))')
if p.errLog:
    _fail("define_reverse_no_error", p.errLog)
else:
    _pass("define_reverse_no_error")

# ── 2. append still enforces 2-arg check in standalone expressions ─────
p = _fresh()
line = ERProofLine('(append null null null)', ruleDict=p.ruleSet)
if line.errLog == ['append only takes 2 arguments, but 3 were provided']:
    _pass("append_rejects_3_args")
else:
    _fail("append_rejects_3_args", f"errLog={line.errLog}")

# ── 3. append accepts exactly 2 args ──────────────────────────────────
p = _fresh()
line = ERProofLine('(append null null)', ruleDict=p.ruleSet)
if not line.errLog:
    _pass("append_accepts_2_args")
else:
    _fail("append_accepts_2_args", f"errLog={line.errLog}")

# ── 4. rev enforces 1-arg check ───────────────────────────────────
p = _fresh()
p.addUDF('(rev L)', 'list>list',
         '(if (null? L) null (append (rev (rest L)) (cons (first L) null)))')
p.errLog = []
line = ERProofLine('(rev null null)', ruleDict=p.ruleSet)
if line.errLog == ['rev only takes 1 argument, but 2 were provided']:
    _pass("reverse_rejects_2_args")
else:
    _fail("reverse_rejects_2_args", f"errLog={line.errLog}")

# ── 5. rev accepts exactly 1 arg ──────────────────────────────────
p = _fresh()
p.addUDF('(rev L)', 'list>list',
         '(if (null? L) null (append (rev (rest L)) (cons (first L) null)))')
p.errLog = []
line = ERProofLine('(rev null)', ruleDict=p.ruleSet)
if not line.errLog:
    _pass("reverse_accepts_1_arg")
else:
    _fail("reverse_accepts_1_arg", f"errLog={line.errLog}")

# ── 6. append body itself uses correct recursive 2-arg check ────────────
# (verifies the fix doesn't break append's self-recursive call count)
p2 = ERProof()
p2.addUDF('(append L M)', '(LIST, LIST)>LIST',
          '(if (null? L) M (cons (first L) (append (rest L) M)))')
if p2.errLog:
    _fail("append_self_recursive_body_ok", p2.errLog)
else:
    _pass("append_self_recursive_body_ok")

# ── 7. actual UI scenario: TwoSidedProof, append enabled as default UDF first ─
# This is the real-world flow — the API uses TwoSidedProof and append is
# applied via use_definition before the user defines reverse.
proof = TwoSidedProof()
proof.addUDF('(append L M)', '(LIST, LIST)>LIST',
             '(if (null? L) M (cons (first L) (append (rest L) M)))')
proof.errLog = []
proof.addUDF('(rev L)', 'list>list',
             '(if (null? L) null (append (rev (rest L)) (cons (first L) null)))')
if proof.errLog:
    _fail("reverse_with_append_as_default_udf", proof.errLog)
else:
    _pass("reverse_with_append_as_default_udf")

# ── 8. callee not yet defined (backend cache cleared scenario) ─────────
# If the Django cache is cleared (server restart), the cached TwoSidedProof
# loses its UDFs. reverse calling an unknown 'append' must not raise a
# spurious arg-count error — the engine should accept it without numArgs info.
p = ERProof()
p.addUDF('(rev L)', 'list>list',
         '(if (null? L) null (append (rev (rest L)) (cons (first L) null)))')
if p.errLog:
    _fail("reverse_without_append_predefined", p.errLog)
else:
    _pass("reverse_without_append_predefined")

print()
if totalFails == 0:
    print("All UDF-calls-UDF tests passed!")
else:
    print(f"{_RED}UDF-calls-UDF test failures: {totalFails}{_RESET}")
