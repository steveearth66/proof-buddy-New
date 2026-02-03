from ast import literal_eval
from rest_framework import serializers

from proofs.models import Generic

from .models import EquationalProof, EquationalProofLine


class EquationalProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquationalProof
        fields = [
            'id', 'user', 'name', 'tag',
            'lhs_goal', 'rhs_goal',
            'current_side', 'is_valid', 'is_complete', 'definition',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_lhs_goal(self, value):
        """Validate that LHS goal is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "LHS goal cannot be empty."
            )
        return value.strip()
    
    def validate_rhs_goal(self, value):
        """Validate that RHS goal is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "RHS goal cannot be empty."
            )
        return value.strip()
    
    def validate(self, data):
        """
        Cross-field validation
        """
        # Ensure LHS and RHS goals are provided
        if 'lhs_goal' in data and 'rhs_goal' in data:
            if data['lhs_goal'] == data['rhs_goal']:
                raise serializers.ValidationError({
                    'rhs_goal': "LHS and RHS goals should not be identical (proof would be trivial)."
                })
        
        return data
