from rest_framework import serializers
from .models import Assignment, AssignmentSubmission, Term

class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ['id', 'name', 'instructor', 'students']

class AssignmentSerializer(serializers.ModelSerializer):
    term = TermSerializer()
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'term', 'created_by']

class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    assignment = AssignmentSerializer()
    student = serializers.StringRelatedField()
    submission = serializers.StringRelatedField()
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'student', 'submission_date', 'submission', 'grade', 'created_at']
