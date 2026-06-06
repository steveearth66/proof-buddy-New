# models.py - Add visibility fields to EquationalProofLine

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class EquationalProof(models.Model):
    """
    Stores equational reasoning proofs - a two-sided proof showing LHS = RHS.
    Simpler than induction proofs: no base/leap cases, no induction variables.
    """
    
    SIDES = [
        ('LHS', 'Left Hand Side'),
        ('RHS', 'Right Hand Side'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='equational_proofs', null=True, blank=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    tag = models.CharField(max_length=100, blank=True, null=True)
    
    # Goals
    lhs_goal = models.TextField()
    rhs_goal = models.TextField()
    
    # Current state
    current_side = models.CharField(max_length=3, choices=SIDES, default='LHS')
    
    # Validation
    is_valid = models.BooleanField(default=True)
    is_complete = models.BooleanField(default=False)
    definition = models.JSONField(default=list)
    
    # Support parameters (instructor-configurable, all default to True = high support)
    support_errors = models.BooleanField(default=True)
    support_current_lhs_rhs = models.BooleanField(default=True)
    support_ih = models.BooleanField(default=True)
    support_premise = models.BooleanField(default=True)
    support_rule_set = models.BooleanField(default=True)
    visible_rules = models.TextField(default=dict, blank=True)
    support_value_mapping = models.BooleanField(default=True)
    support_rewrite_complexity = models.BooleanField(default=True)
    support_rewrite_complexity = models.BooleanField(default=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # Soft delete: False = archived
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'name', 'tag', 'is_active']),
        ]
    
    def __str__(self):
        if self.name:
            # Add a tag to make it obvious in the admin panel
            suffix = "" if self.user else " [Template]" 
            return f"{self.name}{suffix} - Equational Reasoning"
            
        # Safely handle the missing user
        owner = self.user.username if self.user else "Assignment Template"
        return f"Equational Proof - {owner}"


class EquationalProofLine(models.Model):
    """
    Stores individual proof lines for equational reasoning proofs.
    Each line represents a step on either LHS or RHS.
    """
    
    SIDE_CHOICES = [
        ('LHS', 'Left Hand Side'),
        ('RHS', 'Right Hand Side'),
    ]
    
    proof = models.ForeignKey(
        EquationalProof, 
        related_name='proof_lines', 
        on_delete=models.CASCADE
    )
    side = models.CharField(max_length=3, choices=SIDE_CHOICES)
    racket = models.TextField()  # The expression in racket notation
    json_tree = models.JSONField(default=dict, blank=True)  # Parsed expression tree for frontend rendering
    rule = models.CharField(max_length=255, blank=True, default='')  # The rule that was applied
    substitution = models.TextField(blank=True, default='')  # Substitution payload if any
    start_position = models.IntegerField(default=0)  # Position where rule was applied
    selected_node = models.IntegerField(default=0)  # Node ID selected by user for rule application
    result_node = models.IntegerField(default=0)  # Node ID of the changed portion in the result expression
    line_number = models.IntegerField(default=0)  # Order of line in the proof
    created_at = models.DateTimeField(auto_now_add=True)
    errors = models.TextField(blank=True, default='') # Comma separated list of all errors that occured on the line
    
    # NEW: Visibility flags for hiding content from students
    hide_expression = models.BooleanField(default=False)  # If True, hide the racket expression
    hide_justification = models.BooleanField(default=False)  # If True, hide the rule/justification
    
    class Meta:
        ordering = ['side', 'line_number']
        indexes = [
            models.Index(fields=['proof', 'side', 'line_number']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['proof', 'side', 'line_number'],
                name='unique_equational_proof_line'
            ),
        ]
    
    def __str__(self):
        return f"{self.side} Line {self.line_number}: {self.racket[:50]}"
    

class EquationalProofLineComment(models.Model):

    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
    ]

    proof = models.ForeignKey(EquationalProof, related_name='proof_comments', on_delete=models.CASCADE)
    side = models.CharField(max_length=3)    # LHS / RHS
    line_number = models.IntegerField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

