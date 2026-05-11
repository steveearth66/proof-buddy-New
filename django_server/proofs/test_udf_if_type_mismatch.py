"""
Tests for post-fillBody if-branch type validation in UDF definitions.

Verifies that when a user defines a UDF whose if-expression has branches
returning different concrete types (e.g. INT vs LIST), the engine rejects
the definition with a clear error message instead of silently accepting it
and crashing later during proof application.

Root cause: during body parsing, parameters have type PARAM which is in
FLEX_TYPES, so the decorator's checkIf passes. The mismatch is only visible
after fillBody resolves PARAM -> the declared concrete types.

Run individually:
  py manage.py test proofs.test_udf_if_type_mismatch
"""

from django.test import TestCase
from expression_tree.ERProofEngine import ERProof, TwoSidedProof

_WRAP_BAD  = ('(wrap n x)', '(int,int)>list',
               '(if (zero? (+ n 1)) x (cons (wrap (- n 1) x) null))')
_WRAP_ANY  = ('(wrap n x)', '(int,any)>list',
               '(if (zero? (+ n 1)) x (cons (wrap (- n 1) x) null))')
_WRAP_LIST = ('(wrap n x)', '(int,list)>list',
               '(if (zero? (+ n 1)) x (cons (wrap (- n 1) x) null))')


class UDFIfBranchTypeMismatchTests(TestCase):
    """Engine-level tests: post-fillBody if-branch type validation in addUDF."""

    # ── 1. BAD: (int,int)>list — then resolves to INT, else to LIST ──────────
    def test_int_int_list_mismatch_produces_error(self):
        p = ERProof()
        p.addUDF(*_WRAP_BAD)
        self.assertTrue(
            p.errLog,
            "expected an error message for INT vs LIST branch mismatch, but errLog was empty"
        )

    # ── 2. BAD definition must NOT be registered in the ruleset ──────────────
    def test_int_int_list_mismatch_not_registered(self):
        p = ERProof()
        p.addUDF(*_WRAP_BAD)
        self.assertNotIn(
            'wrap', p.ruleSet.get('apply', {}),
            "wrap should not be registered in ruleSet when the definition has type errors"
        )

    # ── 3. Error message mentions both branch types ───────────────────────────
    def test_mismatch_error_mentions_branch_types(self):
        p = ERProof()
        p.addUDF(*_WRAP_BAD)
        msg = p.errLog[0] if p.errLog else ""
        self.assertIn('INT',  msg.upper(), f"error should mention INT, got: {msg!r}")
        self.assertIn('LIST', msg.upper(), f"error should mention LIST, got: {msg!r}")

    # ── 4. GOOD: (int,any)>list — any is in FLEX_TYPES, no error ─────────────
    def test_int_any_list_accepted(self):
        p = ERProof()
        p.addUDF(*_WRAP_ANY)
        self.assertFalse(p.errLog,
                         f"(int,any)>list should be accepted, got errLog={p.errLog}")
        self.assertIn('wrap', p.ruleSet.get('apply', {}),
                      "wrap should be registered in ruleSet when there are no errors")

    # ── 5. GOOD: (int,list)>list — both branches return LIST ─────────────────
    def test_int_list_list_accepted(self):
        p = ERProof()
        p.addUDF(*_WRAP_LIST)
        self.assertFalse(p.errLog,
                         f"(int,list)>list should be accepted, got errLog={p.errLog}")
        self.assertIn('wrap', p.ruleSet.get('apply', {}),
                      "wrap should be registered in ruleSet when there are no errors")

    # ── 6. BAD: non-recursive if, INT vs BOOL branches ───────────────────────
    def test_int_bool_branch_mismatch_rejected(self):
        p = ERProof()
        p.addUDF('(badfn n)', 'int>bool', '(if (zero? n) 1 #f)')
        self.assertTrue(
            p.errLog,
            "expected error for INT vs BOOL branch mismatch, but errLog was empty"
        )

    # ── 7. GOOD: non-recursive if, both branches BOOL ────────────────────────
    def test_bool_bool_branches_accepted(self):
        p = ERProof()
        p.addUDF('(iszero n)', 'int>bool', '(if (zero? n) #t #f)')
        self.assertFalse(p.errLog,
                         f"matching bool branches should be accepted, got errLog={p.errLog}")
        self.assertIn('iszero', p.ruleSet.get('apply', {}),
                      "iszero not registered in ruleSet despite no errors")

    # ── 8. TwoSidedProof: mismatch caught on LHS (the real API path) ─────────
    def test_twosidedproof_lhs_mismatch_rejected(self):
        proof = TwoSidedProof()
        proof.LHS.addUDF(*_WRAP_BAD)
        self.assertTrue(
            proof.LHS.errLog,
            "TwoSidedProof LHS should reject (int,int)>list if-branch mismatch"
        )


class UDFLabelQuestionMarkTests(TestCase):
    """Label validation: '?' is legal only as the last character."""

    # ── 9. GOOD: trailing ? accepted ─────────────────────────────────────────
    def test_trailing_question_mark_accepted(self):
        p = ERProof()
        p.addUDF('(mycheck? n)', 'int>bool', '(if (zero? n) #t #f)')
        self.assertFalse(p.errLog,
                         f"label ending in ? should be accepted, got errLog={p.errLog}")
        self.assertIn('mycheck?', p.ruleSet.get('apply', {}),
                      "mycheck? not registered in ruleSet despite no errors")

    # ── 10. GOOD: plain alpha still works ────────────────────────────────────
    def test_plain_alpha_label_accepted(self):
        p = ERProof()
        p.addUDF('(iszero n)', 'int>bool', '(if (zero? n) #t #f)')
        self.assertFalse(p.errLog,
                         f"plain alpha label should be accepted, got errLog={p.errLog}")

    # ── 11. BAD: ? in the middle rejected ────────────────────────────────────
    def test_middle_question_mark_rejected(self):
        p = ERProof()
        p.addUDF('(my?fn n)', 'int>bool', '(if (zero? n) #t #f)')
        self.assertTrue(p.errLog,
                        "label with ? in the middle should be rejected")

    # ── 12. BAD: ? alone (no alpha prefix) rejected ───────────────────────────
    def test_question_mark_only_rejected(self):
        p = ERProof()
        p.addUDF('(? n)', 'int>bool', '(if (zero? n) #t #f)')
        self.assertTrue(p.errLog,
                        "label '?' with no alpha characters should be rejected")
