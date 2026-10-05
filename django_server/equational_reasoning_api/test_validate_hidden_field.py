"""
Tests for the validate_hidden_field endpoint in equational_reasoning_api.

Covers the bug where Block 5 (expression validation) fired unconditionally,
causing a spurious "You must provide an expression." error when only the
justification was hidden (hide_expression=False).

Run:
    $env:PYTHONIOENCODING="utf-8"; py manage.py test equational_reasoning_api.test_validate_hidden_field
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.core.cache import cache
from dill import dumps

from equational_reasoning_api.models import EquationalProof, EquationalProofLine
from expression_tree.ERProofEngine import TwoSidedProof, ERProof
from expression_tree.ERCommon import makeJson

User = get_user_model()

_URL = '/api/v1/equational/validate-hidden-field'


def _make_cache_entry(proof_obj, proof_id):
    return {'proof_obj': dumps(proof_obj), 'proof_id': proof_id}


def _build_json_tree(racket_str):
    """Return the json_tree dict for a racket expression."""
    p = ERProof()
    p.addProofLine(racket_str)
    if p.errLog or not p.proofLines:
        return {}
    return makeJson(p.proofLines[-1].exprTree)


class ValidateHiddenFieldRuleOnlyTest(TestCase):
    """
    hide_justification=True, hide_expression=False — the reported bug scenario.
    Before the fix, Block 5 fired unconditionally and added
    "You must provide an expression." even when the rule validated correctly.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='student_rule_only', email='r@test.com', password='pass'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.proof = EquationalProof.objects.create(
            user=self.user,
            lhs_goal='(+ (+ 3 1) 1)',
            rhs_goal='5',
        )
        # Line 0 — source line (selected_node=0 means whole-expression selection)
        EquationalProofLine.objects.create(
            proof=self.proof, side='LHS', line_number=0,
            racket='(+ (+ 3 1) 1)',
            json_tree=_build_json_tree('(+ (+ 3 1) 1)'),
            selected_node=0,
        )
        # Line 1 — rule hidden, expression visible ("rewrite math" scenario)
        self.line = EquationalProofLine.objects.create(
            proof=self.proof, side='LHS', line_number=1,
            racket='5', json_tree=_build_json_tree('5'),
            rule='rewrite math',
            hide_justification=True, hide_expression=False,
        )
        cache.set(
            f'equational_obj_{self.user.username}',
            _make_cache_entry(TwoSidedProof(), self.proof.id),
            timeout=None
        )

    def tearDown(self):
        cache.delete(f'equational_obj_{self.user.username}')

    def test_correct_rule_no_expression_succeeds(self):
        """Bug fix: correct rule without studentExpression must succeed with no errors."""
        resp = self.client.post(_URL, {
            'side': 'LHS', 'lineNumber': 1,
            'studentRule': 'rewrite math', 'studentSelectedNode': 0,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['isValid'])
        self.assertEqual(resp.data['errors'], [])
        self.assertFalse(resp.data['hide_justification'])

    def test_correct_rule_reveals_justification_in_db(self):
        """Successful validation must persist hide_justification=False to the DB."""
        self.client.post(_URL, {
            'side': 'LHS', 'lineNumber': 1,
            'studentRule': 'rewrite math', 'studentSelectedNode': 0,
        }, format='json')
        self.line.refresh_from_db()
        self.assertFalse(self.line.hide_justification)

    def test_wrong_rule_returns_error(self):
        """Wrong rule must return isValid=False and leave the line hidden."""
        resp = self.client.post(_URL, {
            'side': 'LHS', 'lineNumber': 1,
            'studentRule': 'eval +', 'studentSelectedNode': 0,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['isValid'])
        self.assertTrue(len(resp.data['errors']) > 0)
        self.line.refresh_from_db()
        self.assertTrue(self.line.hide_justification)


class ValidateHiddenFieldExpressionOnlyTest(TestCase):
    """
    hide_expression=True, hide_justification=False.
    Block 5 must still run and enforce that the student provides the correct expression.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='student_expr_only', email='e@test.com', password='pass'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.proof = EquationalProof.objects.create(
            user=self.user, lhs_goal='(+ 1 2)', rhs_goal='3',
        )
        EquationalProofLine.objects.create(
            proof=self.proof, side='LHS', line_number=0,
            racket='(+ 1 2)', json_tree=_build_json_tree('(+ 1 2)'), selected_node=0,
        )
        self.line = EquationalProofLine.objects.create(
            proof=self.proof, side='LHS', line_number=1,
            racket='3', json_tree=_build_json_tree('3'),
            rule='eval +', hide_justification=False, hide_expression=True,
        )
        cache.set(
            f'equational_obj_{self.user.username}',
            _make_cache_entry(TwoSidedProof(), self.proof.id),
            timeout=None
        )

    def tearDown(self):
        cache.delete(f'equational_obj_{self.user.username}')

    def test_correct_expression_succeeds(self):
        """Correct expression for a hidden-expression line must succeed."""
        resp = self.client.post(_URL, {
            'side': 'LHS', 'lineNumber': 1,
            'studentRule': 'eval +',
            'studentExpression': '3', 'studentSelectedNode': 0,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['isValid'])
        self.assertEqual(resp.data['errors'], [])
        self.assertFalse(resp.data['hide_expression'])

    def test_no_expression_provided_returns_error(self):
        """No studentExpression and no studentRule: Block 5 must fire the expression error."""
        # Omit studentRule so Block 4 is skipped; Block 5 then enforces the missing expression.
        resp = self.client.post(_URL, {
            'side': 'LHS', 'lineNumber': 1, 'studentSelectedNode': 0,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['isValid'])
        self.assertTrue(
            any('expression' in e.lower() for e in resp.data['errors']),
            f"Expected expression error; got: {resp.data['errors']}"
        )

    def test_wrong_expression_returns_error(self):
        """Wrong expression and no studentRule: Block 5 must reject the mismatch."""
        # Omit studentRule so Block 4 is skipped; Block 5 validates (and rejects) the expression.
        resp = self.client.post(_URL, {
            'side': 'LHS', 'lineNumber': 1,
            'studentExpression': '99', 'studentSelectedNode': 0,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['isValid'])


class ValidateHiddenFieldBothHiddenTest(TestCase):
    """
    Both hide_justification=True and hide_expression=True.
    Correct rule in Block 4 reveals both; Block 5 must be skipped because
    line.hide_expression is False by the time Block 5 is evaluated.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='student_both', email='b@test.com', password='pass'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.proof = EquationalProof.objects.create(
            user=self.user, lhs_goal='(+ 1 2)', rhs_goal='3',
        )
        EquationalProofLine.objects.create(
            proof=self.proof, side='LHS', line_number=0,
            racket='(+ 1 2)', json_tree=_build_json_tree('(+ 1 2)'), selected_node=0,
        )
        self.line = EquationalProofLine.objects.create(
            proof=self.proof, side='LHS', line_number=1,
            racket='3', json_tree=_build_json_tree('3'),
            rule='eval +', hide_justification=True, hide_expression=True,
        )
        cache.set(
            f'equational_obj_{self.user.username}',
            _make_cache_entry(TwoSidedProof(), self.proof.id),
            timeout=None
        )

    def tearDown(self):
        cache.delete(f'equational_obj_{self.user.username}')

    def test_correct_rule_reveals_both_no_expression_error(self):
        """Correct rule alone must reveal both fields with no spurious expression error."""
        resp = self.client.post(_URL, {
            'side': 'LHS', 'lineNumber': 1,
            'studentRule': 'eval +', 'studentSelectedNode': 0,
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['isValid'])
        self.assertEqual(resp.data['errors'], [])
        self.assertFalse(resp.data['hide_justification'])
        self.assertFalse(resp.data['hide_expression'])
