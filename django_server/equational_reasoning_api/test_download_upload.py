"""
Tests for equational reasoning proof download / upload (export / import) correctness.

Verifies that:
  - download_proof includes hideExpression and hideJustification per line
  - download_proof includes the comments array
  - upload_proof restores hide_expression and hide_justification to the DB
  - upload_proof creates EquationalProofLineComment records
  - A full roundtrip (download then upload) preserves hidden lines and comments

All DB calls are inside TestCase methods — safe against test discovery DB damage.

Run with:
  cd django_server
  python manage.py test equational_reasoning_api.test_download_upload
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from equational_reasoning_api.models import (
    EquationalProof,
    EquationalProofLine,
    EquationalProofLineComment,
)

User = get_user_model()

DOWNLOAD_URL = '/api/v1/equational/download-proof'
UPLOAD_URL   = '/api/v1/equational/upload-proof'


class EquationalDownloadUploadTestCase(TestCase):
    """Tests for equational download_proof and upload_proof endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='eq_dl_test',
            email='eq_dl_test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        # Minimal valid EquationalProof
        self.proof = EquationalProof.objects.create(
            user=self.user,
            name='EQ DL Test Proof',
            tag='',
            lhs_goal='(+ n 0)',
            rhs_goal='n',
        )

        # Premise line (line 0) — visible
        self.line0 = EquationalProofLine.objects.create(
            proof=self.proof,
            side='LHS',
            line_number=0,
            racket='(+ n 0)',
            rule='Premise',
            hide_expression=False,
            hide_justification=False,
        )

        # Generated line (line 1) — expression hidden, justification visible
        self.line1 = EquationalProofLine.objects.create(
            proof=self.proof,
            side='LHS',
            line_number=1,
            racket='(+ n 0)',
            rule='rewrite +-comm',
            hide_expression=True,
            hide_justification=False,
        )

        # Generated line (line 2) — justification hidden, expression visible
        self.line2 = EquationalProofLine.objects.create(
            proof=self.proof,
            side='LHS',
            line_number=2,
            racket='n',
            rule='eval +',
            hide_expression=False,
            hide_justification=True,
        )

        # Comments on the proof
        self.instructor_comment = EquationalProofLineComment.objects.create(
            proof=self.proof,
            side='LHS',
            line_number=1,
            role='instructor',
            comment='Verify the axiom used here.',
        )
        self.student_comment = EquationalProofLineComment.objects.create(
            proof=self.proof,
            side='LHS',
            line_number=2,
            role='student',
            comment='I used the wrong rule.',
        )

    # ------------------------------------------------------------------
    # STEP 3 tests — download includes hide flags
    # ------------------------------------------------------------------

    def test_download_includes_hide_expression_per_line(self):
        """download_proof must include hideExpression on every line dict."""
        response = self.client.get(DOWNLOAD_URL, {'proof_id': self.proof.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lhs_lines = response.data['lines']['LHS']
        self.assertTrue(len(lhs_lines) >= 2)
        for line in lhs_lines:
            self.assertIn('hideExpression', line,
                          f"Line {line.get('lineNumber')} is missing 'hideExpression'")

    def test_download_includes_hide_justification_per_line(self):
        """download_proof must include hideJustification on every line dict."""
        response = self.client.get(DOWNLOAD_URL, {'proof_id': self.proof.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lhs_lines = response.data['lines']['LHS']
        for line in lhs_lines:
            self.assertIn('hideJustification', line,
                          f"Line {line.get('lineNumber')} is missing 'hideJustification'")

    def test_download_hide_expression_values_are_correct(self):
        """hideExpression values in the download match the DB flags."""
        response = self.client.get(DOWNLOAD_URL, {'proof_id': self.proof.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lhs_lines = {l['lineNumber']: l for l in response.data['lines']['LHS']}
        self.assertFalse(lhs_lines[0]['hideExpression'])
        self.assertTrue(lhs_lines[1]['hideExpression'])
        self.assertFalse(lhs_lines[2]['hideExpression'])

    def test_download_hide_justification_values_are_correct(self):
        """hideJustification values in the download match the DB flags."""
        response = self.client.get(DOWNLOAD_URL, {'proof_id': self.proof.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lhs_lines = {l['lineNumber']: l for l in response.data['lines']['LHS']}
        self.assertFalse(lhs_lines[0]['hideJustification'])
        self.assertFalse(lhs_lines[1]['hideJustification'])
        self.assertTrue(lhs_lines[2]['hideJustification'])

    def test_download_includes_comments_key(self):
        """download_proof response must contain a top-level 'comments' list."""
        response = self.client.get(DOWNLOAD_URL, {'proof_id': self.proof.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('comments', response.data)
        self.assertIsInstance(response.data['comments'], list)

    def test_download_comments_content_is_correct(self):
        """Each comment in the download must have side, lineNumber, role, comment."""
        response = self.client.get(DOWNLOAD_URL, {'proof_id': self.proof.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comments = response.data['comments']
        self.assertEqual(len(comments), 2)
        by_role = {c['role']: c for c in comments}
        self.assertEqual(by_role['instructor']['side'], 'LHS')
        self.assertEqual(by_role['instructor']['lineNumber'], 1)
        self.assertEqual(by_role['instructor']['comment'], 'Verify the axiom used here.')
        self.assertEqual(by_role['student']['side'], 'LHS')
        self.assertEqual(by_role['student']['lineNumber'], 2)
        self.assertEqual(by_role['student']['comment'], 'I used the wrong rule.')

    def test_download_empty_comments_when_none_exist(self):
        """download_proof returns an empty comments list when no comments exist."""
        bare_proof = EquationalProof.objects.create(
            user=self.user,
            name='Bare EQ Proof',
            tag='',
            lhs_goal='(+ 1 2)',
            rhs_goal='3',
        )
        response = self.client.get(DOWNLOAD_URL, {'proof_id': bare_proof.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['comments'], [])

    # ------------------------------------------------------------------
    # STEP 4 tests — upload restores hide flags and comments
    # ------------------------------------------------------------------

    def _make_upload_payload(self, extra_line_flags=None, comments=None):
        """Build a minimal valid equational upload payload."""
        line_flags = extra_line_flags or {}
        return {
            'proofType': 'equational',
            'name': 'Uploaded EQ Proof',
            'tag': '',
            'lhsGoal': '(+ n 0)',
            'rhsGoal': 'n',
            'definition': [],
            'support_errors': True,
            'support_current_lhs_rhs': True,
            'support_ih': True,
            'support_premise': True,
            'support_rule_set': True,
            'visible_rules': {},
            'support_value_mapping': True,
            'support_rewrite_complexity': True,
            'lines': {
                'LHS': [
                    {
                        'lineNumber': 0,
                        'racket': '(+ n 0)',
                        'rule': 'Premise',
                        'startPosition': 0,
                        'selectedNode': 0,
                        'resultNode': 0,
                        'substitution': '',
                        'jsonTree': {},
                        'hideExpression': line_flags.get('line0_hideExpr', False),
                        'hideJustification': line_flags.get('line0_hideJust', False),
                    },
                    {
                        'lineNumber': 1,
                        'racket': 'n',
                        'rule': 'eval +',
                        'startPosition': 0,
                        'selectedNode': 0,
                        'resultNode': 0,
                        'substitution': '',
                        'jsonTree': {},
                        'hideExpression': line_flags.get('line1_hideExpr', False),
                        'hideJustification': line_flags.get('line1_hideJust', False),
                    },
                ],
                'RHS': [],
            },
            'comments': comments if comments is not None else [],
        }

    def test_upload_restores_hide_expression_true(self):
        """upload_proof must write hide_expression=True to DB when JSON has hideExpression=True."""
        payload = self._make_upload_payload(extra_line_flags={'line1_hideExpr': True})
        response = self.client.post(UPLOAD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        proof_id = response.data['proofId']
        line = EquationalProofLine.objects.get(proof_id=proof_id, side='LHS', line_number=1)
        self.assertTrue(line.hide_expression)
        self.assertFalse(line.hide_justification)

    def test_upload_restores_hide_justification_true(self):
        """upload_proof must write hide_justification=True to DB when JSON has hideJustification=True."""
        payload = self._make_upload_payload(extra_line_flags={'line1_hideJust': True})
        response = self.client.post(UPLOAD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        proof_id = response.data['proofId']
        line = EquationalProofLine.objects.get(proof_id=proof_id, side='LHS', line_number=1)
        self.assertFalse(line.hide_expression)
        self.assertTrue(line.hide_justification)

    def test_upload_hide_flags_default_false_when_absent(self):
        """Lines uploaded without hide flags must default to hide_expression=False."""
        payload = self._make_upload_payload()
        response = self.client.post(UPLOAD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        proof_id = response.data['proofId']
        for line_num in (0, 1):
            line = EquationalProofLine.objects.get(proof_id=proof_id, side='LHS', line_number=line_num)
            self.assertFalse(line.hide_expression)
            self.assertFalse(line.hide_justification)

    def test_upload_creates_instructor_comment(self):
        """upload_proof must create EquationalProofLineComment records from the comments array."""
        comments = [{'side': 'LHS', 'lineNumber': 1, 'role': 'instructor', 'comment': 'Well done!'}]
        payload = self._make_upload_payload(comments=comments)
        response = self.client.post(UPLOAD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        proof_id = response.data['proofId']
        c = EquationalProofLineComment.objects.get(proof_id=proof_id, side='LHS', line_number=1, role='instructor')
        self.assertEqual(c.comment, 'Well done!')

    def test_upload_creates_student_comment(self):
        """upload_proof must create student comments from the comments array."""
        comments = [{'side': 'LHS', 'lineNumber': 0, 'role': 'student', 'comment': 'Is this right?'}]
        payload = self._make_upload_payload(comments=comments)
        response = self.client.post(UPLOAD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        proof_id = response.data['proofId']
        c = EquationalProofLineComment.objects.get(proof_id=proof_id, side='LHS', line_number=0, role='student')
        self.assertEqual(c.comment, 'Is this right?')

    def test_upload_creates_multiple_comments(self):
        """upload_proof must create all comment records when multiple comments are present."""
        comments = [
            {'side': 'LHS', 'lineNumber': 1, 'role': 'instructor', 'comment': 'Recheck.'},
            {'side': 'LHS', 'lineNumber': 1, 'role': 'student', 'comment': 'Not sure.'},
        ]
        payload = self._make_upload_payload(comments=comments)
        response = self.client.post(UPLOAD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        proof_id = response.data['proofId']
        count = EquationalProofLineComment.objects.filter(proof_id=proof_id).count()
        self.assertEqual(count, 2)

    def test_upload_no_comments_when_array_empty(self):
        """upload_proof with empty comments array must not create comment records."""
        payload = self._make_upload_payload(comments=[])
        response = self.client.post(UPLOAD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        proof_id = response.data['proofId']
        count = EquationalProofLineComment.objects.filter(proof_id=proof_id).count()
        self.assertEqual(count, 0)

    def test_upload_no_comments_when_key_absent(self):
        """upload_proof with no comments key in payload must not create comment records."""
        payload = self._make_upload_payload()
        del payload['comments']
        response = self.client.post(UPLOAD_URL, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        proof_id = response.data['proofId']
        count = EquationalProofLineComment.objects.filter(proof_id=proof_id).count()
        self.assertEqual(count, 0)

    # ------------------------------------------------------------------
    # Full roundtrip test (Steps 3 + 4 combined)
    # ------------------------------------------------------------------

    def test_full_roundtrip_preserves_hidden_lines_and_comments(self):
        """Download an existing proof then upload it; DB record must preserve all flags and comments."""
        # 1. Download
        dl_response = self.client.get(DOWNLOAD_URL, {'proof_id': self.proof.id})
        self.assertEqual(dl_response.status_code, status.HTTP_200_OK)
        exported = dl_response.data
        exported['name'] = 'EQ Roundtrip Proof'

        # 2. Upload
        ul_response = self.client.post(UPLOAD_URL, exported, format='json')
        self.assertEqual(ul_response.status_code, status.HTTP_201_CREATED)
        new_id = ul_response.data['proofId']

        # 3. Verify hide flags
        line0 = EquationalProofLine.objects.get(proof_id=new_id, side='LHS', line_number=0)
        line1 = EquationalProofLine.objects.get(proof_id=new_id, side='LHS', line_number=1)
        line2 = EquationalProofLine.objects.get(proof_id=new_id, side='LHS', line_number=2)
        self.assertFalse(line0.hide_expression)
        self.assertFalse(line0.hide_justification)
        self.assertTrue(line1.hide_expression)
        self.assertFalse(line1.hide_justification)
        self.assertFalse(line2.hide_expression)
        self.assertTrue(line2.hide_justification)

        # 4. Verify comments
        comments = EquationalProofLineComment.objects.filter(proof_id=new_id)
        self.assertEqual(comments.count(), 2)
        by_role = {c.role: c for c in comments}
        self.assertEqual(by_role['instructor'].comment, 'Verify the axiom used here.')
        self.assertEqual(by_role['student'].comment, 'I used the wrong rule.')
