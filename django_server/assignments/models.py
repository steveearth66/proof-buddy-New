from django.db import models


# Create your models here.
class Term(models.Model):
    name = models.CharField(max_length=255)
    instructor = models.ForeignKey(
        "accounts.Account",
        related_name="term_instructor",
        on_delete=models.CASCADE,
        limit_choices_to={"is_instructor": True},
        null=True,
    )
    students = models.ManyToManyField(
        "accounts.Account",
        related_name="term_students",
        limit_choices_to={"is_instructor": False},
    )
    created_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        limit_choices_to={"is_instructor": True},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, limit_choices_to={"is_instructor": True})

    def __str__(self):
        return self.title

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, limit_choices_to={"is_instructor": False})
    submission_date = models.DateTimeField(auto_now_add=True)
    submission = models.ForeignKey('proofs.Proof', on_delete=models.CASCADE)
    grade = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.assignment.title} - {self.student.username}"
