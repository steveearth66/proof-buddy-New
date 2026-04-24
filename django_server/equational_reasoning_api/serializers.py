from rest_framework import serializers

from .models import EquationalProof, EquationalProofLine


class EquationalProofSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquationalProof
        fields = [
            'id', 'user', 'name', 'tag',
            'lhs_goal', 'rhs_goal',
            'current_side', 'is_valid', 'is_complete', 'definition',
            'support_errors', 'support_current_lhs_rhs', 'support_ih',
            'support_premise', 'support_rule_set', 'support_value_mapping',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_lhs_goal(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("LHS goal cannot be empty.")
        return value.strip()

    def validate_rhs_goal(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("RHS goal cannot be empty.")
        return value.strip()

    def validate(self, data):
        lhs = data.get('lhs_goal', '')
        rhs = data.get('rhs_goal', '')
        if lhs and rhs and lhs.strip() == rhs.strip():
            raise serializers.ValidationError("LHS and RHS goals cannot be identical.")
        return data


class EquationalProofLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquationalProofLine
        fields = [
            'id', 'proof', 'side', 'racket', 'json_tree', 'rule',
            'substitution', 'start_position', 'selected_node', 'result_node',
            'line_number', 'errors', 'hide_expression', 'hide_justification',
            'instructor_comment', 'student_comment', 'comment_correct',
        ]
        read_only_fields = ['id', 'proof', 'created_at']
