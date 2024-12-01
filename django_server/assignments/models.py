from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from dotenv import load_dotenv
import os

load_dotenv()


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
    proofs = models.ManyToManyField('proofs.Proof', related_name='proofs')
    grade = models.FloatField(default=0)

    class Meta:
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.assignment.title} - {self.student.username}"


@receiver(post_save, sender=Assignment)
def send_assignment_email(sender, instance, created, **kwargs):
    if created:
        subject, from_email, to = 'New Assignment!', os.getenv('EMAIL_HOST_USER'), instance.term.students.all().values_list('email', flat=True)
        text_content = f'New assignment: {instance.title} has been created for {instance.term.name}.'
        html_content = f'''
            <h1>New Assignment!</h1>
            <p>New assignment: {instance.title} has been created for {instance.term.name}.</p>
            <b>Assignment Description:</b>
            <p>{instance.description}</p>
            <p>Due Date: {instance.due_date}</p>
        '''
        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()


@receiver(post_save, sender=AssignmentSubmission)
def send_submission_email(sender, instance, created, **kwargs):
    if created:
        subject, from_email, to = 'Submission Received!', os.getenv('EMAIL_HOST_USER'), instance.student.email
        text_content = f'New submission: {instance.assignment.title} has been submitted.'
        html_content = f"""
            <h1>Submission Received!</h1>
            <p>{instance.assignment.title} has been submitted.</p>
            <p><b>Submission Date:</b> {instance.submission_date}</p>
        """
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
