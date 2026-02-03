"""
Integration test to verify proof lines are saved to database with correct rules
"""
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.core.cache import cache
from .models import InductionProof, InductionProofLine

User = get_user_model()


class ProofLinePersistenceTest(TransactionTestCase):
    """Test that proof lines are correctly persisted to database"""
    
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
    
    def test_proof_lines_saved_with_rules(self):
        """Test that applying rules saves proof lines to database with correct rule names"""
        
        # 1. Create an induction proof (using simple math instead of custom functions)
        proof_data = {
            'proof_name': 'Test Proof',
            'proof_tag': 'test-tag',
            'lhs_leap_goal': '(+ n 1)',
            'rhs_leap_goal': '(+ 1 n)',
            'lhs_anchor_goal': '(+ 0 1)',
            'rhs_anchor_goal': '(+ 1 0)',
            'induction_variable': 'n',
            'anchor_value': '0',
            'leap_variable': 'k',
            'induction_type': 'integers',
            'inductive_hypothesis_lhs': '(+ k 1)',
            'inductive_hypothesis_rhs': '(+ 1 k)'
        }
        
        response = self.client.post('/api/v1/induction/start-induction-proof', proof_data)
        self.assertEqual(response.status_code, 201, f"Failed to start proof: {response.data}")
        proof_id = response.data.get('proof_id')
        self.assertIsNotNone(proof_id, "No proof_id returned")
        
        # 2. Set current proof (engine initialization)
        engine_data = {
            'struct': 'int',
            'ivar': 'n',
            'aval': '0',
            'lvar': 'k',
            'lhsPremise': '(+ n 1)',
            'rhsPremise': '(+ 1 n)',
            'definitions': []
        }
        
        response = self.client.post('/api/v1/induction/set-current-proof', engine_data)
        self.assertEqual(response.status_code, 201, f"Failed to set current proof: {response.data}")
        
        # 3. Apply a rule on base case LHS
        apply_rule_data = {
            'case': 'base',
            'side': 'LHS',
            'currentRacket': '(+ 0 1)',
            'rule': 'eval +',
            'startPosition': 0
        }
        
        response = self.client.post('/api/v1/induction/apply-rule', apply_rule_data)
        self.assertEqual(response.status_code, 200, f"Failed to apply rule: {response.data}")
        if not response.data.get('isValid'):
            print(f"\n[TEST DEBUG] Apply rule response: {response.data}")
        self.assertTrue(response.data.get('isValid'), "Rule application was not valid")
        
        # 4. Verify proof lines were saved to database
        proof = InductionProof.objects.get(id=proof_id)
        proof_lines = InductionProofLine.objects.filter(proof=proof)
        
        self.assertGreater(proof_lines.count(), 0, "No proof lines were saved to database")
        
        # 5. Verify base case LHS has a line with the rule
        base_lhs_lines = proof_lines.filter(case='base', side='LHS')
        self.assertGreater(base_lhs_lines.count(), 0, "No base LHS lines saved")
        
        # Find the line with the eval + rule
        eval_line = base_lhs_lines.filter(rule__icontains='eval').first()
        self.assertIsNotNone(eval_line, "No line with 'eval' rule found")
        self.assertIn('eval', eval_line.rule, f"Expected 'eval' in rule, got: {eval_line.rule}")
        
        print(f"\n✓ Test passed! Found {proof_lines.count()} proof lines in database")
        print(f"✓ Base LHS rule: {eval_line.rule}")
        
    def test_delete_line_removes_from_database(self):
        """Test that deleting a line removes it from the database"""
        
        # 1. Create proof and setup (using simple math)
        proof_data = {
            'proof_name': 'Delete Test',
            'proof_tag': 'delete-test',
            'lhs_leap_goal': '(+ n 1)',
            'rhs_leap_goal': '(+ 1 n)',
            'lhs_anchor_goal': '(+ 0 1)',
            'rhs_anchor_goal': '(+ 1 0)',
            'induction_variable': 'n',
            'anchor_value': '0',
            'leap_variable': 'k',
            'induction_type': 'integers',
            'inductive_hypothesis_lhs': '(+ k 1)',
            'inductive_hypothesis_rhs': '(+ 1 k)'
        }
        
        response = self.client.post('/api/v1/induction/start-induction-proof', proof_data)
        self.assertEqual(response.status_code, 201)
        proof_id = response.data.get('proof_id')
        
        # 2. Set current proof
        engine_data = {
            'struct': 'int',
            'ivar': 'n',
            'aval': '0',
            'lvar': 'k',
            'lhsPremise': '(+ n 1)',
            'rhsPremise': '(+ 1 n)',
            'definitions': []
        }
        
        response = self.client.post('/api/v1/induction/set-current-proof', engine_data)
        self.assertEqual(response.status_code, 201)
        
        # 3. Apply a rule
        apply_rule_data = {
            'case': 'base',
            'side': 'LHS',
            'currentRacket': '(+ 0 1)',
            'rule': 'eval +',
            'startPosition': 0
        }
        
        response = self.client.post('/api/v1/induction/apply-rule', apply_rule_data)
        self.assertEqual(response.status_code, 200)
        
        # 4. Verify line was saved
        proof = InductionProof.objects.get(id=proof_id)
        lines_before = InductionProofLine.objects.filter(proof=proof, case='base', side='LHS').count()
        self.assertGreater(lines_before, 0, "No lines saved before delete")
        
        # 5. Delete line 1 (the generated line after the premise at line 0)
        response = self.client.delete('/api/v1/induction/delete-line/base/LHS/1')
        self.assertEqual(response.status_code, 200)
        
        # 6. Verify line was cleared (not removed - the record still exists but is empty)
        lines_after = InductionProofLine.objects.filter(proof=proof, case='base', side='LHS').count()
        self.assertEqual(lines_after, lines_before, "Line count should stay the same (cleared, not removed)")
        
        # Verify the line is now empty
        cleared_line = InductionProofLine.objects.get(proof=proof, case='base', side='LHS', line_number=1)
        self.assertEqual(cleared_line.racket, '', "Cleared line should have empty racket")
        self.assertEqual(cleared_line.rule, '', "Cleared line should have empty rule")
        
        print(f"\n✓ Delete test passed! Lines before: {lines_before}, after: {lines_after}")
