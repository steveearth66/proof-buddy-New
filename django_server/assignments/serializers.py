from rest_framework import serializers
from .models import Assignment, AssignmentSubmission, Term
from accounts.serializers import UserSerializer

class TermSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()
    students = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    class Meta:
        model = Term
        fields = ['id', 'name', 'instructor', 'students', 'created_by']

    def get_instructor(self, obj):
        return UserSerializer(obj.instructor).data
    
    def get_created_by(self, obj):
        return UserSerializer(obj.created_by).data
    
    def get_students(self, obj):
        return UserSerializer(obj.students, many=True).data
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return super().create(validated_data)

class AssignmentSerializer(serializers.ModelSerializer):
    term = TermSerializer()
    submissions = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'term', 'submissions', 'created_by']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.context.get('request').user if 'request' in self.context else None

        if not (user and getattr(user, 'is_instructor', False)):
            self.fields.pop('submissions', None)

    def get_submissions(self, obj):
        submissions = AssignmentSubmission.objects.filter(assignment=obj)
        return AssignmentSubmissionSerializer(submissions, many=True).data
    
    def get_created_by(self, obj):
        return UserSerializer(obj.created_by).data

class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField()
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'student', 'submission_date', 'proofs', 'grade']

    def get_student(self, obj):
        return UserSerializer(obj.student).data
