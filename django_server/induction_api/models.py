# models.py - InductionProof and InductionProofLine models
# Added: instructor_comment, student_comment, comment_correct fields

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

    induction_variable = models.CharField(max_length=100)
    anchor_value = models.CharField(max_length=100)
    leap_variable = models.CharField(max_length=100, blank=True, null=True)

    base_lhs_goal = models.TextField()
    base_rhs_goal = models.TextField()
    leap_lhs_goal = models.TextField(blank=True, default='')
    leap_rhs_goal = models.TextField(blank=True, default='')

    ih_racket = models.TextField(blank=True, default='')
    ih_json_tree = models.JSONField(default=dict, blank=True)

    current_side = models.CharField(max_length=3, choices=SIDES, default='LHS')
    current_case = models.CharField(max_length=10, default='base')
    is_complete = models.BooleanField(default=False)
    definition = models.JSONField(default=list)

    support_errors = models.BooleanField(default=True)
    support_current_lhs_rhs = models.BooleanField(default=True)
    support_ih = models.BooleanField(default=True)
    support_premise = models.BooleanField(default=True)
    support_rule_set = models.BooleanField(default=True)
    support_value_mapping = models.BooleanField(default=True)
    support_rewrite_complexity = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
        models.Index(fields=['user', '-created_at']),
        models.Index(fields=['proof_type']),
        models.Index(fields=['induction_type']),
        models.Index(fields=['user', 'name', 'tag', 'is_active']),
        ]

    def __str__(self):
        return f'{self.name} - Induction ({self.proof_type})'


class InductionProofLine(models.Model):

    CASE_CHOICES = [
    ('base', 'Base Case'),
    ('leap', 'Leap Step'),
    ]

    SIDE_CHOICES = [
    ('LHS', 'Left Hand Side'),
    ('RHS', 'Right Hand Side'),
    ]

    proof = models.ForeignKey(
    InductionProof,
    related_name='proof_lines',
    on_delete=models.CASCADE
    )
    case = models.CharField(max_length=10, choices=CASE_CHOICES)
    side = models.CharField(max_length=3, choices=SIDE_CHOICES)
    racket = models.TextField()
    json_tree = models.JSONField(default=dict, blank=True)
    rule = models.CharField(max_length=255, blank=True, default='')
    substitution = models.TextField(blank=True, default='')
    start_position = models.IntegerField(default=0)
    selected_node = models.IntegerField(default=0)
    result_node = models.IntegerField(default=0)
    line_number = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    errors = models.TextField(blank=True, default='')
    hide_expression = models.BooleanField(default=False)
    hide_justification = models.BooleanField(default=False)
    # --- Comments Feature ---
    instructor_comment = models.TextField(blank=True, default='')
    student_comment = models.TextField(blank=True, default='')
    comment_correct = models.BooleanField(null=True, default=None)

    class Meta:
        ordering = ['case', 'side', 'line_number']
        indexes = [
        models.Index(fields=['proof', 'case', 'side', 'line_number']),
        ]
        constraints = [
        models.UniqueConstraint(
        fields=['proof', 'case', 'side', 'line_number'],
        name='unique_proof_line'
        ),
        ]

    def __str__(self):
        return f'{self.case} {self.side} Line {self.line_number}: {self.racket[:50]}'
