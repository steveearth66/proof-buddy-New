"""
Tests for the AdvLogic "rewrite logic" rule.

No database calls are made in this file. All tests are pure expression-tree
engine tests that exercise AdvLogic via TwoSidedProof.addProofLine().

These tests are written before Phase 1 implementation (TDD). They will fail
with "Could not find rule associated with 'logic'" until AdvLogic is added
to REWRITE_RULES in expression_tree/ERRuleset.py.

Run individually:
    $env:PYTHONIOENCODING="utf-8"; py manage.py test equational_reasoning_api.test_rewrite_logic
"""
from django.test import TestCase
from expression_tree.ERProofEngine import TwoSidedProof


class AdvLogicTests(TestCase):
    """Engine-level tests for the AdvLogic 'rewrite logic' rule.
    No ORM calls — pure expression-tree logic only."""

    _failed_tests = []

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._failed_tests = []
        print("\n[AdvLogic] Running rewrite logic unit tests (8 total)...")

    def tearDown(self):
        if not self._outcome.success:
            AdvLogicTests._failed_tests.append(self._testMethodName)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        failed = len(cls._failed_tests)
        if failed == 0:
            print("[AdvLogic] All 8 rewrite logic tests passed.")
        else:
            print(f"[AdvLogic] {failed}/8 rewrite logic tests FAILED: {', '.join(cls._failed_tests)}")

    # ------------------------------------------------------------------ helpers

    def _proof(self, *bool_generics):
        """Return a fresh TwoSidedProof with bool generics for each label."""
        p = TwoSidedProof()
        for label in bool_generics:
            p.addGeneric(label, 'bool')
        return p

    def _apply(self, proof, src, sub):
        """Add src as the LHS premise, then attempt 'rewrite logic' with sub as
        the substitution targeting the whole expression (position 0).
        Returns (is_valid, errLog)."""
        proof.LHS.addProofLine(src)
        proof.LHS.addProofLine(src, "rewrite logic", 0, sub)
        return proof.LHS.errLog == [], list(proof.LHS.errLog)

    # ------------------------------------------------------------------ negative: non-logic root

    def test_non_logic_root_rejected(self):
        """Applying 'rewrite logic' to arithmetic (+ 2 3) -> 5 must fail with
        an error stating the selected expression is not a logic operation."""
        proof = TwoSidedProof()
        valid, errs = self._apply(proof, "(+ 2 3)", "5")
        self.assertFalse(valid, "Expected rejection for non-logic root (+ 2 3)")
        self.assertTrue(
            any("not a logic operation" in e for e in errs),
            f"Expected 'not a logic operation' in errors; got: {errs}"
        )

    # ------------------------------------------------------------------ negative: non-equivalent

    def test_non_equivalent_substitution_rejected(self):
        """(or #f #f) evaluates to #f, not #t. Substitution must be rejected
        with an error stating the result is not logically equivalent."""
        proof = TwoSidedProof()
        valid, errs = self._apply(proof, "(or #f #f)", "#t")
        self.assertFalse(valid, "Expected rejection: (or #f #f) is not equivalent to #t")
        self.assertTrue(
            any("not logically equivalent" in e for e in errs),
            f"Expected 'not logically equivalent' in errors; got: {errs}"
        )

    # ------------------------------------------------------------------ positive: ground (no symbols)

    def test_and_false_true_equiv_false(self):
        """(and #f #t) is logically equivalent to #f."""
        proof = TwoSidedProof()
        valid, errs = self._apply(proof, "(and #f #t)", "#f")
        self.assertTrue(valid, f"Expected valid; errors: {errs}")

    def test_or_false_false_equiv_false(self):
        """(or #f #f) is logically equivalent to #f."""
        proof = TwoSidedProof()
        valid, errs = self._apply(proof, "(or #f #f)", "#f")
        self.assertTrue(valid, f"Expected valid; errors: {errs}")

    def test_not_false_equiv_true(self):
        """(not #f) is logically equivalent to #t."""
        proof = TwoSidedProof()
        valid, errs = self._apply(proof, "(not #f)", "#t")
        self.assertTrue(valid, f"Expected valid; errors: {errs}")

    # ------------------------------------------------------------------ positive: propositional symbols

    def test_and_true_p_equiv_or_p_false(self):
        """(and #t p) is logically equivalent to (or p #f)."""
        proof = self._proof('p')
        valid, errs = self._apply(proof, "(and #t p)", "(or p #f)")
        self.assertTrue(valid, f"Expected valid; errors: {errs}")

    def test_demorgan_not_and(self):
        """De Morgan: (not (and p q)) is equivalent to (or (not p) (not q))."""
        proof = self._proof('p', 'q')
        valid, errs = self._apply(proof, "(not (and p q))", "(or (not p) (not q))")
        self.assertTrue(valid, f"Expected valid; errors: {errs}")

    # ------------------------------------------------------------------ positive: non-logic subexpressions

    def test_or_with_equality_subexpr(self):
        """(or (= (first '(3 4)) 3) #f) is equivalent to (and #t (= (first '(3 4)) 3)).
        The (= ...) compound has a non-logic root and must be abstracted as an
        opaque propositional symbol by AdvLogic, reused consistently in both
        expressions via the shared abstract_pairs list."""
        proof = TwoSidedProof()
        valid, errs = self._apply(
            proof,
            "(or (= (first '(3 4)) 3) #f)",
            "(and #t (= (first '(3 4)) 3))"
        )
        self.assertTrue(valid, f"Expected valid; errors: {errs}")
