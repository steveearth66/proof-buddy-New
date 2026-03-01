"""
Tests for the cross-mode name conflict feature.

This feature prevents a user from having two active proofs with the same name,
regardless of whether they are Induction or Equational Reasoning proofs.

Tests cover:
  1. check_name_conflict endpoint  (GET /api/v1/induction/check-name-conflict)
  2. Archive logic in start_induction_proof (POST /api/v1/induction/start-induction-proof)
  3. Archive logic in save_proof / get_or_create_proof (POST /api/v1/equational/save-proof)

Run with:
  cd django_server
  python manage.py test induction_api.tests_name_conflict
"""

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache

from induction_api.models import InductionProof
from equational_reasoning_api.models import EquationalProof

User = get_user_model()

# ---------------------------------------------------------------------------
# URL constants
# ---------------------------------------------------------------------------
INDUCTION_BASE = '/api/v1/induction/'
ER_BASE        = '/api/v1/equational/'

CHECK_URL = f'{INDUCTION_BASE}check-name-conflict'
START_IND_URL = f'{INDUCTION_BASE}start-induction-proof'
SAVE_ER_URL   = f'{ER_BASE}save-proof'

# ---------------------------------------------------------------------------
# Minimal valid payloads
# ---------------------------------------------------------------------------
def induction_payload(name='My Proof', tag='my-tag'):
    return {
        'proof_name': name,
        'proof_tag': tag,
        'induction_variable': 'n',
        'anchor_value': 0,
        'leap_variable': 'k',
        'lhs_leap_goal': '(+ n 1)',
        'rhs_leap_goal': '(+ 1 n)',
        'lhs_anchor_goal': '(+ n 1)',
        'rhs_anchor_goal': '(+ 1 n)',
        'induction_type': 'integers',
        'inductive_hypothesis_lhs': '(+ k 1)',
        'inductive_hypothesis_rhs': '(+ 1 k)',
    }


def er_payload(name='My Proof', tag='my-tag'):
    return {
        'name': name,
        'tag': tag,
        'lHSGoal': '(+ a b)',
        'rHSGoal': '(+ b a)',
        'definitions': [],
        'generics': [],
    }


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

class CheckNameConflictEndpointTests(TransactionTestCase):
    """Tests for GET /api/v1/induction/check-name-conflict?name=..."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='conflict_user',
            email='conflict@example.com',
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

    # --- Positive (conflict detected) cases --------------------------------

    def test_detects_active_induction_proof_conflict(self):
        """Conflict returns True and type='Induction' when an active InductionProof exists."""
        InductionProof.objects.create(
            user=self.user,
            name='SharedName',
            tag='t',
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_leap_goal='(+ n 1)',
            rhs_leap_goal='(+ 1 n)',
        )

        response = self.client.get(CHECK_URL, {'name': 'SharedName'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['conflict'])
        self.assertEqual(response.data['type'], 'Induction')
        self.assertEqual(response.data['name'], 'SharedName')

    def test_detects_active_er_proof_conflict(self):
        """Conflict returns True and type='Equational Reasoning' when an active EquationalProof exists."""
        EquationalProof.objects.create(
            user=self.user,
            name='SharedName',
            tag='t',
            lhs_goal='(+ a b)',
            rhs_goal='(+ b a)',
        )

        response = self.client.get(CHECK_URL, {'name': 'SharedName'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['conflict'])
        self.assertEqual(response.data['type'], 'Equational Reasoning')
        self.assertEqual(response.data['name'], 'SharedName')

    # --- Negative (no conflict) cases --------------------------------------

    def test_no_conflict_for_unknown_name(self):
        """No active proof with the given name → conflict is False."""
        response = self.client.get(CHECK_URL, {'name': 'DoesNotExist'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['conflict'])
        self.assertIsNone(response.data['type'])

    def test_no_conflict_when_name_param_missing(self):
        """Missing name param → no crash; conflict is False."""
        response = self.client.get(CHECK_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['conflict'])

    def test_no_conflict_for_archived_induction_proof(self):
        """Archived (is_active=False) InductionProof should not count as a conflict."""
        InductionProof.objects.create(
            user=self.user,
            name='ArchivedInd',
            tag='t',
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_leap_goal='(+ n 1)',
            rhs_leap_goal='(+ 1 n)',
            is_active=False,
        )

        response = self.client.get(CHECK_URL, {'name': 'ArchivedInd'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['conflict'])

    def test_no_conflict_for_archived_er_proof(self):
        """Archived (is_active=False) EquationalProof should not count as a conflict."""
        EquationalProof.objects.create(
            user=self.user,
            name='ArchivedER',
            tag='t',
            lhs_goal='(+ a b)',
            rhs_goal='(+ b a)',
            is_active=False,
        )

        response = self.client.get(CHECK_URL, {'name': 'ArchivedER'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['conflict'])

    def test_no_conflict_for_other_users_proof(self):
        """Another user's active proof should not conflict with the requesting user."""
        other_user = User.objects.create_user(
            username='other_user_conflict',
            email='other_conflict@example.com',
            password='testpass123',
        )
        InductionProof.objects.create(
            user=other_user,
            name='OtherUserProof',
            tag='t',
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_leap_goal='(+ n 1)',
            rhs_leap_goal='(+ 1 n)',
        )

        response = self.client.get(CHECK_URL, {'name': 'OtherUserProof'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['conflict'])

    def test_unauthenticated_request_is_rejected(self):
        """Unauthenticated requests should receive a 401/403."""
        unauthenticated_client = APIClient()
        response = unauthenticated_client.get(CHECK_URL, {'name': 'AnyName'})

        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ])

    def test_exact_name_match_returns_conflict(self):
        """Exact proof name match returns conflict=True."""
        InductionProof.objects.create(
            user=self.user,
            name='ExactName',
            tag='t',
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_leap_goal='(+ n 1)',
            rhs_leap_goal='(+ 1 n)',
        )

        response = self.client.get(CHECK_URL, {'name': 'ExactName'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['conflict'])

    def test_different_name_returns_no_conflict(self):
        """A completely different name returns conflict=False even with an existing proof."""
        InductionProof.objects.create(
            user=self.user,
            name='ExistingName',
            tag='t',
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_leap_goal='(+ n 1)',
            rhs_leap_goal='(+ 1 n)',
        )

        response = self.client.get(CHECK_URL, {'name': 'TotallyDifferent'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['conflict'])


# ---------------------------------------------------------------------------

class InductionStartArchiveTests(TransactionTestCase):
    """
    Tests for archive (is_active=False) logic triggered by startInductionProof.

    Starting a new proof with name X must archive:
      - any existing active InductionProof named X (same user)
      - any existing active EquationalProof named X (same user)
    and must NOT affect proofs with different names.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='archive_ind_user',
            email='arch_ind@example.com',
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

    def test_starting_induction_archives_old_induction_same_name(self):
        """
        When starting an induction proof whose name already exists as an active
        InductionProof, the old proof is archived and the new one is active.
        """
        old_proof = InductionProof.objects.create(
            user=self.user,
            name='Shared',
            tag='v1',
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_leap_goal='(+ n 1)',
            rhs_leap_goal='(+ 1 n)',
            is_active=True,
        )

        response = self.client.post(START_IND_URL, induction_payload(name='Shared', tag='v2'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        old_proof.refresh_from_db()
        self.assertFalse(old_proof.is_active, "Old InductionProof should be archived.")

        new_id = response.data['proof_id']
        new_proof = InductionProof.objects.get(id=new_id)
        self.assertTrue(new_proof.is_active, "New InductionProof should be active.")

    def test_starting_induction_archives_existing_er_proof_same_name(self):
        """
        When starting an induction proof whose name already exists as an active
        EquationalProof, the ER proof is archived (cross-table archiving).
        """
        er_proof = EquationalProof.objects.create(
            user=self.user,
            name='CrossOver',
            tag='er',
            lhs_goal='(+ a b)',
            rhs_goal='(+ b a)',
            is_active=True,
        )

        response = self.client.post(START_IND_URL, induction_payload(name='CrossOver', tag='ind'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        er_proof.refresh_from_db()
        self.assertFalse(er_proof.is_active, "EquationalProof with same name should be archived.")

    def test_starting_induction_does_not_archive_different_name(self):
        """
        Starting an induction proof must NOT archive an existing proof with a
        different name.
        """
        unrelated_ind = InductionProof.objects.create(
            user=self.user,
            name='Different',
            tag='t',
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_leap_goal='(+ n 1)',
            rhs_leap_goal='(+ 1 n)',
            is_active=True,
        )
        unrelated_er = EquationalProof.objects.create(
            user=self.user,
            name='AlsoUnrelated',
            tag='t',
            lhs_goal='(+ a b)',
            rhs_goal='(+ b a)',
            is_active=True,
        )

        self.client.post(START_IND_URL, induction_payload(name='NewUnique', tag='nu'), format='json')

        unrelated_ind.refresh_from_db()
        unrelated_er.refresh_from_db()
        self.assertTrue(unrelated_ind.is_active, "Unrelated InductionProof should remain active.")
        self.assertTrue(unrelated_er.is_active, "Unrelated EquationalProof should remain active.")

    def test_starting_induction_does_not_archive_other_users_proofs(self):
        """
        Archive logic must be scoped to the requesting user only.
        """
        other = User.objects.create_user(
            username='other_archive_ind',
            email='other_archive_ind@example.com',
            password='testpass123',
        )
        other_proof = InductionProof.objects.create(
            user=other,
            name='Shared',
            tag='t',
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_leap_goal='(+ n 1)',
            rhs_leap_goal='(+ 1 n)',
            is_active=True,
        )

        self.client.post(START_IND_URL, induction_payload(name='Shared', tag='mine'), format='json')

        other_proof.refresh_from_db()
        self.assertTrue(other_proof.is_active, "Another user's proof must not be archived.")


# ---------------------------------------------------------------------------

class ERSaveArchiveTests(TransactionTestCase):
    """
    Tests for archive logic triggered by POST /api/v1/equational/save-proof
    (which calls get_or_create_proof internally).

    Saving an ER proof with name X must archive:
      - any existing active EquationalProof named X (same user)
      - any existing active InductionProof named X (same user)
    and must NOT affect proofs with different names.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='archive_er_user',
            email='arch_er@example.com',
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

    def test_saving_er_archives_old_er_proof_same_name(self):
        """
        Saving an ER proof with a name that already exists as an active
        EquationalProof archives the old one and creates a new active one.
        """
        old_er = EquationalProof.objects.create(
            user=self.user,
            name='ERName',
            tag='v1',
            lhs_goal='(+ a b)',
            rhs_goal='(+ b a)',
            is_active=True,
        )

        response = self.client.post(SAVE_ER_URL, er_payload(name='ERName', tag='v2'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        old_er.refresh_from_db()
        self.assertFalse(old_er.is_active, "Old EquationalProof should be archived.")

        new_id = response.data['proofId']
        new_er = EquationalProof.objects.get(id=new_id)
        self.assertTrue(new_er.is_active, "New EquationalProof should be active.")

    def test_saving_er_archives_existing_induction_proof_same_name(self):
        """
        Saving an ER proof whose name already exists as an active InductionProof
        archives the induction proof (cross-table archiving).
        """
        ind_proof = InductionProof.objects.create(
            user=self.user,
            name='CrossER',
            tag='ind',
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_leap_goal='(+ n 1)',
            rhs_leap_goal='(+ 1 n)',
            is_active=True,
        )

        response = self.client.post(SAVE_ER_URL, er_payload(name='CrossER', tag='er'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ind_proof.refresh_from_db()
        self.assertFalse(ind_proof.is_active, "InductionProof with same name should be archived.")

    def test_saving_er_does_not_archive_different_name(self):
        """
        Saving an ER proof must NOT archive proofs with different names.
        """
        unrelated_er = EquationalProof.objects.create(
            user=self.user,
            name='UnrelatedER',
            tag='t',
            lhs_goal='(+ a b)',
            rhs_goal='(+ b a)',
            is_active=True,
        )
        unrelated_ind = InductionProof.objects.create(
            user=self.user,
            name='UnrelatedInd',
            tag='t',
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_leap_goal='(+ n 1)',
            rhs_leap_goal='(+ 1 n)',
            is_active=True,
        )

        self.client.post(SAVE_ER_URL, er_payload(name='BrandNew', tag='bn'), format='json')

        unrelated_er.refresh_from_db()
        unrelated_ind.refresh_from_db()
        self.assertTrue(unrelated_er.is_active, "Unrelated EquationalProof should remain active.")
        self.assertTrue(unrelated_ind.is_active, "Unrelated InductionProof should remain active.")

    def test_saving_er_does_not_archive_other_users_proofs(self):
        """
        Archive logic must be scoped to the requesting user only.
        """
        other = User.objects.create_user(
            username='other_archive_er',
            email='other_archive_er@example.com',
            password='testpass123',
        )
        other_ind = InductionProof.objects.create(
            user=other,
            name='CrossER',
            tag='ind',
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_leap_goal='(+ n 1)',
            rhs_leap_goal='(+ 1 n)',
            is_active=True,
        )

        self.client.post(SAVE_ER_URL, er_payload(name='CrossER', tag='er'), format='json')

        other_ind.refresh_from_db()
        self.assertTrue(other_ind.is_active, "Another user's proof must not be archived.")
