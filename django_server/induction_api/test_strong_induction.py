"""
Tests for Strong Induction IH support.

The IH rule should accept "apply IH" on any node that structurally matches the
induction hypothesis with the leap variable k replaced by an arithmetic expression
e where e <= k is provable via sympy.  Exact (k == k) matches remain as before.

Run individually:
  $env:PYTHONIOENCODING="utf-8"; py manage.py test induction_api.test_strong_induction
"""

from django.test import TestCase
from expression_tree.ERProofEngine import ProofComponent, ERProofLine
from expression_tree.ERRuleset import IH


def _make_proof_with_k():
    proof = ProofComponent()
    proof.addGeneric('k', 'int')
    return proof


def _parse(expr, proof):
    return ERProofLine(expr, ruleDict=proof.ruleSet, generics=proof.generics)


class BackwardCompatTests(TestCase):
    """Exact-match behaviour must be unchanged after the feature is added."""

    def setUp(self):
        proof = _make_proof_with_k()
        lhs = _parse("(+ k 5)", proof)
        rhs = _parse("(+ 5 k)", proof)
        self.ih = IH(lhs.exprTree, rhs.exprTree, lvar='k')
        self.lhs_tree = lhs.exprTree
        self.rhs_tree = rhs.exprTree

    def test_exact_lhs_match_accepted(self):
        ok, _ = self.ih.isApplicable(self.lhs_tree)
        self.assertTrue(ok)

    def test_exact_rhs_match_accepted(self):
        ok, _ = self.ih.isApplicable(self.rhs_tree)
        self.assertTrue(ok)

    def test_params_still_rejected(self):
        ok, msg = self.ih.isApplicable(self.lhs_tree, rawParams=['k=1'])
        self.assertFalse(ok)
        self.assertIn("no parameters", msg)

    def test_exact_lhs_substitution_returns_rhs(self):
        self.ih.isApplicable(self.lhs_tree)
        result = self.ih.insertSubstitution(self.lhs_tree)
        self.assertEqual(str(result), str(self.rhs_tree))

    def test_exact_rhs_substitution_returns_lhs(self):
        self.ih.isApplicable(self.rhs_tree)
        result = self.ih.insertSubstitution(self.rhs_tree)
        self.assertEqual(str(result), str(self.lhs_tree))


class StrongIHAcceptanceTests(TestCase):
    """Expressions e <= k substituted for k should be accepted."""

    def setUp(self):
        self.proof = _make_proof_with_k()
        lhs = _parse("(+ k 5)", self.proof)
        rhs = _parse("(+ 5 k)", self.proof)
        self.ih = IH(lhs.exprTree, rhs.exprTree, lvar='k')

    def test_k_minus_1_accepted(self):
        target = _parse("(+ (- k 1) 5)", self.proof)
        ok, _ = self.ih.isApplicable(target.exprTree)
        self.assertTrue(ok)

    def test_k_minus_3_accepted(self):
        target = _parse("(+ (- k 3) 5)", self.proof)
        ok, _ = self.ih.isApplicable(target.exprTree)
        self.assertTrue(ok)

    def test_constant_zero_accepted(self):
        # 0 <= k for any positive integer k
        target = _parse("(+ 0 5)", self.proof)
        ok, _ = self.ih.isApplicable(target.exprTree)
        self.assertTrue(ok)

    def test_lhs_substitution_correct(self):
        # (+ (- k 1) 5) matches LHS; result should be (+ 5 (- k 1))
        target = _parse("(+ (- k 1) 5)", self.proof)
        self.ih.isApplicable(target.exprTree)
        result = self.ih.insertSubstitution(target.exprTree)
        self.assertEqual(str(result), "(+ 5 (- k 1))")

    def test_rhs_substitution_correct(self):
        # (+ 5 (- k 1)) matches RHS; result should be (+ (- k 1) 5)
        target = _parse("(+ 5 (- k 1))", self.proof)
        self.ih.isApplicable(target.exprTree)
        result = self.ih.insertSubstitution(target.exprTree)
        self.assertEqual(str(result), "(+ (- k 1) 5)")


class StrongIHRejectionTests(TestCase):
    """Expressions e > k or unverifiable e must be rejected with the right messages."""

    def setUp(self):
        self.proof = _make_proof_with_k()
        lhs = _parse("(+ k 5)", self.proof)
        rhs = _parse("(+ 5 k)", self.proof)
        self.ih = IH(lhs.exprTree, rhs.exprTree, lvar='k')

    def test_k_plus_1_rejected(self):
        target = _parse("(+ (+ k 1) 5)", self.proof)
        ok, msg = self.ih.isApplicable(target.exprTree)
        self.assertFalse(ok)
        self.assertIn("cannot verify", msg)

    def test_k_plus_1_message_names_expression(self):
        target = _parse("(+ (+ k 1) 5)", self.proof)
        _, msg = self.ih.isApplicable(target.exprTree)
        self.assertIn("(+ k 1)", msg)

    def test_nonmath_expression_rejected(self):
        # Register a UDF so (f k) parses; e = (f k) is not verifiable as <= k
        self.proof.addUDF('(f x)', 'int>int', '1')
        target = _parse("(+ (f k) 5)", self.proof)
        ok, msg = self.ih.isApplicable(target.exprTree)
        self.assertFalse(ok)
        self.assertIn("cannot verify", msg)

    def test_no_structural_match_uses_original_message(self):
        # Completely different structure — no k-substitution possible
        target = _parse("(* k 5)", self.proof)
        ok, msg = self.ih.isApplicable(target.exprTree)
        self.assertFalse(ok)
        self.assertIn("does not match", msg)

    def test_no_lvar_set_rejects_substitution(self):
        # lvar=None means the IH has no leap variable context; only exact match allowed
        proof2 = _make_proof_with_k()
        lhs2 = _parse("(+ k 5)", proof2)
        rhs2 = _parse("(+ 5 k)", proof2)
        ih_no_lvar = IH(lhs2.exprTree, rhs2.exprTree)
        target = _parse("(+ (- k 1) 5)", proof2)
        ok, msg = ih_no_lvar.isApplicable(target.exprTree)
        self.assertFalse(ok)
        self.assertIn("does not match", msg)

    def test_inconsistent_lvar_binding_rejected(self):
        # Template (+ k k); target (+ (- k 1) (- k 2)) — k maps to two different values
        proof3 = _make_proof_with_k()
        lhs3 = _parse("(+ k k)", proof3)
        rhs3 = _parse("(* 2 k)", proof3)
        ih3 = IH(lhs3.exprTree, rhs3.exprTree, lvar='k')
        target = _parse("(+ (- k 1) (- k 2))", proof3)
        ok, _ = ih3.isApplicable(target.exprTree)
        self.assertFalse(ok)
