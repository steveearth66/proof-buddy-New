"""
Tests for the validate_hidden_field endpoint in induction_api.

Mirrors equational_reasoning_api/test_validate_hidden_field.py.
Uses TransactionTestCase and API-driven setup (matching other induction tests)
to ensure the engine cache is fully initialised before validate_hidden_field
is exercised.

Run:
    $env:PYTHONIOENCODING="utf-8"; py manage.py test induction_api.test_validate_hidden_field
"""

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.core.cache import cache

from induction_api.models import InductionProof, InductionProofLine
from expression_tree.ERProofEngine import ERProof
from expression_tree.ERCommon import makeJson

User = get_user_model()

_URL = '/api/v1/induction/validate-hidden-field'

_START_DATA = {
    'proof_name': 'Hidden Field Test',
    'proof_tag': 'hf-test',
    'lhs_leap_goal': '(+ n 1)',
    'rhs_leap_goal': '(+ 1 n)',
    'lhs_anchor_goal': '(+ 0 1)',
    'rhs_anchor_goal': '(+ 1 0)',
    'induction_variable': 'n',
    'anchor_value': '0',
    'leap_variable': 'k',
    'induction_type': 'integers',
    'inductive_hypothesis_lhs': '(+ k 1)',
    'inductive_hypothesis_rhs': '(+ 1 k)',
}

_ENGINE_DATA = {
    'struct': 'int',
    'ivar': 'n',
    'aval': '0',
    'lvar': 'k',
    'lhsPremise': '(+ n 1)',
    'rhsPremise': '(+ 1 n)',
    'definitions': [],
}


def _build_json_tree(racket_str):
    """Return the json_tree dict for a racket expression."""
    p = ERProof()
    p.addProofLine(racket_str)
    if p.errLog or not p.proofLines:
        return {}
    return makeJson(p.proofLines[-1].exprTree)


class _IndHiddenFieldBase(TransactionTestCase):
    """Shared setUp: start proof, initialise engine, apply one rule on base/LHS."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='ind_hf_user', email='ind@test.com', password='pass'
        )
        self.client.force_authenticate(user=self.user)

        resp = self.client.post('/api/v1/induction/start-induction-proof', _START_DATA)
        self.assertEqual(resp.status_code, 201, f"start-induction-proof failed: {resp.data}")
        self.proof_id = resp.data['proof_id']

        resp = self.client.post('/api/v1/induction/set-current-proof', _ENGINE_DATA)
        self.assertEqual(resp.status_code, 201, f"set-current-proof failed: {resp.data}")

        # Apply eval + on base/LHS: (+ 0 1) -> 1
        resp = self.client.post('/api/v1/induction/apply-rule', {
            'case': 'base', 'side': 'LHS',
            'currentRacket': '(+ 0 1)', 'rule': 'eval +', 'startPosition': 0,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data.get('isValid'), f"apply-rule failed: {resp.data}")

        self.proof = InductionProof.objects.get(id=self.proof_id)
        # The generated line (line_number=1) is what we test hidden-field validation against
        self.line = InductionProofLine.objects.get(
            proof=self.proof, case='base', side='LHS', line_number=1
        )

    def tearDown(self):
        cache.clear()


class InductionValidateHiddenFieldRuleOnlyTest(_IndHiddenFieldBase):
    """
    hide_justification=True, hide_expression=False — the reported bug scenario.
    """

    def setUp(self):
        super().setUp()
        self.line.hide_justification = True
        self.line.hide_expression = False
        self.line.save()

    def test_correct_rule_no_expression_succeeds(self):
        """Bug fix: correct rule without studentExpression must succeed with no errors."""
        resp = self.client.post(_URL, {
            'case': 'base', 'side': 'LHS', 'lineNumber': 1,
            'studentRule': 'eval +', 'studentSelectedNode': 0,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['isValid'])
        self.assertEqual(resp.data['errors'], [])
        self.assertFalse(resp.data['hide_justification'])

    def test_correct_rule_reveals_justification_in_db(self):
        """Successful validation must persist hide_justification=False to the DB."""
        self.client.post(_URL, {
            'case': 'base', 'side': 'LHS', 'lineNumber': 1,
            'studentRule': 'eval +', 'studentSelectedNode': 0,
        }, format='json')
        self.line.refresh_from_db()
        self.assertFalse(self.line.hide_justification)

    def test_wrong_rule_returns_error(self):
        """Wrong rule must return isValid=False and leave the line hidden."""
        resp = self.client.post(_URL, {
            'case': 'base', 'side': 'LHS', 'lineNumber': 1,
            'studentRule': 'rewrite math', 'studentSelectedNode': 0,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['isValid'])
        self.assertTrue(len(resp.data['errors']) > 0)
        self.line.refresh_from_db()
        self.assertTrue(self.line.hide_justification)


class InductionValidateHiddenFieldExpressionOnlyTest(_IndHiddenFieldBase):
    """
    hide_expression=True, hide_justification=False.
    Block 5 must still run and enforce that the student provides the correct expression.
    """

    def setUp(self):
        super().setUp()
        self.line.hide_expression = True
        self.line.hide_justification = False
        # Ensure json_tree is populated for tree comparison
        if not self.line.json_tree:
            self.line.json_tree = _build_json_tree(self.line.racket)
        self.line.save()

    def test_correct_expression_succeeds(self):
        """Correct expression for a hidden-expression line must succeed."""
        resp = self.client.post(_URL, {
            'case': 'base', 'side': 'LHS', 'lineNumber': 1,
            'studentRule': 'eval +',
            'studentExpression': self.line.racket, 'studentSelectedNode': 0,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['isValid'])
        self.assertEqual(resp.data['errors'], [])
        self.assertFalse(resp.data['hide_expression'])

    def test_wrong_rule_and_no_expression_returns_error(self):
        """Wrong rule and no studentExpression: both Block 4 and Block 5 must produce errors."""
        # A wrong rule means Block 4 fails and does NOT reveal hide_expression,
        # so Block 5 fires and complains about the missing expression.
        resp = self.client.post(_URL, {
            'case': 'base', 'side': 'LHS', 'lineNumber': 1,
            'studentRule': 'rewrite math', 'studentSelectedNode': 0,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['isValid'])
        self.assertTrue(len(resp.data['errors']) > 0)


class InductionValidateHiddenFieldBothHiddenTest(_IndHiddenFieldBase):
    """
    Both hide_justification=True and hide_expression=True.
    Correct rule in Block 4 reveals both; Block 5 must be skipped.
    """

    def setUp(self):
        super().setUp()
        self.line.hide_justification = True
        self.line.hide_expression = True
        if not self.line.json_tree:
            self.line.json_tree = _build_json_tree(self.line.racket)
        self.line.save()

    def test_correct_rule_reveals_both_no_expression_error(self):
        """Correct rule alone must reveal both fields with no spurious expression error."""
        resp = self.client.post(_URL, {
            'case': 'base', 'side': 'LHS', 'lineNumber': 1,
            'studentRule': 'eval +', 'studentSelectedNode': 0,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['isValid'])
        self.assertEqual(resp.data['errors'], [])
        self.assertFalse(resp.data['hide_justification'])
        self.assertFalse(resp.data['hide_expression'])
