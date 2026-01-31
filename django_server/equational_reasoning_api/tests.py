from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import EquationalProof, EquationalProofLine
from .serializers import EquationalProofSerializer

User = get_user_model()


class EquationalProofModelTests(TestCase):
    """Test the EquationalProof model"""
    
    def setUp(self):
        """Create a test user for all tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_equational_proof(self):
        """Test creating an EquationalProof object"""
        proof = EquationalProof.objects.create(
            user=self.user,
            name='Test Proof',
            tag='test',
            lhs_goal='(+ 1 2)',
            rhs_goal='3'
        )
        self.assertEqual(proof.user, self.user)
        self.assertEqual(proof.name, 'Test Proof')
        self.assertEqual(proof.tag, 'test')
        self.assertEqual(proof.lhs_goal, '(+ 1 2)')
        self.assertEqual(proof.rhs_goal, '3')
        self.assertEqual(proof.current_side, 'LHS')  # default
        self.assertTrue(proof.is_valid)  # default
        self.assertFalse(proof.is_complete)  # default
        self.assertTrue(proof.is_active)  # default
    
    def test_proof_str_representation(self):
        """Test the string representation of a proof"""
        proof = EquationalProof.objects.create(
            user=self.user,
            name='My Proof',
            lhs_goal='(+ 1 2)',
            rhs_goal='3'
        )
        self.assertEqual(str(proof), 'My Proof - Equational Reasoning')
        
        # Test without name
        proof_no_name = EquationalProof.objects.create(
            user=self.user,
            lhs_goal='(+ 1 2)',
            rhs_goal='3'
        )
        self.assertIn('Equational Proof', str(proof_no_name))
        self.assertIn('testuser', str(proof_no_name))
    
    def test_proof_defaults(self):
        """Test that model defaults are set correctly"""
        proof = EquationalProof.objects.create(
            user=self.user,
            lhs_goal='(+ 1 2)',
            rhs_goal='3'
        )
        self.assertEqual(proof.current_side, 'LHS')
        self.assertTrue(proof.is_valid)
        self.assertFalse(proof.is_complete)
        self.assertTrue(proof.is_active)
        self.assertEqual(proof.definition, [])


class EquationalProofLineModelTests(TestCase):
    """Test the EquationalProofLine model"""
    
    def setUp(self):
        """Create a test user and proof"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.proof = EquationalProof.objects.create(
            user=self.user,
            name='Test Proof',
            lhs_goal='(+ 1 2)',
            rhs_goal='3'
        )
    
    def test_create_proof_line(self):
        """Test creating a proof line"""
        line = EquationalProofLine.objects.create(
            proof=self.proof,
            side='LHS',
            racket='(+ 1 2)',
            line_number=0
        )
        self.assertEqual(line.proof, self.proof)
        self.assertEqual(line.side, 'LHS')
        self.assertEqual(line.racket, '(+ 1 2)')
        self.assertEqual(line.line_number, 0)
        self.assertEqual(line.rule, '')  # default
        self.assertEqual(line.start_position, 0)  # default
        self.assertEqual(line.selected_node, 0)  # default
        self.assertEqual(line.result_node, 0)  # default
    
    def test_proof_line_str_representation(self):
        """Test the string representation of a proof line"""
        line = EquationalProofLine.objects.create(
            proof=self.proof,
            side='RHS',
            racket='(+ 1 2)',
            line_number=5
        )
        self.assertEqual(str(line), 'RHS Line 5: (+ 1 2)')
    
    def test_unique_constraint(self):
        """Test that duplicate proof lines (same proof, side, line_number) are prevented"""
        EquationalProofLine.objects.create(
            proof=self.proof,
            side='LHS',
            line_number=0,
            racket='(+ 1 2)'
        )
        
        # Try to create duplicate
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            EquationalProofLine.objects.create(
                proof=self.proof,
                side='LHS',
                line_number=0,  # Same as above
                racket='3'
            )


class EquationalProofSerializerTests(TestCase):
    """Test the EquationalProofSerializer"""
    
    def test_valid_data(self):
        """Test serializer with valid data"""
        data = {
            'lhs_goal': '(+ 1 2)',
            'rhs_goal': '3',
            'name': 'Test Proof',
            'tag': 'demo'
        }
        serializer = EquationalProofSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['lhs_goal'], '(+ 1 2)')
        self.assertEqual(serializer.validated_data['rhs_goal'], '3')
    
    def test_empty_lhs_goal(self):
        """Test that empty LHS goal is rejected"""
        data = {
            'lhs_goal': '',
            'rhs_goal': '3'
        }
        serializer = EquationalProofSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('lhs_goal', serializer.errors)
    
    def test_empty_rhs_goal(self):
        """Test that empty RHS goal is rejected"""
        data = {
            'lhs_goal': '(+ 1 2)',
            'rhs_goal': ''
        }
        serializer = EquationalProofSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('rhs_goal', serializer.errors)
    
    def test_whitespace_stripped(self):
        """Test that whitespace is stripped from goals"""
        data = {
            'lhs_goal': '  (+ 1 2)  ',
            'rhs_goal': '  3  '
        }
        serializer = EquationalProofSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['lhs_goal'], '(+ 1 2)')
        self.assertEqual(serializer.validated_data['rhs_goal'], '3')
    
    def test_identical_goals_rejected(self):
        """Test that identical LHS and RHS goals are rejected"""
        data = {
            'lhs_goal': '(+ 1 2)',
            'rhs_goal': '(+ 1 2)'
        }
        serializer = EquationalProofSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('rhs_goal', serializer.errors)
