"""
Test suite for verifying proof line database persistence
Run with: python manage.py test induction_api.test_database_persistence
"""

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache
from .models import InductionProof, InductionProofLine

User = get_user_model()


class ProofLineDatabasePersistenceTests(TransactionTestCase):
    """Test that proof lines are correctly persisted to database with rules"""
    
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
    
    def test_manual_proof_line_creation(self):
        """Test manually creating proof lines to verify model works correctly"""
        print("\n→ Testing manual proof line creation...")
        
        # Create a proof
        proof = InductionProof.objects.create(
            user=self.user,
            name='Manual Test Proof',
            tag='manual-test',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_anchor_goal='(sum 0)',
            rhs_anchor_goal='0',
            lhs_leap_goal='(sum (+ k 1))',
            rhs_leap_goal='(+ (sum k) (+ k 1))'
        )
        
        # Create proof lines
        line1 = InductionProofLine.objects.create(
            proof=proof,
            case='base',
            side='LHS',
            racket='(sum 0)',
            rule='Premise',
            start_position=0,
            line_number=0
        )
        
        line2 = InductionProofLine.objects.create(
            proof=proof,
            case='base',
            side='LHS',
            racket='0',
            rule='eval sum',
            start_position=0,
            line_number=1
        )
        
        line3 = InductionProofLine.objects.create(
            proof=proof,
            case='base',
            side='RHS',
            racket='0',
            rule='rewrite math with 0',
            start_position=0,
            line_number=0
        )
        
        # Verify lines were created
        self.assertEqual(InductionProofLine.objects.filter(proof=proof).count(), 3)
        
        # Verify specific rules
        eval_line = InductionProofLine.objects.filter(proof=proof, rule__icontains='eval sum').first()
        self.assertIsNotNone(eval_line, "No 'eval sum' rule found")
        self.assertEqual(eval_line.rule, 'eval sum')
        
        math_line = InductionProofLine.objects.filter(proof=proof, rule__icontains='rewrite math').first()
        self.assertIsNotNone(math_line, "No 'rewrite math' rule found")
        self.assertIn('rewrite math', math_line.rule)
        self.assertIn('with', math_line.rule)
        
        print(f"✓ Created {InductionProofLine.objects.filter(proof=proof).count()} proof lines")
        print(f"✓ Verified 'eval sum' rule: {eval_line.rule}")
        print(f"✓ Verified 'rewrite math' rule: {math_line.rule}")
    
    def test_apply_rule_saves_to_database(self):
        """Test that apply-rule endpoint saves proof lines to database"""
        print("\n→ Testing apply-rule saves to database...")
        
        # Create a proof in database first
        proof = InductionProof.objects.create(
            user=self.user,
            name='Apply Rule Test',
            tag='apply-test',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_anchor_goal='(+ 0 1)',
            rhs_anchor_goal='1'
        )
        
        # Initialize the engine
        init_data = {
            'struct': 'int',
            'ivar': 'n',
            'aval': '0',
            'lvar': 'k',
            'lhsPremise': '(+ 0 1)',
            'rhsPremise': '1',
            'definitions': []
        }
        
        response = self.client.post('/api/v1/induction/set-current-proof', init_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Update cache to link proof_id
        from .views import get_or_set_induction_obj, save_induction_obj_to_cache
        ind_proof, _ = get_or_set_induction_obj(self.user)
        save_induction_obj_to_cache(self.user, ind_proof, proof.id)
        
        # Apply a rule
        rule_data = {
            'case': 'base',
            'side': 'LHS',
            'currentRacket': '(+ 0 1)',
            'rule': 'eval +',
            'startPosition': 0
        }
        
        response = self.client.post('/api/v1/induction/apply-rule', rule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('isValid'), "Rule application was not valid")
        
        # Verify proof line was saved to database
        proof_lines = InductionProofLine.objects.filter(proof=proof, case='base', side='LHS')
        self.assertGreater(proof_lines.count(), 0, "No proof lines were saved to database")
        
        # Find line with the rule
        rule_line = proof_lines.filter(rule__icontains='eval').first()
        self.assertIsNotNone(rule_line, "No line with eval rule found")
        
        print(f"✓ Saved {proof_lines.count()} proof line(s) to database")
        print(f"✓ Rule saved: {rule_line.rule}")
    
    def test_substitution_saves_to_database(self):
        """Test that substitution endpoint saves proof lines with correct rule names"""
        print("\n→ Testing substitution saves to database with correct rule...")
        
        # Create a proof
        proof = InductionProof.objects.create(
            user=self.user,
            name='Substitution Test',
            tag='sub-test',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_anchor_goal='(+ 0 1)',
            rhs_anchor_goal='1'
        )
        
        # Initialize engine
        init_data = {
            'struct': 'int',
            'ivar': 'n',
            'aval': '0',
            'lvar': 'k',
            'lhsPremise': '(+ 0 1)',
            'rhsPremise': '(* 0 2)',
            'definitions': []
        }
        
        response = self.client.post('/api/v1/induction/set-current-proof', init_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Link proof_id in cache
        from .views import get_or_set_induction_obj, save_induction_obj_to_cache
        ind_proof, _ = get_or_set_induction_obj(self.user)
        save_induction_obj_to_cache(self.user, ind_proof, proof.id)
        
        # Apply substitution with "math" rule
        sub_data = {
            'case': 'base',
            'side': 'RHS',
            'currentRacket': '(* 0 2)',
            'rule': 'math',  # This should be converted to "rewrite math"
            'substitution': '0',
            'startPosition': 0
        }
        
        response = self.client.post('/api/v1/induction/substitution', sub_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('isValid'), "Substitution was not valid")
        
        # Verify proof line was saved with correct rule
        proof_lines = InductionProofLine.objects.filter(proof=proof, case='base', side='RHS')
        self.assertGreater(proof_lines.count(), 0, "No proof lines were saved")
        
        # Verify rule name includes "rewrite math" and substitution
        math_line = proof_lines.filter(rule__icontains='rewrite math').first()
        self.assertIsNotNone(math_line, "No line with 'rewrite math' rule found")
        self.assertIn('rewrite math', math_line.rule, f"Expected 'rewrite math', got: {math_line.rule}")
        self.assertIn('with', math_line.rule, f"Expected 'with' in rule, got: {math_line.rule}")
        self.assertIn('as', math_line.rule, f"Expected 'as' in rule, got: {math_line.rule}")
        self.assertIn('0', math_line.rule, f"Expected substitution value in rule, got: {math_line.rule}")
        
        print(f"✓ Saved {proof_lines.count()} proof line(s)")
        print(f"✓ Rule correctly saved as: {math_line.rule}")
    
    def test_delete_line_removes_from_database(self):
        """Test that delete-line endpoint removes proof lines from database"""
        print("\n→ Testing delete-line removes from database...")
        
        # Create proof
        proof = InductionProof.objects.create(
            user=self.user,
            name='Delete Test',
            tag='delete-test',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_anchor_goal='(+ 0 1)',
            rhs_anchor_goal='1'
        )
        
        # Initialize engine
        init_data = {
            'struct': 'int',
            'ivar': 'n',
            'aval': '0',
            'lvar': 'k',
            'lhsPremise': '(+ 0 1)',
            'rhsPremise': '1',
            'definitions': []
        }
        
        response = self.client.post('/api/v1/induction/set-current-proof', init_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Link proof_id
        from .views import get_or_set_induction_obj, save_induction_obj_to_cache
        ind_proof, _ = get_or_set_induction_obj(self.user)
        save_induction_obj_to_cache(self.user, ind_proof, proof.id)
        
        # Apply a rule to create a line
        rule_data = {
            'case': 'base',
            'side': 'LHS',
            'currentRacket': '(+ 0 1)',
            'rule': 'eval +',
            'startPosition': 0
        }
        
        response = self.client.post('/api/v1/induction/apply-rule', rule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Count lines before delete
        lines_before = InductionProofLine.objects.filter(proof=proof, case='base', side='LHS').count()
        self.assertGreater(lines_before, 0, "No lines saved before delete")
        
        # Delete the line
        response = self.client.delete('/api/v1/induction/delete-line/base/LHS')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify line was removed
        lines_after = InductionProofLine.objects.filter(proof=proof, case='base', side='LHS').count()
        self.assertEqual(lines_after, lines_before - 1, "Line was not removed from database")
        
        print(f"✓ Lines before delete: {lines_before}")
        print(f"✓ Lines after delete: {lines_after}")
        print(f"✓ Successfully removed line from database")
    
    def test_proof_line_organization(self):
        """Test that proof lines are properly organized by case, side, and line number"""
        print("\n→ Testing proof line organization...")
        
        proof = InductionProof.objects.create(
            user=self.user,
            name='Organization Test',
            tag='org-test',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_anchor_goal='(sum 0)',
            rhs_anchor_goal='0'
        )
        
        # Create lines for different cases and sides
        test_lines = [
            {'case': 'base', 'side': 'LHS', 'line_number': 0, 'rule': 'Premise'},
            {'case': 'base', 'side': 'LHS', 'line_number': 1, 'rule': 'eval sum'},
            {'case': 'base', 'side': 'RHS', 'line_number': 0, 'rule': 'Premise'},
            {'case': 'leap', 'side': 'LHS', 'line_number': 0, 'rule': 'Premise'},
            {'case': 'leap', 'side': 'RHS', 'line_number': 0, 'rule': 'Premise'},
        ]
        
        for line_data in test_lines:
            InductionProofLine.objects.create(
                proof=proof,
                racket='test',
                start_position=0,
                **line_data
            )
        
        # Verify organization
        base_lhs = InductionProofLine.objects.filter(proof=proof, case='base', side='LHS').count()
        base_rhs = InductionProofLine.objects.filter(proof=proof, case='base', side='RHS').count()
        leap_lhs = InductionProofLine.objects.filter(proof=proof, case='leap', side='LHS').count()
        leap_rhs = InductionProofLine.objects.filter(proof=proof, case='leap', side='RHS').count()
        
        self.assertEqual(base_lhs, 2, "Wrong number of base LHS lines")
        self.assertEqual(base_rhs, 1, "Wrong number of base RHS lines")
        self.assertEqual(leap_lhs, 1, "Wrong number of leap LHS lines")
        self.assertEqual(leap_rhs, 1, "Wrong number of leap RHS lines")
        
        # Verify ordering
        ordered_lines = InductionProofLine.objects.filter(
            proof=proof, case='base', side='LHS'
        ).order_by('line_number')
        
        line_numbers = [line.line_number for line in ordered_lines]
        self.assertEqual(line_numbers, [0, 1], "Lines not properly ordered")
        
        print(f"✓ Base LHS: {base_lhs} lines")
        print(f"✓ Base RHS: {base_rhs} lines")
        print(f"✓ Leap LHS: {leap_lhs} lines")
        print(f"✓ Leap RHS: {leap_rhs} lines")
        print(f"✓ Line ordering verified: {line_numbers}")
    
    def test_admin_relationship(self):
        """Test that proof lines are accessible through proof relationship"""
        print("\n→ Testing proof-to-lines relationship...")
        
        proof = InductionProof.objects.create(
            user=self.user,
            name='Relationship Test',
            tag='rel-test',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_anchor_goal='(sum 0)',
            rhs_anchor_goal='0'
        )
        
        # Create some lines
        for i in range(3):
            InductionProofLine.objects.create(
                proof=proof,
                case='base',
                side='LHS',
                racket=f'line {i}',
                rule=f'rule {i}',
                start_position=0,
                line_number=i
            )
        
        # Access lines through relationship
        lines = proof.proof_lines.all()
        self.assertEqual(lines.count(), 3, "Wrong number of related lines")
        
        # Test filtering through relationship
        rule_0_lines = proof.proof_lines.filter(rule='rule 0')
        self.assertEqual(rule_0_lines.count(), 1, "Filtering through relationship failed")
        
        print(f"✓ Accessed {lines.count()} lines through proof.proof_lines")
        print(f"✓ Filtered lines through relationship")
