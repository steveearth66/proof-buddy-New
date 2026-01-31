"""
Tests for induction proof management operations (clear, archive, restore)
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from induction_api.models import InductionProof, InductionProofLine

User = get_user_model()


class ClearProofTestCase(TestCase):
    """Test suite for Clear Proof (soft delete) functionality"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create a test proof
        self.proof_data = {
            'proof_name': 'Test Proof',
            'proof_tag': 'n',
            'induction_variable': 'n',
            'anchor_value': 0,
            'leap_variable': 'k',
            'lhs_leap_goal': '(f n)',
            'rhs_leap_goal': '(quotient (* n (+ n 1)) 2)',
            'lhs_anchor_goal': '(f 0)',
            'rhs_anchor_goal': '0',
            'induction_type': 'integers',
            'side': 'LHS',
            'is_anchor': False,
            'inductive_hypothesis_lhs': '(f k)',
            'inductive_hypothesis_rhs': '(quotient (* k (+ k 1)) 2)'
        }
    
    def test_clear_proof_archives_proof(self):
        """Test that clearing a proof sets is_active to False"""
        # Create a proof
        response = self.client.post('/api/v1/induction/start-induction-proof', self.proof_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify proof exists and is active
        proof = InductionProof.objects.filter(user=self.user, is_active=True).first()
        self.assertIsNotNone(proof)
        self.assertEqual(proof.name, 'Test Proof')
        self.assertTrue(proof.is_active)
        
        # Clear the proof
        clear_response = self.client.post('/api/v1/induction/clear-induction')
        self.assertEqual(clear_response.status_code, status.HTTP_200_OK)
        self.assertIn('message', clear_response.data)
        
        # Verify proof is now archived
        proof.refresh_from_db()
        self.assertFalse(proof.is_active)
        
        # Verify no active proofs remain
        active_proofs = InductionProof.objects.filter(user=self.user, is_active=True)
        self.assertEqual(active_proofs.count(), 0)
    
    def test_clear_proof_preserves_data(self):
        """Test that clearing a proof preserves all proof data in database"""
        # Create a proof
        response = self.client.post('/api/v1/induction/start-induction-proof', self.proof_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        proof = InductionProof.objects.filter(user=self.user, is_active=True).first()
        proof_id = proof.id
        original_name = proof.name
        original_created_at = proof.created_at
        
        # Clear the proof
        self.client.post('/api/v1/induction/clear-induction')
        
        # Verify proof still exists in database with same data
        archived_proof = InductionProof.objects.get(id=proof_id)
        self.assertEqual(archived_proof.name, original_name)
        self.assertEqual(archived_proof.created_at, original_created_at)
        self.assertFalse(archived_proof.is_active)
    
    def test_clear_proof_when_no_active_proof(self):
        """Test clearing when there's no active proof returns gracefully"""
        response = self.client.post('/api/v1/induction/clear-induction')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Message could be either "No active proof found" or "Induction proof cleared successfully"
        self.assertIn('message', response.data)
    
    def test_multiple_proofs_same_name_after_clear(self):
        """Test that users can create multiple proofs with same name after clearing"""
        # Create first proof
        response1 = self.client.post('/api/v1/induction/start-induction-proof', self.proof_data)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        proof1_id = InductionProof.objects.filter(user=self.user, is_active=True).first().id
        
        # Clear it
        self.client.post('/api/v1/induction/clear-induction')
        
        # Create second proof with same name
        response2 = self.client.post('/api/v1/induction/start-induction-proof', self.proof_data)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Verify both proofs exist
        all_proofs = InductionProof.objects.filter(user=self.user, name='Test Proof')
        self.assertEqual(all_proofs.count(), 2)
        
        # Verify only one is active
        active_proofs = all_proofs.filter(is_active=True)
        self.assertEqual(active_proofs.count(), 1)
        
        # Verify the active one is the second proof
        self.assertNotEqual(active_proofs.first().id, proof1_id)
    
    def test_clear_proof_with_proof_lines(self):
        """Test that clearing a proof with proof lines preserves all line data"""
        # Create a proof
        response = self.client.post('/api/v1/induction/start-induction-proof', self.proof_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        proof = InductionProof.objects.filter(user=self.user, is_active=True).first()
        
        # Add some proof lines manually
        InductionProofLine.objects.create(
            proof=proof,
            case='leap',
            side='LHS',
            racket='(f k)',
            rule='Premise',
            line_number=0,
            selected_node=0,
            result_node=0
        )
        InductionProofLine.objects.create(
            proof=proof,
            case='leap',
            side='LHS',
            racket='(+ (f k) (+ k 1))',
            rule='apply f',
            line_number=1,
            selected_node=0,
            result_node=0
        )
        
        # Clear the proof
        self.client.post('/api/v1/induction/clear-induction')
        
        # Verify proof lines still exist
        lines = InductionProofLine.objects.filter(proof=proof)
        self.assertEqual(lines.count(), 2)
        
        # Verify line data is preserved
        first_line = lines.filter(line_number=0).first()
        self.assertEqual(first_line.racket, '(f k)')
        self.assertEqual(first_line.rule, 'Premise')
    
    def test_different_users_independent_clear(self):
        """Test that clearing one user's proof doesn't affect another user's proof"""
        # Create proof for first user
        response1 = self.client.post('/api/v1/induction/start-induction-proof', self.proof_data)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Create second user
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user2)
        
        # Create proof for second user
        response2 = self.client.post('/api/v1/induction/start-induction-proof', self.proof_data)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Clear second user's proof
        self.client.post('/api/v1/induction/clear-induction')
        
        # Verify first user's proof is still active
        user1_proof = InductionProof.objects.filter(user=self.user, is_active=True).first()
        self.assertIsNotNone(user1_proof)
        self.assertTrue(user1_proof.is_active)
        
        # Verify second user's proof is archived
        user2_proof = InductionProof.objects.filter(user=user2).first()
        self.assertFalse(user2_proof.is_active)


def run_tests():
    """Helper function to run these tests"""
    import sys
    from django.core.management import call_command
    
    # Run just this test file
    call_command('test', 'induction_api.test_proof_management', verbosity=2)


if __name__ == '__main__':
    run_tests()
