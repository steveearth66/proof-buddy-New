from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache
from dill import dumps, loads
from .models import InductionProof
from .views import save_induction_proof_to_cache, get_or_set_induction_proof, clear_induction_proof


User = get_user_model()


BASE_URL = '/api/v1/induction/'

CREATE_URL = f'{BASE_URL}create-induction-proof'
START_URL = f'{BASE_URL}start-induction-proof'
CLEAR_URL = f'{BASE_URL}clear-induction'
LIST_PROOFS_URL = f'{BASE_URL}get-induction-proofs'
DETAIL_PROOF_URL = lambda pk: f'{BASE_URL}proof/{pk}/'


class InductionProofViewTests(TransactionTestCase):
    """Test suite for induction proof views"""
    
    def setUp(self):
        """Set up test client and test user"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        try:
            cache.clear()
        except Exception:
            pass
    
    def tearDown(self):
        """Clean up after each test"""
        try:
            cache.clear()
        except Exception:
            pass

    
    def test_create_induction_proof_success(self):
        """Test successful creation of induction proof"""
        data = {
            'induction_variable': 'n',
            'anchor_value': 0,
            'leap_variable': 'k',
            'lhs_expression': '(sum n)',
            'rhs_expression': '(* n (+ n 1) (/ 1 2))'
        }
        
        response = self.client.post(CREATE_URL, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['induction_variable'], 'n')
        self.assertEqual(response.data['anchor_value'], 0)
        self.assertEqual(response.data['leap_variable'], 'k')
        
        self.assertEqual(response.data['lhs_anchor_goal'], '(sum 0)')
        self.assertEqual(response.data['rhs_anchor_goal'], '(* 0 (+ 0 1) (/ 1 2))')
        
        self.assertEqual(response.data['lhs_leap_goal'], '(sum k)')
        self.assertEqual(response.data['rhs_leap_goal'], '(* k (+ k 1) (/ 1 2))')
        
        proof = InductionProof.objects.get(user=self.user)
        self.assertEqual(proof.induction_variable, 'n')
        self.assertEqual(proof.anchor_value, 0)
        
        cache_key = f"induction_proof_{self.user.username}"
        cached_proof = loads(cache.get(cache_key))
        self.assertIsNotNone(cached_proof)
        self.assertEqual(cached_proof['lhs_leap_goal'], '(sum k)')
    
    def test_create_induction_proof_missing_fields(self):
        """Test creation fails with missing required fields"""
        data = {
            'induction_variable': 'n',
            'anchor_value': 0,

        }
        
        response = self.client.post(CREATE_URL, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    
    def test_start_induction_proof(self):
        """Test starting an induction proof"""
        data = {
            'proof_id': 1,
            'side': 'LHS',
            'case': 'anchor'
        }
        
        response = self.client.post(START_URL, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, data)

    
    def test_clear_induction_cache_only(self):
        """Test clearing only cache, not database"""
        proof = InductionProof.objects.create(
            user=self.user,
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_expression='(sum n)',
            rhs_expression='(* n (+ n 1) (/ 1 2))'
        )
        
        save_induction_proof_to_cache(self.user, {'id': proof.id, 'test': 'data'})
        
        response = self.client.post(CLEAR_URL, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Induction proof cleared successfully')
        
        cache_key = f"induction_proof_{self.user.username}"
        self.assertIsNone(cache.get(cache_key))
        
        self.assertTrue(InductionProof.objects.filter(user=self.user).exists())
    
    def test_clear_induction_delete_all(self):
        """Test clearing cache and deleting all proofs from database"""
        InductionProof.objects.create(
            user=self.user,
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_expression='(sum n)',
            rhs_expression='(* n)'
        )
        InductionProof.objects.create(
            user=self.user,
            proof_type='induction_int',
            induction_variable='x',
            anchor_value=1,
            leap_variable='y',
            lhs_expression='(factorial x)',
            rhs_expression='(* x)'
        )
        
        save_induction_proof_to_cache(self.user, {'test': 'data'})
        
        response = self.client.post(
            CLEAR_URL,
            {'delete_all': True},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        cache_key = f"induction_proof_{self.user.username}"
        self.assertIsNone(cache.get(cache_key))
        
        self.assertEqual(InductionProof.objects.filter(user=self.user).count(), 0)

    
    def test_get_induction_proofs_empty(self):
        """Test getting proofs when user has none"""
        response = self.client.get(LIST_PROOFS_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
    
    def test_get_induction_proofs_multiple(self):
        """Test getting multiple proofs for user"""
        proof1 = InductionProof.objects.create(
            user=self.user,
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_expression='(sum n)',
            rhs_expression='(* n)'
        )
        proof2 = InductionProof.objects.create(
            user=self.user,
            proof_type='induction_int',
            induction_variable='x',
            anchor_value=1,
            leap_variable='y',
            lhs_expression='(factorial x)',
            rhs_expression='(* x)'
        )
        
        response = self.client.get(LIST_PROOFS_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        proof_ids = [p['id'] for p in response.data]
        self.assertIn(proof1.id, proof_ids)
        self.assertIn(proof2.id, proof_ids)

    
    def test_get_induction_proof_success(self):
        """Test getting a single proof by ID"""
        proof = InductionProof.objects.create(
            user=self.user,
            proof_type='induction_int',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_expression='(sum n)',
            rhs_expression='(* n)'
        )
        
        response = self.client.get(DETAIL_PROOF_URL(proof.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], proof.id)
        self.assertEqual(response.data['induction_variable'], 'n')
    
    def test_get_induction_proof_not_found(self):
        """Test getting non-existent proof"""
        response = self.client.get(DETAIL_PROOF_URL(99999))
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    
    def test_save_induction_proof_to_cache(self):
        """Test saving proof to cache"""
        proof_data = {
            'id': 1,
            'lhs_leap_goal': '(sum k)',
            'rhs_leap_goal': '(* k)',
            'current_goal': 'base_case'
        }
        
        save_induction_proof_to_cache(self.user, proof_data)
        
        cache_key = f"induction_proof_{self.user.username}"
        cached_data = loads(cache.get(cache_key))
        
        self.assertEqual(cached_data['id'], 1)
        self.assertEqual(cached_data['lhs_leap_goal'], '(sum k)')
    
    def test_get_or_set_induction_proof_new(self):
        """Test getting proof when cache is empty"""
        proof_data = get_or_set_induction_proof(self.user)
        
        self.assertIsNotNone(proof_data)
        self.assertIsNone(proof_data['lhs_leap_goal'])
        self.assertIsNone(proof_data['current_goal'])
        self.assertTrue(proof_data['isValid'])
        self.assertEqual(proof_data['definition'], [])
    
    def test_clear_induction_proof_function(self):
        """Test clear_induction_proof helper function"""
        save_induction_proof_to_cache(self.user, {'test': 'data'})
        
        cache_key = f"induction_proof_{self.user.username}"
        self.assertIsNotNone(cache.get(cache_key))
        
        clear_induction_proof(self.user)
        
        self.assertIsNone(cache.get(cache_key))


class EngineEndpointTests(TransactionTestCase):
    """Test suite for new induction ER engine endpoints"""
    
    def setUp(self):
        """Set up test client and test user"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        try:
            cache.clear()
        except Exception:
            pass
    
    def tearDown(self):
        """Clean up after each test"""
        try:
            cache.clear()
        except Exception:
            pass

    def test_set_current_proof_basic(self):
        """Test set_current_proof initializes IndProof engine"""
        print("\n→ Testing set_current_proof initializes IndProof engine...")
        data = {
            'struct': 'int',
            'ivar': 'n',
            'aval': '0',
            'lvar': 'k',
            'lhsPremise': '(+ n 1)',
            'rhsPremise': '(+ 1 n)',
            'definitions': []
        }
        
        response = self.client.post(f'{BASE_URL}set-current-proof', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['isValid'])
        self.assertEqual(response.data['errors'], [])
        self.assertIn('base', response.data)
        self.assertIn('leap', response.data)
        self.assertIn('LHS', response.data['base'])
        self.assertIn('RHS', response.data['base'])

    def test_set_current_proof_missing_fields(self):
        """Test set_current_proof fails with missing fields"""
        print("\n→ Testing set_current_proof validation with missing fields...")
        data = {
            'struct': 'int',
            'ivar': 'n'
        }
        
        response = self.client.post(f'{BASE_URL}set-current-proof', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['isValid'])
        self.assertIn('errors', response.data)

    def test_apply_rule_base_lhs(self):
        """Test apply_rule on base case LHS"""
        print("\n→ Testing apply_rule on base case LHS...")
        # First initialize proof
        init_data = {
            'struct': 'int',
            'ivar': 'n',
            'aval': '0',
            'lvar': 'k',
            'lhsPremise': '(+ 0 1)',
            'rhsPremise': '1',
            'definitions': []
        }
        self.client.post(f'{BASE_URL}set-current-proof', init_data, format='json')
        
        # Apply a rule
        rule_data = {
            'case': 'base',
            'side': 'LHS',
            'currentRacket': '(+ 0 1)',
            'rule': 'math',
            'startPosition': 0
        }
        
        response = self.client.post(f'{BASE_URL}apply-rule', rule_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('isValid', response.data)
        self.assertIn('racket', response.data)
        self.assertIn('jsonTree', response.data)

    def test_check_goal_base_lhs(self):
        """Test check_goal sets new goal for base LHS"""
        print("\n→ Testing check_goal sets new goal for base LHS...")
        # Initialize proof
        init_data = {
            'struct': 'int',
            'ivar': 'n',
            'aval': '0',
            'lvar': 'k',
            'lhsPremise': '(+ n 1)',
            'rhsPremise': '1',
            'definitions': []
        }
        self.client.post(f'{BASE_URL}set-current-proof', init_data, format='json')
        
        # Set new goal
        goal_data = {
            'case': 'base',
            'side': 'LHS',
            'goal': '(+ 0 2)'
        }
        
        response = self.client.post(f'{BASE_URL}check-goal', goal_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['isValid'])
        self.assertIn('jsonTree', response.data)

    def test_delete_line_base_lhs(self):
        """Test delete_line removes last proof line"""
        print("\n→ Testing delete_line removes last proof line...")
        # Initialize proof
        init_data = {
            'struct': 'int',
            'ivar': 'n',
            'aval': '0',
            'lvar': 'k',
            'lhsPremise': '(+ 0 1)',
            'rhsPremise': '1',
            'definitions': []
        }
        self.client.post(f'{BASE_URL}set-current-proof', init_data, format='json')
        
        # Delete a line
        response = self.client.delete(f'{BASE_URL}delete-line/base/LHS')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_substitution_leap_rhs(self):
        """Test substitution with extra expression"""
        print("\n→ Testing substitution with extra expression on leap RHS...")
        # Initialize proof
        init_data = {
            'struct': 'int',
            'ivar': 'n',
            'aval': '0',
            'lvar': 'k',
            'lhsPremise': '(+ n 1)',
            'rhsPremise': '(+ 1 n)',
            'definitions': []
        }
        self.client.post(f'{BASE_URL}set-current-proof', init_data, format='json')
        
        # Apply substitution
        sub_data = {
            'case': 'leap',
            'side': 'RHS',
            'currentRacket': '(+ 1 (+ k 1))',
            'rule': 'math',
            'startPosition': 0,
            'substitution': 'k'
        }
        
        response = self.client.post(f'{BASE_URL}substitution', sub_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('isValid', response.data)
        self.assertIn('racket', response.data)

    def test_imports_load_correctly(self):
        """Test that all new view functions can be imported"""
        print("\n→ Testing all view functions import successfully...")
        try:
            from induction_api.views import (
                set_current_proof,
                apply_rule,
                delete_line,
                check_goal,
                substitution
            )
            imported = True
        except ImportError:
            imported = False
        
        self.assertTrue(imported, "All induction endpoint functions should import successfully")

    def test_url_patterns_registered(self):
        """Test that all URL patterns are correctly registered"""
        print("\n→ Testing all URL patterns are registered...")
        from induction_api import urls
        
        endpoint_names = [p.name for p in urls.urlpatterns]
        
        required_endpoints = [
            'set_current_proof',
            'apply_rule',
            'delete_line',
            'check_goal',
            'substitution'
        ]
        
        for endpoint in required_endpoints:
            self.assertIn(endpoint, endpoint_names, f"{endpoint} should be in URL patterns")