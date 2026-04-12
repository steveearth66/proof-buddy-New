import hashlib
import secrets
import string
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import Assignment, AssignmentSubmission, Course, AssignmentProof
from accounts.serializers import UserSerializer
from equational_reasoning_api.models import EquationalProof, EquationalProofLine
from induction_api.models import InductionProof, InductionProofLine

User = get_user_model()

class CourseSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()
    students = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = ['id', 'name', 'instructor', 'students', 'join_code_expires_at', 'created_by', 'is_active', 'term', 'description']

    def get_instructor(self, obj):
        return UserSerializer(obj.instructor).data
    
    def get_created_by(self, obj):
        return UserSerializer(obj.created_by).data
    
    def get_students(self, obj):
        return UserSerializer(obj.students, many=True).data

class CreateCourseSerializer(serializers.ModelSerializer):
    students = serializers.ListField(child=serializers.CharField(), required=False)
    
    # New write-only fields to control join code logic
    generate_join_code = serializers.BooleanField(write_only=True, default=False)
    expiration_date = serializers.DateTimeField(write_only=True, required=False)

    class Meta:
        model = Course
        fields = ['name', 'instructor', 'students', 'generate_join_code', 'expiration_date']

    def save(self, **kwargs):
        request = self.context.get('request')
        validated_data = self.validated_data
        
        # Extract the join code instructions
        generate_join_code = validated_data.pop('generate_join_code', False)
        expiration_date = validated_data.pop('expiration_date', None)

        validated_data['created_by'] = request.user
        validated_data['instructor'] = request.user

        student_identifiers = validated_data.pop('students', [])

        raw_code = None
        if generate_join_code:
            # Generate a random 8-character join code
            raw_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            
            # Hash it for database storage
            validated_data['join_code_hash'] = hashlib.sha256(raw_code.encode('utf-8')).hexdigest()
            
            # Use provided expiration date, or default to 1 week from now
            if expiration_date:
                validated_data['join_code_expires_at'] = expiration_date
            else:
                validated_data['join_code_expires_at'] = timezone.now() + timedelta(days=7)

        term = super().save(**kwargs)

        if student_identifiers:
            students = User.objects.filter(username__in=student_identifiers) | User.objects.filter(email__in=student_identifiers)
            term.students.set(students)

        response_data = CourseSerializer(term).data
        
        # Only inject the raw code into the return payload if it was generated
        if raw_code:
            response_data['join_code'] = raw_code 
            
        return response_data

class AssignmentSerializer(serializers.ModelSerializer):
    submissions = serializers.SerializerMethodField()
    submission = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    proofs = serializers.SerializerMethodField()
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'course', 'submissions', 'submission', 'created_by', 'proofs']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.context.get('request').user if 'request' in self.context else None

        if not (user and getattr(user, 'is_instructor', False)):
            self.fields.pop('submissions', None)
        if not (user and not getattr(user, 'is_instructor', True)):
            self.fields.pop('submission', None)

    def get_submissions(self, obj):
        submissions = AssignmentSubmission.objects.filter(assignment=obj)
        return AssignmentSubmissionSerializer(submissions, many=True).data
    
    def get_submission(self, obj):
        user = self.context.get('request').user
        submission = AssignmentSubmission.objects.filter(assignment=obj, student=user).first()
        return AssignmentSubmissionSerializer(submission).data if submission else None
    
    def get_created_by(self, obj):
        return UserSerializer(obj.created_by).data
    
    def get_proofs(self, obj):
        proof_mappings = obj.proof_items.all()
        proofs_list = []

        for mapping in proof_mappings:
            proof = mapping.proof_object
            if proof:
                proof_title = getattr(proof, 'name', None) or f"Untitled {mapping.content_type.model}"
                
                proofs_list.append({
                    'id': proof.id,
                    'type': mapping.content_type.model, # 'equationalproof' or 'inductionproof'
                    'title': proof_title
                })
        return proofs_list
    
class CreateAssignmentSerializer(serializers.ModelSerializer):
    # Expects a payload like: [{"type": "equationalproof", "id": 5}, {"type": "inductionproof", "id": 12}]
    proofs = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)

    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'course', 'proofs'] 

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        
        # Extract the proofs list before saving the Assignment model
        proofs_data = validated_data.pop('proofs', [])

        assignment = super().create(validated_data)

        # 2. Deep Clone the Proofs
        for proof in proofs_data:
            p_type = proof.get('type')
            p_id = proof.get('id')
            
            if p_type == 'equationalproof':
                try:
                    orig_proof = EquationalProof.objects.get(id=p_id)
                    orig_lines = orig_proof.proof_lines.all()
                    
                    # Clone the Proof Header
                    orig_proof.pk = None
                    orig_proof.user = None # Orphan it from the instructor
                    orig_proof.save()
                    cloned_proof = orig_proof # Now has a new ID
                    
                    # Clone the Proof Lines
                    for line in orig_lines:
                        line.pk = None
                        line.proof = cloned_proof
                        line.save()
                        
                    # Bind the CLONED proof to the Assignment
                    ctype = ContentType.objects.get(app_label='equational_reasoning_api', model='equationalproof')
                    AssignmentProof.objects.create(assignment=assignment, content_type=ctype, object_id=cloned_proof.id)
                
                except EquationalProof.DoesNotExist:
                    continue

            elif p_type == 'inductionproof':
                try:
                    orig_proof = InductionProof.objects.get(id=p_id)
                    orig_lines = orig_proof.proof_lines.all()
                    
                    # Clone the Proof Header
                    orig_proof.pk = None
                    orig_proof.user = None # Orphan it
                    orig_proof.save()
                    cloned_proof = orig_proof 
                    
                    # Clone the Proof Lines
                    for line in orig_lines:
                        line.pk = None
                        line.proof = cloned_proof
                        line.save()
                        
                    # Bind the CLONED proof to the Assignment
                    ctype = ContentType.objects.get(app_label='induction_api', model='inductionproof')
                    AssignmentProof.objects.create(assignment=assignment, content_type=ctype, object_id=cloned_proof.id)
                
                except InductionProof.DoesNotExist:
                    continue

        return assignment

class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student = serializers.SerializerMethodField()
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'student', 'submission_date', 'proofs', 'grade']

    def get_student(self, obj):
        return UserSerializer(obj.student).data
