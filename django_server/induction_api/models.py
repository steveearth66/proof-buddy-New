from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class InductionProof(models.Model):
    
    PROOF_TYPES = [
        ('induction_int', 'Integer Induction'),
        ('induction_lists', 'List Induction'),
    ]
    
    INDUCTION_TYPES = [
        ('integers', 'Integers'),
        ('lists', 'Lists'),
    ]
    
    SIDES = [
        ('LHS', 'Left Hand Side'),
        ('RHS', 'Right Hand Side'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='induction_proofs')
    name = models.CharField(max_length=255, blank=True, null=True)
    tag = models.CharField(max_length=100, blank=True, null=True)
    proof_type = models.CharField(max_length=50, choices=PROOF_TYPES, default='induction_int')
    induction_type = models.CharField(max_length=20, choices=INDUCTION_TYPES, default='integers')
    
    # Proof parameters
    induction_variable = models.CharField(max_length=100)
    anchor_value = models.IntegerField()
    leap_variable = models.CharField(max_length=100)
    
    lhs_leap_goal = models.TextField(blank=True, null=True)
    rhs_leap_goal = models.TextField(blank=True, null=True)
    lhs_anchor_goal = models.TextField(blank=True, null=True)
    rhs_anchor_goal = models.TextField(blank=True, null=True)
    
    # Current state
    current_side = models.CharField(max_length=3, choices=SIDES, default='LHS')
    current_goal = models.TextField(blank=True, null=True)
    is_anchor_case = models.BooleanField(default=False)
    
    # Validation
    is_valid = models.BooleanField(default=True)
    definition = models.JSONField(default=list)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['proof_type']),
            models.Index(fields=['induction_type']),
        ]
    
    def __str__(self):
        if self.name:
            return f"{self.name} - {self.proof_type}"
        return f"{self.proof_type} - {self.user.username} - {self.induction_variable}"