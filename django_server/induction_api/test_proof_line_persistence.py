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
        
        # 1. Create an induction proof
        proof_data = {
            'proof_name': 'Test Proof',
            'proof_tag': 'test-tag',
            'lhs_leap_goal': '(sum n)',
            'rhs_leap_goal': '(quotient (* n (+ n 1)) 2)',
            'induction_variable': 'n',
            'anchor_value': '0',
            'leap_variable': 'k',
            'induction_type': 'integers'
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
            'lhsPremise': '(sum n)',
            'rhsPremise': '(quotient (* n (+ n 1)) 2)',
            'definitions': []
        }
        
        response = self.client.post('/api/v1/induction/set-current-proof', engine_data)
        self.assertEqual(response.status_code, 201, f"Failed to set current proof: {response.data}")
        
        # 3. Apply a rule on base case LHS
        apply_rule_data = {
            'case': 'base',
            'side': 'LHS',
            'currentRacket': '(sum 0)',
            'rule': 'eval sum',
            'startPosition': 0
        }
        
        response = self.client.post('/api/v1/induction/apply-rule', apply_rule_data)
        self.assertEqual(response.status_code, 200, f"Failed to apply rule: {response.data}")
        self.assertTrue(response.data.get('isValid'), "Rule application was not valid")
        
        # 4. Apply substitution with "rewrite math"
        substitution_data = {
            'case': 'base',
            'side': 'RHS',
            'currentRacket': '(quotient (* 0 (+ 0 1)) 2)',
            'rule': 'math',
            'substitution': '0',
            'startPosition': 0
        }
        
        response = self.client.post('/api/v1/induction/substitution', substitution_data)
        self.assertEqual(response.status_code, 200, f"Failed to apply substitution: {response.data}")
        self.assertTrue(response.data.get('isValid'), "Substitution was not valid")
        
        # 5. Verify proof lines were saved to database
        proof = InductionProof.objects.get(id=proof_id)
        proof_lines = InductionProofLine.objects.filter(proof=proof)
        
        self.assertGreater(proof_lines.count(), 0, "No proof lines were saved to database")
        
        # 6. Verify base case LHS has a line with the rule
        base_lhs_lines = proof_lines.filter(case='base', side='LHS')
        self.assertGreater(base_lhs_lines.count(), 0, "No base LHS lines saved")
        
        # Find the line with the eval sum rule
        eval_line = base_lhs_lines.filter(rule__icontains='eval sum').first()
        self.assertIsNotNone(eval_line, "No line with 'eval sum' rule found")
        self.assertIn('eval sum', eval_line.rule, f"Expected 'eval sum' in rule, got: {eval_line.rule}")
        
        # 7. Verify base case RHS has a line with "rewrite math"
        base_rhs_lines = proof_lines.filter(case='base', side='RHS')
        self.assertGreater(base_rhs_lines.count(), 0, "No base RHS lines saved")
        
        # Find the line with rewrite math rule
        math_line = base_rhs_lines.filter(rule__icontains='rewrite math').first()
        self.assertIsNotNone(math_line, "No line with 'rewrite math' rule found")
        self.assertIn('rewrite math', math_line.rule, f"Expected 'rewrite math' in rule, got: {math_line.rule}")
        
        # 8. Verify the rule includes the substitution
        self.assertIn('with', math_line.rule, f"Expected 'with' in substitution rule, got: {math_line.rule}")
        self.assertIn('0', math_line.rule, f"Expected substitution value in rule, got: {math_line.rule}")
        
        print(f"\n✓ Test passed! Found {proof_lines.count()} proof lines in database")
        print(f"✓ Base LHS rule: {eval_line.rule}")
        print(f"✓ Base RHS rule: {math_line.rule}")
        
    def test_delete_line_removes_from_database(self):
        """Test that deleting a line removes it from the database"""
        
        # 1. Create proof and setup
        proof_data = {
            'proof_name': 'Delete Test',
            'proof_tag': 'delete-test',
            'lhs_leap_goal': '(sum n)',
            'rhs_leap_goal': '(quotient (* n (+ n 1)) 2)',
            'induction_variable': 'n',
            'anchor_value': '0',
            'leap_variable': 'k',
            'induction_type': 'integers'
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
            'lhsPremise': '(sum n)',
            'rhsPremise': '(quotient (* n (+ n 1)) 2)',
            'definitions': []
        }
        
        response = self.client.post('/api/v1/induction/set-current-proof', engine_data)
        self.assertEqual(response.status_code, 201)
        
        # 3. Apply a rule
        apply_rule_data = {
            'case': 'base',
            'side': 'LHS',
            'currentRacket': '(sum 0)',
            'rule': 'eval sum',
            'startPosition': 0
        }
        
        response = self.client.post('/api/v1/induction/apply-rule', apply_rule_data)
        self.assertEqual(response.status_code, 200)
        
        # 4. Verify line was saved
        proof = InductionProof.objects.get(id=proof_id)
        lines_before = InductionProofLine.objects.filter(proof=proof, case='base', side='LHS').count()
        self.assertGreater(lines_before, 0, "No lines saved before delete")
        
        # 5. Delete the line
        response = self.client.delete('/api/v1/induction/delete-line/base/LHS')
        self.assertEqual(response.status_code, 200)
        
        # 6. Verify line was removed from database
        lines_after = InductionProofLine.objects.filter(proof=proof, case='base', side='LHS').count()
        self.assertEqual(lines_after, lines_before - 1, "Line was not removed from database")
        
        print(f"\n✓ Delete test passed! Lines before: {lines_before}, after: {lines_after}")
