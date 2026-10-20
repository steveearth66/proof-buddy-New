"""
Comprehensive unit tests for validate_hidden_field on a simple one-line proof.

Proof setup for all tests:
  - LHS premise (line 0): (+ 1 2)
  - Generated line (line 1): 3  via  eval +

Three visibility scenarios tested, each with correct and incorrect student input:

  A. Rule hidden, expression visible
       A1. correct rule         → reveals rule,  no errors
       A2. wrong rule           → error, nothing revealed

  B. Expression hidden, rule visible
       B1. correct expression   → reveals expression,  no errors
       B2. wrong expression     → error, nothing revealed
       B3. no expression given  → error, nothing revealed

  C. Both hidden
       C1. correct rule + correct expression → reveals both,  no errors
       C2. correct rule + wrong expression   → expression error, nothing revealed
       C3. wrong rule  + correct expression  → rule error,  nothing revealed
       C4. wrong rule  + wrong expression    → both errors, nothing revealed

All DB calls are inside TestCase methods — safe against test discovery DB damage.

Run:
    cd django_server
    $env:PYTHONIOENCODING="utf-8"; py manage.py test equational_reasoning_api.test_hidden_field_cases
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

# Proof:  (+ 1 2)  =  3  via  eval +
_LHS_GOAL = '(+ 1 2)'
_RHS_GOAL = '3'
_PREMISE   = '(+ 1 2)'
_GENERATED = '3'
_RULE      = 'eval +'
_WRONG_EXPRESSION = '99'
_WRONG_RULE       = 'eval -'


def _build_json_tree(racket_str):
    """Build the json_tree dict for a racket expression via the ER engine."""
    p = ERProof()
    p.addProofLine(racket_str)
    if p.errLog or not p.proofLines:
        return {}
    return makeJson(p.proofLines[-1].exprTree)


def _make_cache_entry(proof_obj, proof_id):
    return {'proof_obj': dumps(proof_obj), 'proof_id': proof_id}


class _SimpleProofBase(TestCase):
    """
    Base: one premise + one generated line, both initially visible.
    Subclasses adjust hide flags in their own setUp.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='hf_student', email='hf@test.com', password='pass'
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.proof = EquationalProof.objects.create(
            user=self.user,
            lhs_goal=_LHS_GOAL,
            rhs_goal=_RHS_GOAL,
        )
        # Line 0 — premise; selected_node=0 so selection check always passes
        EquationalProofLine.objects.create(
            proof=self.proof, side='LHS', line_number=0,
            racket=_PREMISE,
            json_tree=_build_json_tree(_PREMISE),
            selected_node=0,
        )
        # Line 1 — the generated line we validate against
        self.line = EquationalProofLine.objects.create(
            proof=self.proof, side='LHS', line_number=1,
            racket=_GENERATED,
            json_tree=_build_json_tree(_GENERATED),
            rule=_RULE,
            hide_justification=False,
            hide_expression=False,
        )
        cache.set(
            f'equational_obj_{self.user.username}',
            _make_cache_entry(TwoSidedProof(), self.proof.id),
            timeout=None
        )

    def tearDown(self):
        cache.delete(f'equational_obj_{self.user.username}')

    def _post(self, **kwargs):
        """POST helper; always includes side and lineNumber."""
        payload = {'side': 'LHS', 'lineNumber': 1, 'studentSelectedNode': 0}
        payload.update(kwargs)
        return self.client.post(_URL, payload, format='json')

    def _refresh(self):
        self.line.refresh_from_db()


# ---------------------------------------------------------------------------
# A. Rule hidden, expression visible
# ---------------------------------------------------------------------------

class RuleHiddenExpressionVisibleTest(_SimpleProofBase):
    """hide_justification=True, hide_expression=False."""

    def setUp(self):
        super().setUp()
        self.line.hide_justification = True
        self.line.hide_expression = False
        self.line.save()

    # A1 — correct rule
    def test_correct_rule_succeeds(self):
        """Correct rule must return isValid=True with no errors."""
        resp = self._post(studentRule=_RULE)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['isValid'])
        self.assertEqual(resp.data['errors'], [])

    def test_correct_rule_reveals_justification(self):
        """Correct rule must flip hide_justification to False in the response and DB."""
        resp = self._post(studentRule=_RULE)
        self.assertFalse(resp.data['hide_justification'])
        self._refresh()
        self.assertFalse(self.line.hide_justification)

    def test_correct_rule_leaves_expression_unchanged(self):
        """Expression was already visible; hide_expression must stay False."""
        resp = self._post(studentRule=_RULE)
        self.assertFalse(resp.data['hide_expression'])

    # A2 — wrong rule
    def test_wrong_rule_fails(self):
        """Wrong rule must return isValid=False with an error."""
        resp = self._post(studentRule=_WRONG_RULE)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['isValid'])
        self.assertTrue(len(resp.data['errors']) > 0)

    def test_wrong_rule_leaves_line_hidden(self):
        """Wrong rule must NOT reveal hide_justification."""
        self._post(studentRule=_WRONG_RULE)
        self._refresh()
        self.assertTrue(self.line.hide_justification)


# ---------------------------------------------------------------------------
# B. Expression hidden, rule visible
# ---------------------------------------------------------------------------

class ExpressionHiddenRuleVisibleTest(_SimpleProofBase):
    """hide_expression=True, hide_justification=False."""

    def setUp(self):
        super().setUp()
        self.line.hide_justification = False
        self.line.hide_expression = True
        self.line.save()

    # B1 — correct expression
    def test_correct_expression_succeeds(self):
        """Correct expression must return isValid=True with no errors."""
        resp = self._post(studentExpression=_GENERATED)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['isValid'])
        self.assertEqual(resp.data['errors'], [])

    def test_correct_expression_reveals_expression(self):
        """Correct expression must flip hide_expression to False in the response and DB."""
        resp = self._post(studentExpression=_GENERATED)
        self.assertFalse(resp.data['hide_expression'])
        self._refresh()
        self.assertFalse(self.line.hide_expression)

    def test_correct_expression_leaves_rule_unchanged(self):
        """Rule was already visible; hide_justification must stay False."""
        resp = self._post(studentExpression=_GENERATED)
        self.assertFalse(resp.data['hide_justification'])

    # B2 — wrong expression
    def test_wrong_expression_fails(self):
        """Wrong expression must return isValid=False with an error."""
        resp = self._post(studentExpression=_WRONG_EXPRESSION)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['isValid'])
        self.assertIn('Expression does not match.', resp.data['errors'])

    def test_wrong_expression_leaves_line_hidden(self):
        """Wrong expression must NOT reveal hide_expression."""
        self._post(studentExpression=_WRONG_EXPRESSION)
        self._refresh()
        self.assertTrue(self.line.hide_expression)

    # B3 — no expression given
    def test_no_expression_fails(self):
        """Omitting studentExpression must return isValid=False."""
        resp = self._post()
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['isValid'])
        self.assertTrue(
            any('expression' in e.lower() for e in resp.data['errors']),
            f"Expected expression error; got: {resp.data['errors']}"
        )

    def test_no_expression_leaves_line_hidden(self):
        """Omitting studentExpression must NOT reveal hide_expression."""
        self._post()
        self._refresh()
        self.assertTrue(self.line.hide_expression)


# ---------------------------------------------------------------------------
# C. Both hidden
# ---------------------------------------------------------------------------

class BothHiddenTest(_SimpleProofBase):
    """hide_justification=True, hide_expression=True."""

    def setUp(self):
        super().setUp()
        self.line.hide_justification = True
        self.line.hide_expression = True
        self.line.save()

    # C1 — correct rule + correct expression
    def test_correct_rule_and_expression_reveals_both(self):
        """Correct rule and expression must reveal both fields."""
        resp = self._post(studentRule=_RULE, studentExpression=_GENERATED)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['isValid'])
        self.assertEqual(resp.data['errors'], [])
        self.assertFalse(resp.data['hide_justification'])
        self.assertFalse(resp.data['hide_expression'])

    def test_correct_rule_and_expression_persisted_to_db(self):
        """Both flags must be False in the DB after a fully correct submission."""
        self._post(studentRule=_RULE, studentExpression=_GENERATED)
        self._refresh()
        self.assertFalse(self.line.hide_justification)
        self.assertFalse(self.line.hide_expression)

    # C2 — correct rule + wrong expression
    def test_correct_rule_wrong_expression_fails(self):
        """Correct rule with wrong expression must fail and reveal nothing."""
        resp = self._post(studentRule=_RULE, studentExpression=_WRONG_EXPRESSION)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['isValid'])
        self.assertIn('Expression does not match.', resp.data['errors'])
        self.assertTrue(resp.data['hide_justification'])
        self.assertTrue(resp.data['hide_expression'])

    def test_correct_rule_wrong_expression_nothing_revealed_in_db(self):
        """Neither flag must be changed in the DB when expression is wrong."""
        self._post(studentRule=_RULE, studentExpression=_WRONG_EXPRESSION)
        self._refresh()
        self.assertTrue(self.line.hide_justification)
        self.assertTrue(self.line.hide_expression)

    # C3 — wrong rule + correct expression
    def test_wrong_rule_correct_expression_fails(self):
        """Wrong rule with correct expression must fail and reveal nothing."""
        resp = self._post(studentRule=_WRONG_RULE, studentExpression=_GENERATED)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['isValid'])
        self.assertIn('Rule does not match.', resp.data['errors'])
        self.assertTrue(resp.data['hide_justification'])
        self.assertTrue(resp.data['hide_expression'])

    def test_wrong_rule_correct_expression_nothing_revealed_in_db(self):
        """Neither flag must be changed in the DB when rule is wrong."""
        self._post(studentRule=_WRONG_RULE, studentExpression=_GENERATED)
        self._refresh()
        self.assertTrue(self.line.hide_justification)
        self.assertTrue(self.line.hide_expression)

    # C4 — wrong rule + wrong expression
    def test_wrong_rule_wrong_expression_fails(self):
        """Both wrong must fail and reveal nothing."""
        resp = self._post(studentRule=_WRONG_RULE, studentExpression=_WRONG_EXPRESSION)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['isValid'])
        self.assertTrue(len(resp.data['errors']) > 0)
        self.assertTrue(resp.data['hide_justification'])
        self.assertTrue(resp.data['hide_expression'])

    def test_wrong_rule_wrong_expression_nothing_revealed_in_db(self):
        """Neither flag must be changed in the DB when both are wrong."""
        self._post(studentRule=_WRONG_RULE, studentExpression=_WRONG_EXPRESSION)
        self._refresh()
        self.assertTrue(self.line.hide_justification)
        self.assertTrue(self.line.hide_expression)
