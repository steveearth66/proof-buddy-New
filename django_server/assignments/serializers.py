import hashlib
import secrets
import string
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import Assignment, StudentProofMapping, Course, AssignmentProof
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
    created_by = serializers.SerializerMethodField()
    proofs = serializers.SerializerMethodField()
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'course', 'created_by', 'proofs']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.context.get('request').user if 'request' in self.context else None

        if not (user and getattr(user, 'is_instructor', False)):
            self.fields.pop('submissions', None)
        if not (user and not getattr(user, 'is_instructor', True)):
            self.fields.pop('submission', None)
    
    def get_created_by(self, obj):
        return UserSerializer(obj.created_by).data
    
    def get_proofs(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        
        proof_data = []
        # Get the instructor's template proofs mapped to this assignment
        assignment_proofs = AssignmentProof.objects.filter(assignment=obj)

        for ap in assignment_proofs:
            template_proof = ap.proof_object
            if not template_proof:
                continue

            proof_info = {
                "id": template_proof.id, # Template ID
                "title": getattr(template_proof, 'name', 'Untitled Proof'),
                "type": ap.content_type.model,
                "status": "Not Started",
                "student_proof_id": None
            }

            # If the user is a student, check if they have started it
            if user and not user.is_superuser and getattr(user, 'is_instructor', False) == False:
                mapping = StudentProofMapping.objects.filter(
                    assignment=obj,
                    student=user,
                    template_proof_id=template_proof.id,
                    content_type=ap.content_type
                ).first()

                if mapping:
                    student_proof = mapping.student_proof
                    proof_info["student_proof_id"] = mapping.object_id
                    
                    is_completed = getattr(student_proof, 'is_complete', False) 
                    
                    if is_completed:
                        proof_info["status"] = "Completed"
                    else:
                        proof_info["status"] = "In Progress"

            proof_data.append(proof_info)

        return proof_data
    
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
                    # 1. Grab the untouched original to read from
                    orig_proof = EquationalProof.objects.get(id=p_id)
                    
                    # 2. Grab a FRESH instance to mutate into the clone
                    cloned_proof = EquationalProof.objects.get(id=p_id)
                    
                    # Clone the Proof Header
                    cloned_proof.pk = None
                    cloned_proof.id = None
                    cloned_proof.user = None # Orphan it from the instructor
                    cloned_proof.save()
                    
                    # Clone the Proof Lines using the UNTOUCHED original_proof
                    for line in orig_proof.proof_lines.all():
                        line.pk = None
                        line.id = None
                        line.proof = cloned_proof
                        line.save()
                        
                    # Bind the CLONED proof to the Assignment
                    ctype = ContentType.objects.get(app_label='equational_reasoning_api', model='equationalproof')
                    AssignmentProof.objects.create(assignment=assignment, content_type=ctype, object_id=cloned_proof.id)
                
                except EquationalProof.DoesNotExist:
                    continue

            elif p_type == 'inductionproof':
                try:
                    # 1. Grab the untouched original to read from
                    orig_proof = InductionProof.objects.get(id=p_id)
                    
                    # 2. Grab a FRESH instance to mutate into the clone
                    cloned_proof = InductionProof.objects.get(id=p_id)
                    
                    # Clone the Proof Header
                    cloned_proof.pk = None
                    cloned_proof.id = None
                    cloned_proof.user = None # Orphan it
                    cloned_proof.save()
                    
                    # Clone the Proof Lines using the UNTOUCHED original_proof
                    for line in orig_proof.proof_lines.all():
                        line.pk = None
                        line.id = None
                        line.proof = cloned_proof
                        line.save()
                        
                    # Bind the CLONED proof to the Assignment
                    ctype = ContentType.objects.get(app_label='induction_api', model='inductionproof')
                    AssignmentProof.objects.create(assignment=assignment, content_type=ctype, object_id=cloned_proof.id)
                
                except InductionProof.DoesNotExist:
                    continue

        return assignment
