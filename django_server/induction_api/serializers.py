from rest_framework import serializers
from .models import InductionProof
import re


class InductionProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = InductionProof
        fields = [
            'id', 'user', 'proof_type', 'name', 'tag',
            'induction_variable', 'anchor_value', 'leap_variable',
            'lhs_leap_goal', 'rhs_leap_goal', 
            'lhs_anchor_goal', 'rhs_anchor_goal',
            'induction_type', 'current_side', 'is_anchor_case',
            'current_goal', 'is_valid', 'definition', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_anchor_value(self, value):
        """Validate that anchor value is a non-negative integer"""
        if value < 0:
            raise serializers.ValidationError(
                "Anchor value must be a non-negative integer."
            )
        return value
    
    def validate_leap_variable(self, value):
        """Validate that leap variable is a valid identifier"""
        if not value:
            raise serializers.ValidationError(
                "Leap variable cannot be empty."
            )
        
        # Check if it's a valid Python identifier
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError(
                "Leap variable must be a valid identifier (letters, numbers, underscores; cannot start with a number)."
            )
        
        return value
    
    def validate_induction_variable(self, value):
        """Validate that induction variable is a valid identifier"""
        if not value:
            raise serializers.ValidationError(
                "Induction variable cannot be empty."
            )
        
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError(
                "Induction variable must be a valid identifier."
            )
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        induction_var = data.get('induction_variable')
        leap_var = data.get('leap_variable')
        lhs_expr = data.get('lhs_expression', '')
        rhs_expr = data.get('rhs_expression', '')
        
        # Validate induction variable is in LHS or RHS
        if induction_var:
            if induction_var not in lhs_expr and induction_var not in rhs_expr:
                raise serializers.ValidationError({
                    'induction_variable': f"Induction variable '{induction_var}' must be used in either LHS or RHS expression."
                })
        
        # Validate leap variable is unique (not same as induction variable)
        if leap_var and induction_var and leap_var == induction_var:
            raise serializers.ValidationError({
                'leap_variable': f"Leap variable '{leap_var}' must be different from induction variable '{induction_var}'."
            })
        
        # Check that leap variable is not already used in expressions
        if leap_var:
            if leap_var in lhs_expr or leap_var in rhs_expr:
                raise serializers.ValidationError({
                    'leap_variable': f"Leap variable '{leap_var}' is already used in the expressions. Choose a unique variable name."
                })
        
        return data


class InductionProofCreateSerializer(serializers.Serializer):
    """Serializer for creating a new induction proof"""
    
    induction_variable = serializers.CharField(max_length=100)
    anchor_value = serializers.IntegerField(min_value=0)
    leap_variable = serializers.CharField(max_length=100)
    lhs_expression = serializers.CharField()
    rhs_expression = serializers.CharField()
    
    def validate_anchor_value(self, value):
        """Validate that anchor value is a non-negative integer"""
        if value < 0:
            raise serializers.ValidationError(
                "Anchor value must be a non-negative integer."
            )
        return value
    
    def validate_leap_variable(self, value):
        """Validate that leap variable is a valid identifier"""
        if not value:
            raise serializers.ValidationError(
                "Leap variable cannot be empty."
            )
        
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError(
                "Leap variable must be a valid identifier (letters, numbers, underscores; cannot start with a number)."
            )
        
        return value
    
    def validate_induction_variable(self, value):
        """Validate that induction variable is a valid identifier"""
        if not value:
            raise serializers.ValidationError(
                "Induction variable cannot be empty."
            )
        
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError(
                "Induction variable must be a valid identifier."
            )
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        induction_var = data.get('induction_variable')
        leap_var = data.get('leap_variable')
        lhs_expr = data.get('lhs_expression', '')
        rhs_expr = data.get('rhs_expression', '')
        
        # Validate induction variable is in LHS or RHS
        if induction_var:
            # More robust check for variable usage
            var_pattern = r'\b' + re.escape(induction_var) + r'\b'
            if not re.search(var_pattern, lhs_expr) and not re.search(var_pattern, rhs_expr):
                raise serializers.ValidationError({
                    'induction_variable': f"Induction variable '{induction_var}' must be used in either LHS or RHS expression."
                })
        
        # Validate leap variable is unique (not same as induction variable)
        if leap_var and induction_var and leap_var == induction_var:
            raise serializers.ValidationError({
                'leap_variable': f"Leap variable '{leap_var}' must be different from induction variable '{induction_var}'."
            })
        
        # Check that leap variable is not already used in expressions
        if leap_var:
            var_pattern = r'\b' + re.escape(leap_var) + r'\b'
            if re.search(var_pattern, lhs_expr) or re.search(var_pattern, rhs_expr):
                raise serializers.ValidationError({
                    'leap_variable': f"Leap variable '{leap_var}' is already used in the expressions. Choose a unique variable name."
                })
        
        return data