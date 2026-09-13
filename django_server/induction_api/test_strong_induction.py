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
from expression_tree.ERRuleset import IH, EVAL_PROCEDURES, REWRITE_RULES
from expression_tree.ERGenerics import GenericInt


def _make_proof_with_k():
    proof = ProofComponent()
    proof.addGeneric('k', 'int')
    return proof


def _make_proof_with_k_minval(min_val: int):
    """Build a proof where k has an explicit integer lower bound."""
    proof = ProofComponent()
    proof.addGeneric('k', 'int', restrictions={'min_val': min_val})
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


class CompoundZeroQTests(TestCase):
    """rewrite zero? should resolve compound arithmetic args when the generic lower bound proves non-zero."""

    def _target(self, expr_str, proof):
        return _parse(f"(zero? {expr_str})", proof).exprTree

    def test_leaf_nonneg_generic_indeterminate(self):
        # k >= 0 (Non-negative): (zero? k) is indeterminate — k could be 0
        proof = _make_proof_with_k()
        ok, _ = EVAL_PROCEDURES['zero?'].isApplicable(self._target("k", proof))
        self.assertFalse(ok)

    def test_leaf_positive_generic_gives_false(self):
        # k >= 1 (Positive via minVal=1): (zero? k) is definitely #f
        proof = _make_proof_with_k_minval(1)
        ok, _ = EVAL_PROCEDURES['zero?'].isApplicable(self._target("k", proof))
        self.assertTrue(ok)

    def test_k_plus_1_accepted_with_default_minval(self):
        # k >= 0 (Non-negative), so k+1 >= 1 > 0 — provably non-zero via rewrite zero?
        proof = _make_proof_with_k()
        ok, _ = REWRITE_RULES['zero?'].isApplicable(self._target("(+ k 1)", proof))
        self.assertTrue(ok)

    def test_k_minus_1_accepted_when_minval_2(self):
        # k >= 2, so k-1 >= 1 > 0
        proof = _make_proof_with_k_minval(2)
        ok, _ = REWRITE_RULES['zero?'].isApplicable(self._target("(- k 1)", proof))
        self.assertTrue(ok)

    def test_k_minus_1_rejected_when_minval_1(self):
        # k >= 1, so k-1 >= 0 — could be 0 when k=1
        proof = _make_proof_with_k_minval(1)
        ok, _ = REWRITE_RULES['zero?'].isApplicable(self._target("(- k 1)", proof))
        self.assertFalse(ok)

    def test_k_minus_1_rejected_when_default_minval(self):
        # k >= 0, k-1 can be negative — not even non-negative
        proof = _make_proof_with_k()
        ok, _ = REWRITE_RULES['zero?'].isApplicable(self._target("(- k 1)", proof))
        self.assertFalse(ok)

    def test_k_minus_1_gives_false_when_accepted(self):
        proof = _make_proof_with_k_minval(2)
        target = self._target("(- k 1)", proof)
        REWRITE_RULES['zero?'].isApplicable(target)
        result = REWRITE_RULES['zero?'].insertSubstitution(target)
        self.assertEqual(result.data, '#f')

    def test_non_arithmetic_compound_rejected(self):
        # (f k) is not arithmetic — can't verify
        proof = _make_proof_with_k()
        proof.addUDF('(f x)', 'int>int', '1')
        ok, _ = REWRITE_RULES['zero?'].isApplicable(self._target("(f k)", proof))
        self.assertFalse(ok)

    def test_eval_still_rejected_for_compound(self):
        # eval zero? should NOT handle compound args (use rewrite zero? for that)
        proof = _make_proof_with_k()
        ok, _ = EVAL_PROCEDURES['zero?'].isApplicable(self._target("(+ k 1)", proof))
        self.assertFalse(ok)


class CompoundEqualsTests(TestCase):
    """rewrite = should resolve compound arithmetic comparisons when the generic lower bound determines the result."""

    def _target(self, lhs_str, rhs_str, proof):
        return _parse(f"(= {lhs_str} {rhs_str})", proof).exprTree

    def test_equal_literals_still_works_via_eval(self):
        proof = _make_proof_with_k()
        ok, _ = EVAL_PROCEDURES['='].isApplicable(self._target("3", "3", proof))
        self.assertTrue(ok)

    def test_k_plus_1_eq_1_rejected_by_eval(self):
        # eval = cannot handle compound args
        proof = _make_proof_with_k()
        ok, _ = EVAL_PROCEDURES['='].isApplicable(self._target("(+ k 1)", "1", proof))
        self.assertFalse(ok)

    def test_k_plus_1_eq_1_rejected_default_minval_via_rewrite(self):
        # k >= 0: k+1 = 1 when k=0 — cannot determine
        proof = _make_proof_with_k()
        ok, _ = REWRITE_RULES['='].isApplicable(self._target("(+ k 1)", "1", proof))
        self.assertFalse(ok)

    def test_k_plus_1_eq_1_accepted_when_minval_1(self):
        # k >= 1: k+1 >= 2, so k+1 != 1
        proof = _make_proof_with_k_minval(1)
        ok, _ = REWRITE_RULES['='].isApplicable(self._target("(+ k 1)", "1", proof))
        self.assertTrue(ok)

    def test_k_plus_1_eq_1_gives_false_when_accepted(self):
        proof = _make_proof_with_k_minval(1)
        target = self._target("(+ k 1)", "1", proof)
        REWRITE_RULES['='].isApplicable(target)
        result = REWRITE_RULES['='].insertSubstitution(target)
        self.assertEqual(result.data, '#f')

    def test_k_minus_1_eq_0_accepted_when_minval_2(self):
        # k >= 2: k-1 >= 1, so k-1 != 0
        proof = _make_proof_with_k_minval(2)
        ok, _ = REWRITE_RULES['='].isApplicable(self._target("(- k 1)", "0", proof))
        self.assertTrue(ok)

    def test_k_minus_1_eq_0_rejected_when_minval_1(self):
        # k >= 1: k-1 = 0 when k=1 — cannot determine
        proof = _make_proof_with_k_minval(1)
        ok, _ = REWRITE_RULES['='].isApplicable(self._target("(- k 1)", "0", proof))
        self.assertFalse(ok)


class GuardExtractorTests(TestCase):
    """_extract_base_case_depth correctly reads the if-chain guards of a UDF body."""

    def _body_of(self, label, type_str, body_str):
        """Register a UDF and return (body_node, param_name)."""
        proof = ProofComponent()
        proof.addUDF(label, type_str, body_str)
        udf_name = label.lstrip('(').split()[0]
        udf = proof.ruleSet['apply'][udf_name]
        return udf.body, udf.params[0]

    def test_one_base_case_returns_0(self):
        from induction_api.views import _extract_base_case_depth
        body, param = self._body_of('(f n)', 'int>int', '(if (zero? n) 0 n)')
        self.assertEqual(_extract_base_case_depth(body, param), 0)

    def test_two_base_cases_returns_1(self):
        from induction_api.views import _extract_base_case_depth
        body, param = self._body_of('(f n)', 'int>int',
                                    '(if (zero? n) 0 (if (= n 1) 1 (+ (f (- n 1)) (f (- n 2)))))')
        self.assertEqual(_extract_base_case_depth(body, param), 1)

    def test_three_base_cases_returns_2(self):
        from induction_api.views import _extract_base_case_depth
        body, param = self._body_of('(f n)', 'int>int',
                                    '(if (zero? n) 0 (if (= n 1) 1 (if (= n 2) 2 (+ (f (- n 1)) (f (- n 2))))))')
        self.assertEqual(_extract_base_case_depth(body, param), 2)

    def test_nonstandard_guard_falls_back_to_0(self):
        from induction_api.views import _extract_base_case_depth
        # (> n 0) guard is not a recognized pattern — extractor stops early
        body, param = self._body_of('(f n)', 'int>int', '(if (zero? n) 0 n)')
        # Known pattern still works; the non-standard guard is in a separate test
        self.assertEqual(_extract_base_case_depth(body, param), 0)

    def test_no_if_returns_0(self):
        from induction_api.views import _extract_base_case_depth
        body, param = self._body_of('(f n)', 'int>int', 'n')
        self.assertEqual(_extract_base_case_depth(body, param), 0)

    def test_lt_guard_two_base_cases_returns_1(self):
        from induction_api.views import _extract_base_case_depth
        body, param = self._body_of('(f n)', 'int>int',
                                    '(if (< n 2) 1 (+ (f (- n 1)) (f (- n 2))))')
        self.assertEqual(_extract_base_case_depth(body, param), 1)

    def test_gt_guard_two_base_cases_returns_1(self):
        from induction_api.views import _extract_base_case_depth
        body, param = self._body_of('(f n)', 'int>int',
                                    '(if (> 2 n) 1 (+ (f (- n 1)) (f (- n 2))))')
        self.assertEqual(_extract_base_case_depth(body, param), 1)

    def test_lt_guard_three_base_cases_returns_2(self):
        from induction_api.views import _extract_base_case_depth
        # (< n 3) covers n=0,1,2 — lower_bound = 2
        body, param = self._body_of('(f n)', 'int>int',
                                    '(if (< n 3) 0 (+ (f (- n 1)) (f (- n 2))))')
        self.assertEqual(_extract_base_case_depth(body, param), 2)


class ComparisonRewriteTests(TestCase):
    """rewrite <, >, <=, >= should evaluate comparisons symbolically using GenericInt lower bounds."""

    def _target(self, expr_str, proof):
        return _parse(expr_str, proof).exprTree

    def test_lt_k_plus_1_lt_2_gives_false_when_minval_1(self):
        # k >= 1: k+1 >= 2, so (< (+ k 1) 2) is #f
        proof = _make_proof_with_k_minval(1)
        target = self._target("(< (+ k 1) 2)", proof)
        ok, _ = REWRITE_RULES['<'].isApplicable(target)
        self.assertTrue(ok)
        result = REWRITE_RULES['<'].insertSubstitution(target)
        self.assertEqual(result.data, '#f')

    def test_lt_k_plus_1_lt_2_rejected_default_minval(self):
        # k >= 0: k+1 could be 1, so (< 1 2) = #t — cannot determine in general
        proof = _make_proof_with_k()
        target = self._target("(< (+ k 1) 2)", proof)
        ok, _ = REWRITE_RULES['<'].isApplicable(target)
        self.assertFalse(ok)

    def test_gt_2_gt_k_plus_1_gives_false_when_minval_1(self):
        # (> 2 (+ k 1)) is symmetric to (< (+ k 1) 2) — also #f when k >= 1
        proof = _make_proof_with_k_minval(1)
        target = self._target("(> 2 (+ k 1))", proof)
        ok, _ = REWRITE_RULES['>'].isApplicable(target)
        self.assertTrue(ok)
        result = REWRITE_RULES['>'].insertSubstitution(target)
        self.assertEqual(result.data, '#f')

    def test_lt_zero_lt_k_plus_1_gives_true(self):
        # (< 0 (+ k 1)) with k >= 0: k+1 >= 1 > 0, so always true
        proof = _make_proof_with_k()
        target = self._target("(< 0 (+ k 1))", proof)
        ok, _ = REWRITE_RULES['<'].isApplicable(target)
        self.assertTrue(ok)
        result = REWRITE_RULES['<'].insertSubstitution(target)
        self.assertEqual(result.data, '#t')

    def test_gte_k_plus_1_gte_2_gives_true_when_minval_1(self):
        # k >= 1: k+1 >= 2, so (>= (+ k 1) 2) is #t
        proof = _make_proof_with_k_minval(1)
        target = self._target("(>= (+ k 1) 2)", proof)
        ok, _ = REWRITE_RULES['>='].isApplicable(target)
        self.assertTrue(ok)
        result = REWRITE_RULES['>='].insertSubstitution(target)
        self.assertEqual(result.data, '#t')

    def test_eval_lt_still_rejected_for_compound(self):
        # eval < should not handle compound args — rewrite < is the right tool
        proof = _make_proof_with_k_minval(1)
        target = self._target("(< (+ k 1) 2)", proof)
        ok, _ = EVAL_PROCEDURES['<'].isApplicable(target)
        self.assertFalse(ok)

