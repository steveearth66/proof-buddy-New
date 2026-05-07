"""
Tests for the Value Mapping (High Support) feature.

support_value_mapping = True  → user may omit parameter mappings; backend infers them
                                 from the highlighted subexpression.
support_value_mapping = False → user must supply all parameter mappings explicitly (LOW mode).

Engine tests (ValueMappingEngineTests) verify the inference logic directly via
TwoSidedProof / ERProof without any HTTP layer or database access.

API tests (ValueMappingAPITests) test the full HTTP path: DB flag → view → engine.

Run individually:
  $env:PYTHONIOENCODING="utf-8"; py manage.py test equational_reasoning_api.test_value_mapping
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from expression_tree.ERProofEngine import TwoSidedProof

User = get_user_model()


class ValueMappingEngineTests(TestCase):
    """Engine-level tests for auto_infer parameter on addProofLine / applyRule.
    No ORM calls — pure expression-tree logic only."""

    # ------------------------------------------------------------------ helpers
    def _make_proof_with_udf(self):
        """Return a fresh TwoSidedProof with UDF (F a b) = (* a (* 2 b))."""
        p = TwoSidedProof()
        p.addUDF("(F a b)", "(INT,INT)>INT", "(* a (* 2 b))")
        self.assertEqual(p.errLog, [], f"UDF setup failed: {p.errLog}")
        return p

    # ------------------------------------------------------------------ UDF tests
    def test_udf_high_mode_no_params_succeeds(self):
        """In HIGH mode, 'apply F' with no params on (F 3 5) should succeed."""
        p = self._make_proof_with_udf()
        p.LHS.addProofLine("(F 3 5)")
        p.LHS.addProofLine("(F 3 5)", "apply F", 0, auto_infer=True)
        self.assertEqual(p.LHS.errLog, [], p.LHS.errLog)

    def test_udf_low_mode_no_params_fails(self):
        """In LOW mode, 'apply F' with no params should fail with an error."""
        p = self._make_proof_with_udf()
        p.LHS.addProofLine("(F 3 5)")
        p.LHS.addProofLine("(F 3 5)", "apply F", 0, auto_infer=False)
        self.assertNotEqual(p.LHS.errLog, [], "Expected error in LOW mode without params")

    def test_udf_high_mode_explicit_params_still_work(self):
        """In HIGH mode, explicit params should still be accepted."""
        p = self._make_proof_with_udf()
        p.LHS.addProofLine("(F 3 5)")
        p.LHS.addProofLine("(F 3 5)", "apply F with a=3, b=5", 0, auto_infer=True)
        self.assertEqual(p.LHS.errLog, [], p.LHS.errLog)

    def test_udf_high_mode_wrong_explicit_params_still_rejected(self):
        """In HIGH mode, wrong explicit params (a=99) should still be rejected."""
        p = self._make_proof_with_udf()
        p.LHS.addProofLine("(F 3 5)")
        p.LHS.addProofLine("(F 3 5)", "apply F with a=99, b=5", 0, auto_infer=True)
        self.assertNotEqual(p.LHS.errLog, [], "Wrong explicit params should still fail in HIGH mode")

    def test_udf_high_mode_applied_rule_contains_arrows(self):
        """In HIGH mode, the stored appliedRule should contain ↦ arrows."""
        p = self._make_proof_with_udf()
        p.LHS.addProofLine("(F 3 5)")
        p.LHS.addProofLine("(F 3 5)", "apply F", 0, auto_infer=True)
        self.assertEqual(p.LHS.errLog, [], p.LHS.errLog)
        last = p.LHS.proofLines[-1]
        self.assertIn("a\u21a63", last.appliedRule, f"Expected 'a↦3' in: {last.appliedRule}")
        self.assertIn("b\u21a65", last.appliedRule, f"Expected 'b↦5' in: {last.appliedRule}")

    def test_udf_high_mode_result_is_correct(self):
        """In HIGH mode the inferred result tree should match explicit-params result."""
        # Apply with inferred params
        p1 = self._make_proof_with_udf()
        p1.LHS.addProofLine("(F 3 5)")
        p1.LHS.addProofLine("(F 3 5)", "apply F", 0, auto_infer=True)
        self.assertEqual(p1.LHS.errLog, [], p1.LHS.errLog)
        result_inferred = str(p1.LHS.proofLines[-1].exprTree)
        # Apply with explicit params
        p2 = self._make_proof_with_udf()
        p2.LHS.addProofLine("(F 3 5)")
        p2.LHS.addProofLine("(F 3 5)", "apply F with a=3, b=5", 0, auto_infer=False)
        self.assertEqual(p2.LHS.errLog, [], p2.LHS.errLog)
        result_explicit = str(p2.LHS.proofLines[-1].exprTree)
        self.assertEqual(result_inferred, result_explicit,
                         f"Inferred result '{result_inferred}' != explicit result '{result_explicit}'")

    # ------------------------------------------------------------------ Axiom tests
    def test_axiom_first_cons_high_mode_no_params_succeeds(self):
        """In HIGH mode, 'rewrite first-cons' with no params on (first (cons 7 null)) should succeed."""
        p = TwoSidedProof()
        p.LHS.addProofLine("(first (cons 7 null))")
        p.LHS.addProofLine("(first (cons 7 null))", "rewrite first-cons", 0, auto_infer=True)
        self.assertEqual(p.LHS.errLog, [], p.LHS.errLog)

    def test_axiom_rest_cons_high_mode_no_params_succeeds(self):
        """In HIGH mode, 'rewrite rest-cons' with no params on (rest (cons 7 null)) should succeed."""
        p = TwoSidedProof()
        p.LHS.addProofLine("(rest (cons 7 null))")
        p.LHS.addProofLine("(rest (cons 7 null))", "rewrite rest-cons", 0, auto_infer=True)
        self.assertEqual(p.LHS.errLog, [], p.LHS.errLog)

    def test_axiom_null_q_cons_high_mode_no_params_succeeds(self):
        """In HIGH mode, 'rewrite null?-cons' with no params on (null? (cons 7 null)) should succeed."""
        p = TwoSidedProof()
        p.LHS.addProofLine("(null? (cons 7 null))")
        p.LHS.addProofLine("(null? (cons 7 null))", "rewrite null?-cons", 0, auto_infer=True)
        self.assertEqual(p.LHS.errLog, [], p.LHS.errLog)

    def test_axiom_low_mode_no_params_fails(self):
        """In LOW mode, 'rewrite first-cons' with no params should fail."""
        p = TwoSidedProof()
        p.LHS.addProofLine("(first (cons 7 null))")
        p.LHS.addProofLine("(first (cons 7 null))", "rewrite first-cons", 0, auto_infer=False)
        self.assertNotEqual(p.LHS.errLog, [], "Expected error in LOW mode without params for axiom")

    def test_axiom_high_mode_applied_rule_contains_arrows(self):
        """In HIGH mode, axiom appliedRule should contain ↦ arrows with inferred values."""
        p = TwoSidedProof()
        p.LHS.addProofLine("(first (cons 7 null))")
        p.LHS.addProofLine("(first (cons 7 null))", "rewrite first-cons", 0, auto_infer=True)
        self.assertEqual(p.LHS.errLog, [], p.LHS.errLog)
        last = p.LHS.proofLines[-1]
        self.assertIn("x\u21a67", last.appliedRule, f"Expected 'x↦7' in: {last.appliedRule}")
        self.assertIn("L\u21a6null", last.appliedRule, f"Expected 'L↦null' in: {last.appliedRule}")

    def test_axiom_high_mode_result_is_correct(self):
        """In HIGH mode the inferred result tree should match the explicit-params result."""
        p1 = TwoSidedProof()
        p1.LHS.addProofLine("(first (cons 7 null))")
        p1.LHS.addProofLine("(first (cons 7 null))", "rewrite first-cons", 0, auto_infer=True)
        self.assertEqual(p1.LHS.errLog, [], p1.LHS.errLog)
        result_inferred = str(p1.LHS.proofLines[-1].exprTree)
        p2 = TwoSidedProof()
        p2.LHS.addProofLine("(first (cons 7 null))")
        p2.LHS.addProofLine("(first (cons 7 null))", "rewrite first-cons x=7, L=null", 0, auto_infer=False)
        self.assertEqual(p2.LHS.errLog, [], p2.LHS.errLog)
        result_explicit = str(p2.LHS.proofLines[-1].exprTree)
        self.assertEqual(result_inferred, result_explicit,
                         f"Inferred result '{result_inferred}' != explicit result '{result_explicit}'")

    def test_zero_q_plus_high_mode_concrete_int_right(self):
        """In HIGH mode, 'rewrite zero?+' on (zero? (+ k 1)) infers a=1, k=k and succeeds."""
        p = TwoSidedProof()
        p.LHS.addGeneric('k', 'int')
        p.LHS.addProofLine("(zero? (+ k 1))")
        p.LHS.addProofLine("(zero? (+ k 1))", "rewrite zero?+", 0, auto_infer=True)
        self.assertEqual(p.LHS.errLog, [], p.LHS.errLog)
        self.assertEqual(str(p.LHS.proofLines[-1].exprTree), '#f')

    def test_zero_q_plus_high_mode_concrete_int_left(self):
        """In HIGH mode, 'rewrite zero?+' on (zero? (+ 1 k)) infers a=1, k=k and succeeds."""
        p = TwoSidedProof()
        p.LHS.addGeneric('k', 'int')
        p.LHS.addProofLine("(zero? (+ 1 k))")
        p.LHS.addProofLine("(zero? (+ 1 k))", "rewrite zero?+", 0, auto_infer=True)
        self.assertEqual(p.LHS.errLog, [], p.LHS.errLog)
        self.assertEqual(str(p.LHS.proofLines[-1].exprTree), '#f')

    def test_zero_q_plus_high_mode_inferred_matches_explicit(self):
        """In HIGH mode the inferred zero?+ result matches the explicit a=1, k=k result."""
        p1 = TwoSidedProof()
        p1.LHS.addGeneric('k', 'int')
        p1.LHS.addProofLine("(zero? (+ k 1))")
        p1.LHS.addProofLine("(zero? (+ k 1))", "rewrite zero?+", 0, auto_infer=True)
        self.assertEqual(p1.LHS.errLog, [], p1.LHS.errLog)
        result_inferred = str(p1.LHS.proofLines[-1].exprTree)
        p2 = TwoSidedProof()
        p2.LHS.addGeneric('k', 'int')
        p2.LHS.addProofLine("(zero? (+ k 1))")
        p2.LHS.addProofLine("(zero? (+ k 1))", "rewrite zero?+ a=1, k=k", 0, auto_infer=False)
        self.assertEqual(p2.LHS.errLog, [], p2.LHS.errLog)
        result_explicit = str(p2.LHS.proofLines[-1].exprTree)
        self.assertEqual(result_inferred, result_explicit,
                         f"Inferred result '{result_inferred}' != explicit result '{result_explicit}'")


class ValueMappingAPITests(TestCase):
    """
    API-level tests: verify that support_value_mapping=True on the EquationalProof
    causes the apply-rule endpoint to auto-infer parameter mappings from the
    highlighted node (no params needed in the rule string).
    """

    def setUp(self):
        from rest_framework.authtoken.models import Token
        from equational_reasoning_api.models import EquationalProof as _EqProof
        from django.core.cache import cache
        self._EqProof = _EqProof
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser_vm_api',
            email='vm_api@example.com',
            password='testpass123'
        )
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        try:
            cache.clear()
        except Exception:
            pass

    def tearDown(self):
        from django.core.cache import cache
        try:
            cache.clear()
        except Exception:
            pass

    # ------------------------------------------------------------------ helpers

    def _create_proof_with_flag(self, support_value_mapping: bool):
        """Create an EquationalProof in the DB and seed the cache with its id."""
        from equational_reasoning_api.views import save_equational_obj_to_cache
        from expression_tree.ERProofEngine import TwoSidedProof as _TSP
        proof = self._EqProof.objects.create(
            user=self.user,
            name='vm-api-test',
            tag='t1',
            lhs_goal='(+ 0 1)',
            rhs_goal='1',
            support_value_mapping=support_value_mapping,
        )
        # Seed the cache so apply_rule can find the proof_id and read support_value_mapping.
        save_equational_obj_to_cache(self.user, _TSP(), proof.id)
        return proof

    def _init_engine(self, lhs='(+ 0 1)', rhs='1', definitions=None):
        """Call set-current-proof to seed the engine cache."""
        resp = self.client.post('/api/v1/equational/set-current-proof', {
            'lhsPremise': lhs,
            'rhsPremise': rhs,
            'definitions': definitions or [],
        }, format='json')
        self.assertEqual(resp.status_code, 200, f"set-current-proof failed: {resp.data}")
        return resp

    def _apply(self, current_racket, rule, start_position=0):
        return self.client.post('/api/v1/equational/apply-rule', {
            'side': 'LHS',
            'currentRacket': current_racket,
            'rule': rule,
            'startPosition': start_position,
            'selectedNode': start_position,
            'lineNumber': 0,
        }, format='json')

    # ------------------------------------------------------------------ tests

    def test_high_mode_axiom_no_params_succeeds(self):
        """
        [POSITIVE] With support_value_mapping=True, 'rewrite first-cons' (no params)
        on '(first (cons 7 null))' should succeed via auto-inference.
        """
        self._create_proof_with_flag(support_value_mapping=True)
        self._init_engine(lhs='(first (cons 7 null))', rhs='7')
        resp = self._apply('(first (cons 7 null))', 'rewrite first-cons', start_position=0)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data.get('isValid'), f"Expected isValid=True, got: {resp.data}")

    def test_low_mode_axiom_no_params_fails(self):
        """
        [NEGATIVE] With support_value_mapping=False, 'rewrite first-cons' (no params)
        should fail — explicit mappings are required in LOW mode.
        """
        self._create_proof_with_flag(support_value_mapping=False)
        self._init_engine(lhs='(first (cons 7 null))', rhs='7')
        resp = self._apply('(first (cons 7 null))', 'rewrite first-cons', start_position=0)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertFalse(resp.data.get('isValid'), f"Expected isValid=False in LOW mode, got: {resp.data}")

    def test_high_mode_axiom_applied_rule_contains_arrows(self):
        """
        [POSITIVE] In HIGH mode the stored appliedRule should contain ↦ arrows
        (inferred mappings), even though the user typed no params.
        """
        self._create_proof_with_flag(support_value_mapping=True)
        self._init_engine(lhs='(first (cons 7 null))', rhs='7')
        resp = self._apply('(first (cons 7 null))', 'rewrite first-cons', start_position=0)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data.get('isValid'), resp.data)
        rule_stored = resp.data.get('rule', '')
        self.assertIn('\u21a6', rule_stored,
                      f"Expected ↦ in stored rule; got: {rule_stored!r}")

    def test_high_mode_explicit_params_still_accepted(self):
        """
        [POSITIVE] In HIGH mode, a rule with explicit params still succeeds —
        inference is skipped when params are already provided.
        """
        self._create_proof_with_flag(support_value_mapping=True)
        self._init_engine(lhs='(first (cons 7 null))', rhs='7')
        resp = self._apply('(first (cons 7 null))', 'rewrite first-cons x=7, L=null', start_position=0)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data.get('isValid'), f"Explicit params should still work in HIGH mode: {resp.data}")


class ValueMappingLemmaTests(TestCase):
    """
    API-level tests for lemma inference in HIGH mode.
    A lemma is a saved completed EquationalProof referenced by name.
    In HIGH mode the backend unifies the lemma's premise tree against the
    highlighted target node and infers the parameter mappings automatically.
    """

    def setUp(self):
        from rest_framework.authtoken.models import Token
        from equational_reasoning_api.models import EquationalProof as _EqProof
        from django.core.cache import cache
        self._EqProof = _EqProof
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser_vm_lemma',
            email='vm_lemma@example.com',
            password='testpass123'
        )
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        try:
            cache.clear()
        except Exception:
            pass

    def tearDown(self):
        from django.core.cache import cache
        try:
            cache.clear()
        except Exception:
            pass

    def _create_lemma_proof(self, name, lhs, rhs):
        """Create a completed EquationalProof to act as a saved lemma."""
        return self._EqProof.objects.create(
            user=self.user,
            name=name,
            tag='lemma',
            lhs_goal=lhs,
            rhs_goal=rhs,
            is_complete=True,
        )

    def _create_working_proof(self, support_value_mapping):
        """Create the active proof and seed its cache entry."""
        from equational_reasoning_api.views import save_equational_obj_to_cache
        from expression_tree.ERProofEngine import TwoSidedProof as _TSP
        proof = self._EqProof.objects.create(
            user=self.user,
            name='vm-lemma-working',
            tag='t',
            lhs_goal='(+ 5 0)',
            rhs_goal='5',
            support_value_mapping=support_value_mapping,
        )
        save_equational_obj_to_cache(self.user, _TSP(), proof.id)
        return proof

    def _init_engine(self, lhs='(+ 5 0)', rhs='5'):
        resp = self.client.post('/api/v1/equational/set-current-proof', {
            'lhsPremise': lhs,
            'rhsPremise': rhs,
            'definitions': [],
        }, format='json')
        self.assertEqual(resp.status_code, 200, f"set-current-proof failed: {resp.data}")
        return resp

    def _apply(self, current_racket, rule, start_position=0):
        return self.client.post('/api/v1/equational/apply-rule', {
            'side': 'LHS',
            'currentRacket': current_racket,
            'rule': rule,
            'startPosition': start_position,
            'selectedNode': start_position,
            'lineNumber': 0,
        }, format='json')

    # ------------------------------------------------------------------ tests

    def test_high_mode_lemma_no_params_succeeds(self):
        """
        [POSITIVE] With support_value_mapping=True, 'apply plus-zero' (no params)
        on '(+ 5 0)' should succeed when plus-zero is a completed proof
        with lhs_goal='(+ n 0)', rhs_goal='n'.
        """
        self._create_lemma_proof('plus-zero', '(+ n 0)', 'n')
        self._create_working_proof(support_value_mapping=True)
        self._init_engine(lhs='(+ 5 0)', rhs='5')
        resp = self._apply('(+ 5 0)', 'apply plus-zero', start_position=0)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data.get('isValid'), f"Expected isValid=True, got: {resp.data}")

    def test_low_mode_lemma_no_params_fails(self):
        """
        [NEGATIVE] With support_value_mapping=False, 'apply plus-zero' (no params)
        should fail — explicit mappings required in LOW mode.
        """
        self._create_lemma_proof('plus-zero', '(+ n 0)', 'n')
        self._create_working_proof(support_value_mapping=False)
        self._init_engine(lhs='(+ 5 0)', rhs='5')
        resp = self._apply('(+ 5 0)', 'apply plus-zero', start_position=0)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertFalse(resp.data.get('isValid'), f"Expected isValid=False in LOW mode, got: {resp.data}")

    def test_high_mode_lemma_applied_rule_contains_arrows(self):
        """
        [POSITIVE] In HIGH mode the stored rule should contain ↦ with the inferred value.
        """
        self._create_lemma_proof('plus-zero', '(+ n 0)', 'n')
        self._create_working_proof(support_value_mapping=True)
        self._init_engine(lhs='(+ 5 0)', rhs='5')
        resp = self._apply('(+ 5 0)', 'apply plus-zero', start_position=0)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data.get('isValid'), resp.data)
        rule_stored = resp.data.get('rule', '')
        self.assertIn('\u21a6', rule_stored,
                      f"Expected ↦ in stored rule; got: {rule_stored!r}")

    def test_high_mode_lemma_explicit_params_still_accepted(self):
        """
        [POSITIVE] In HIGH mode, explicit params on a lemma still work —
        inference is skipped when params are already provided.
        """
        self._create_lemma_proof('plus-zero', '(+ n 0)', 'n')
        self._create_working_proof(support_value_mapping=True)
        self._init_engine(lhs='(+ 5 0)', rhs='5')
        resp = self._apply('(+ 5 0)', 'apply plus-zero n=5', start_position=0)
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data.get('isValid'),
                        f"Explicit params should still work in HIGH mode: {resp.data}")
