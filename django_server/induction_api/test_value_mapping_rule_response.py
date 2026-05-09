"""
Tests that the induction apply-rule API response includes the ``rule`` field
containing ↦ annotations when support_value_mapping (High support) is enabled.

Regression test for: value_mapping implemented commit (bf37f486) updated the
frontend to use ``fullRacket.rule || ruleFromFooter`` but the induction
``apply_rule`` view never included ``"rule"`` in its Response payload, so the
rule column always displayed the raw un-annotated footer text entered by the
user rather than the inferred ``"apply sumList L↦null"`` / ``"rewrite zero?+ …"``
form that shows students the parameter mappings.

Two cases exercised:
  - UDF apply   : ``apply sumList`` on ``(sumList null)`` — tests the DEFINITION
                  branch of ``_infer_params_for_rule``
  - Axiom rewrite: ``rewrite zero?+`` on ``(zero? (+ k 1))`` — tests the AXIOM
                  branch (requires a generic for ``k``)

Each case has a POSITIVE test (HIGH mode → ``↦`` in response rule) and a
NEGATIVE test (LOW mode → response rule equals the plain rule the user typed,
no ``↦``).

Run individually:
  $env:PYTHONIOENCODING="utf-8"; py manage.py test induction_api.test_value_mapping_rule_response
"""

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from induction_api.models import InductionProof
from induction_api.views import save_induction_obj_to_cache
from expression_tree.IndProofs import IndProof

User = get_user_model()

_START_URL = '/api/v1/induction/start-induction-proof'
_SET_URL   = '/api/v1/induction/set-current-proof'
_APPLY_URL = '/api/v1/induction/apply-rule'


class InductionValueMappingRuleResponseTests(TransactionTestCase):
    """
    Verify that the ``rule`` key in the induction apply-rule response carries
    the ↦-annotated rule string produced by HIGH support auto-inference,
    not just the raw footer text the user typed.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='vm_ind_tester',
            email='vm_ind@example.com',
            password='testpass123',
        )
        self.client.force_authenticate(user=self.user)
        try:
            cache.clear()
        except Exception:
            pass

    def tearDown(self):
        try:
            cache.clear()
        except Exception:
            pass

    # ------------------------------------------------------------------ helpers

    def _set_support_value_mapping(self, proof_id, enabled: bool):
        """Directly flip support_value_mapping on the DB row."""
        InductionProof.objects.filter(id=proof_id).update(
            support_value_mapping=enabled
        )

    def _start_list_proof(self):
        """
        Create a list-induction proof for sumList.
        Returns proof_id.  The UDF sumList is added via the definitions payload
        of set-current-proof.
        """
        resp = self.client.post(_START_URL, {
            'proof_name': 'sumList test',
            'proof_tag':  'vm-ind-test',
            'lhs_leap_goal':  '(sumList n)',
            'rhs_leap_goal':  '(sumList n)',
            'lhs_anchor_goal': '(sumList n)',
            'rhs_anchor_goal': '0',
            'induction_variable': 'n',
            'anchor_value':       'null',
            'leap_variable':      'k',
            'induction_type':     'lists',
            'inductive_hypothesis_lhs': '(sumList k)',
            'inductive_hypothesis_rhs': '(sumList k)',
        }, format='json')
        self.assertEqual(resp.status_code, 201, f"start-induction-proof failed: {resp.data}")
        return resp.data['proof_id']

    def _init_engine_list(self):
        """Call set-current-proof with the sumList UDF definition."""
        resp = self.client.post(_SET_URL, {
            'struct':    'list',
            'ivar':      'n',
            'aval':      'null',
            'lvar':      'k',
            'lhsPremise': '(sumList n)',
            'rhsPremise': '(sumList n)',
            'definitions': [
                {
                    'label':      '(sumList L)',
                    'type':       'LIST>INT',
                    'expression': '(if (null? L) 0 (+ (first L) (sumList (rest L))))',
                    'notes':      '',
                }
            ],
        }, format='json')
        self.assertEqual(resp.status_code, 201, f"set-current-proof failed: {resp.data}")

    def _start_int_proof(self):
        """Create an integer-induction proof for the zero?+ axiom test. Returns proof_id."""
        resp = self.client.post(_START_URL, {
            'proof_name': 'zero?+ test',
            'proof_tag':  'vm-ind-test-int',
            'lhs_leap_goal':  '(zero? (+ n 1))',
            'rhs_leap_goal':  '#f',
            'lhs_anchor_goal': '(zero? (+ n 1))',
            'rhs_anchor_goal': '#f',
            'induction_variable': 'n',
            'anchor_value':       '0',
            'leap_variable':      'k',
            'induction_type':     'integers',
            'inductive_hypothesis_lhs': '(zero? (+ k 1))',
            'inductive_hypothesis_rhs': '#f',
        }, format='json')
        self.assertEqual(resp.status_code, 201, f"start-induction-proof failed: {resp.data}")
        return resp.data['proof_id']

    def _init_engine_int(self):
        """Call set-current-proof for the integer proof."""
        resp = self.client.post(_SET_URL, {
            'struct':    'int',
            'ivar':      'n',
            'aval':      '0',
            'lvar':      'k',
            'lhsPremise': '(zero? (+ n 1))',
            'rhsPremise': '#f',
            'definitions': [],
        }, format='json')
        self.assertEqual(resp.status_code, 201, f"set-current-proof failed: {resp.data}")

    def _apply(self, case, side, racket, rule, start_position=0):
        return self.client.post(_APPLY_URL, {
            'case':           case,
            'side':           side,
            'currentRacket':  racket,
            'rule':           rule,
            'startPosition':  start_position,
            'selectedNode':   start_position,
        }, format='json')

    # ================================================================== UDF tests

    def test_udf_high_mode_response_rule_contains_arrows(self):
        """
        [POSITIVE] HIGH mode, ``apply sumList`` on ``(sumList null)`` with no
        explicit params → response ``rule`` must contain a ↦ annotation.
        """
        proof_id = self._start_list_proof()
        self._set_support_value_mapping(proof_id, enabled=True)
        self._init_engine_list()

        resp = self._apply('base', 'LHS', '(sumList null)', 'apply sumList')
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data.get('isValid'),
                        f"Expected isValid=True in HIGH mode; got: {resp.data}")
        rule_returned = resp.data.get('rule', '')
        self.assertIn('\u21a6', rule_returned,
                      f"Expected ↦ in response rule (HIGH mode); got: {rule_returned!r}")

    def test_udf_low_mode_response_rule_has_no_arrows(self):
        """
        [NEGATIVE] LOW mode, ``apply sumList L=null`` with explicit params →
        response ``rule`` must NOT contain ↦ (it stores the raw rule string as
        typed, without auto-inferred annotation).
        """
        proof_id = self._start_list_proof()
        self._set_support_value_mapping(proof_id, enabled=False)
        self._init_engine_list()

        resp = self._apply('base', 'LHS', '(sumList null)', 'apply sumList L=null')
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data.get('isValid'),
                        f"Expected isValid=True with explicit param in LOW mode; got: {resp.data}")
        rule_returned = resp.data.get('rule', '')
        self.assertNotIn('\u21a6', rule_returned,
                         f"Expected no ↦ in response rule (LOW mode); got: {rule_returned!r}")

    def test_udf_high_mode_response_rule_key_present(self):
        """
        [POSITIVE] The response JSON must always include the ``rule`` key
        (not just implicitly return None/missing), even in HIGH mode.
        """
        proof_id = self._start_list_proof()
        self._set_support_value_mapping(proof_id, enabled=True)
        self._init_engine_list()

        resp = self._apply('base', 'LHS', '(sumList null)', 'apply sumList')
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertIn('rule', resp.data,
                      "Response JSON must include the 'rule' key")

    # ================================================================== Axiom tests

    def test_axiom_high_mode_response_rule_contains_arrows(self):
        """
        [POSITIVE] HIGH mode, ``rewrite zero?+`` on ``(zero? (+ k 1))`` with no
        explicit params → response ``rule`` must contain a ↦ annotation.
        """
        proof_id = self._start_int_proof()
        self._set_support_value_mapping(proof_id, enabled=True)
        self._init_engine_int()

        resp = self._apply('leap', 'LHS', '(zero? (+ k 1))', 'rewrite zero?+')
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data.get('isValid'),
                        f"Expected isValid=True in HIGH mode; got: {resp.data}")
        rule_returned = resp.data.get('rule', '')
        self.assertIn('\u21a6', rule_returned,
                      f"Expected ↦ in response rule (HIGH mode); got: {rule_returned!r}")

    def test_axiom_low_mode_response_rule_has_no_arrows(self):
        """
        [NEGATIVE] LOW mode, ``rewrite zero?+ a=1, k=k`` with explicit params →
        response ``rule`` must NOT contain ↦.
        """
        proof_id = self._start_int_proof()
        self._set_support_value_mapping(proof_id, enabled=False)
        self._init_engine_int()

        resp = self._apply('leap', 'LHS', '(zero? (+ k 1))', 'rewrite zero?+ a=1, k=k')
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data.get('isValid'),
                        f"Expected isValid=True with explicit params in LOW mode; got: {resp.data}")
        rule_returned = resp.data.get('rule', '')
        self.assertNotIn('\u21a6', rule_returned,
                         f"Expected no ↦ in response rule (LOW mode); got: {rule_returned!r}")

    def test_axiom_high_mode_response_rule_key_present(self):
        """
        [POSITIVE] The response JSON must always include the ``rule`` key for
        axiom rules too.
        """
        proof_id = self._start_int_proof()
        self._set_support_value_mapping(proof_id, enabled=True)
        self._init_engine_int()

        resp = self._apply('leap', 'LHS', '(zero? (+ k 1))', 'rewrite zero?+')
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertIn('rule', resp.data,
                      "Response JSON must include the 'rule' key for axiom rules")
