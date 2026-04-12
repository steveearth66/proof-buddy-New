from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from dotenv import load_dotenv
import os

load_dotenv()


# Create your models here.
class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=False)
    instructor = models.ForeignKey(
        "accounts.Account",
        related_name="course_instructor",
        on_delete=models.CASCADE,
        limit_choices_to={"is_instructor": True},
        null=True,
    )
    students = models.ManyToManyField(
        "accounts.Account",
        related_name="course_students",
        limit_choices_to={"is_instructor": False},
    )

    join_code_hash = models.CharField(max_length=128, blank=True, null=True)
    join_code_expires_at = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        limit_choices_to={"is_instructor": True},
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    term_validator = RegexValidator(
        regex=r'^(Spring|Summer|Fall|Winter) \d{4}$',
        message="Term must be a season followed by a 4-digit year (e.g., 'Fall 2026')."
    )

    now = timezone.now()
    month = now.month
    year = now.year
    day = now.day

    if month in [1, 2, 3]:
        season = "Winter"
    elif month in [4, 5, 6]:
        season = "Spring"
    elif month in [7, 8] or (month == 9 and day < 19):
        season = "Summer"
    else:
        season = "Fall"
        
    default_term = f"{season} {year}"

    term = models.CharField(
        max_length=20, 
        blank=True, 
        default=default_term,
        validators=[term_validator]
    )

    def __str__(self):
        return self.name


class Assignment(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, limit_choices_to={"is_instructor": True})

    def __str__(self):
        return self.title
    
class AssignmentProof(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='proof_items')
    
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        limit_choices_to=models.Q(app_label='equational_reasoning_api', model='equationalproof') | 
                         models.Q(app_label='induction_api', model='inductionproof')
    )
    
    object_id = models.PositiveIntegerField()
    
    proof_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('assignment', 'content_type', 'object_id')

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


# Sends emails for assignments and submissions, leave commented out for now to prevent issues when deployed
# @receiver(post_save, sender=Assignment)
# def send_assignment_email(sender, instance, created, **kwargs):
#     if created:
#         subject, from_email, to = 'New Assignment!', os.getenv('EMAIL_HOST_USER'), instance.course.students.all().values_list('email', flat=True)
#         text_content = f'New assignment: {instance.title} has been created for {instance.course.name}.'
#         html_content = f'''
#             <h1>New Assignment!</h1>
#             <p>New assignment: {instance.title} has been created for {instance.course.name}.</p>
#             <b>Assignment Description:</b>
#             <p>{instance.description}</p>
#             <p>Due Date: {instance.due_date}</p>
#         '''
#         msg = EmailMultiAlternatives(subject, text_content, from_email, to)
#         msg.attach_alternative(html_content, "text/html")
#         msg.send()


# @receiver(post_save, sender=AssignmentSubmission)
# def send_submission_email(sender, instance, created, **kwargs):
#     if created:
#         subject, from_email, to = 'Submission Received!', os.getenv('EMAIL_HOST_USER'), instance.student.email
#         text_content = f'New submission: {instance.assignment.title} has been submitted.'
#         html_content = f"""
#             <h1>Submission Received!</h1>
#             <p>{instance.assignment.title} has been submitted.</p>
#             <p><b>Submission Date:</b> {instance.submission_date}</p>
#         """
#         msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
#         msg.attach_alternative(html_content, "text/html")
#         msg.send()
