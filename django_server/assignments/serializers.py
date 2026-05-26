import hashlib
import secrets
import string
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import Assignment, StudentProofMapping, Course, AssignmentProof, CourseInvitation
from accounts.serializers import UserSerializer
from equational_reasoning_api.models import EquationalProof
from induction_api.models import InductionProof

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

class StudentViewCourseSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'name', 'instructor', 'is_active', 'term', 'description']

    def get_instructor(self, obj):
        instructor = UserSerializer(obj.instructor).data
        instructor.pop('id')
        instructor.pop('email')
        return instructor

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

        course = super().save(**kwargs)

        if student_identifiers:
            students = User.objects.filter(username__in=student_identifiers) | User.objects.filter(email__in=student_identifiers)
            course.students.set(students)

        response_data = CourseSerializer(course).data
        
        # Only inject the raw code into the return payload if it was generated
        if raw_code:
            response_data['join_code'] = raw_code 
            
        return response_data

class AssignmentSerializer(serializers.ModelSerializer):
    proofs = serializers.SerializerMethodField()
    class Meta:
        model = Assignment
        fields = ['id', 'title', 'description', 'due_date', 'course', 'proofs']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user = self.context.get('request').user if 'request' in self.context else None
    
    def get_proofs(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        
        proof_data = []
        # Get the instructor's template proofs mapped to this assignment
        assignment_proofs = AssignmentProof.objects.filter(assignment=obj).order_by('order', 'id')

        for ap in assignment_proofs:
            template_proof = ap.proof_object
            if not template_proof:
                continue

            type = ap.content_type.model
            proof_info = {
                "id": template_proof.id, # Template ID
                "name": getattr(template_proof, 'name', 'Untitled Proof'),
                "tag": getattr(template_proof, 'tag', 'General'),
                "type": type,
                "displayType": "Equational Reasoning" if type == "equationalproof" else "Induction",
                "status": "Not Started",
                "student_proof_id": None,
                "is_locked": StudentProofMapping.objects.filter(
                    assignment=obj, 
                    template_proof_id=template_proof.id,
                    content_type=ap.content_type
                ).exists()
            }

            # If the user is a student, check if they have started it
            if user and not user.is_superuser and getattr(user, 'is_instructor', False) == False:
                proof_info.pop("is_locked")
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
            p_name = proof.get('name')
            
            self._clone_and_bind_proof(assignment, p_id, p_type, p_name)

        return assignment
    
    def update(self, assignment, validated_data):
        proofs_data = validated_data.pop('proofs', None)
        
        # 1. Update standard fields (title, description, due_date)
        assignment.title = validated_data.get('title', assignment.title)
        assignment.description = validated_data.get('description', assignment.description)
        assignment.due_date = validated_data.get('due_date', assignment.due_date)
        assignment.save()

        if proofs_data is not None:
            # Get current proofs attached to this assignment
            current_assignment_proofs = list(AssignmentProof.objects.filter(assignment=assignment))
                        
            new_proof_list = []
            
            for index, p_info in enumerate(proofs_data):
                p_id = p_info.get('id')
                p_type = p_info.get('type')
                p_name = p_info.get('name')
                
                # Check if this proof is already attached to the assignment
                # (Matching by object_id and content_type)
                existing = next((ap for ap in current_assignment_proofs 
                                if ap.object_id == p_id and ap.content_type.model == p_type), None)
                
                if existing:
                    existing.order = index
                    if not StudentProofMapping.objects.filter(
                        assignment=assignment,
                        template_proof_id=existing.object_id,
                        content_type=existing.content_type
                    ).exists():
                        existing.proof_object.name = p_name
                        existing.proof_object.save()
                    existing.save()
                    new_proof_list.append(existing)
                else:
                    # clone newly added proof
                    cloned_ap = self._clone_and_bind_proof(assignment, p_id, p_type, p_name)
                    if cloned_ap:
                        cloned_ap.order = index
                        cloned_ap.save()
                        new_proof_list.append(cloned_ap)

            for old_ap in current_assignment_proofs:
                if old_ap not in new_proof_list:
                    # Check if ANY student has started this proof
                    has_progress = StudentProofMapping.objects.filter(
                        assignment=assignment,
                        template_proof_id=old_ap.object_id,
                        content_type=old_ap.content_type
                    ).exists()

                    if not has_progress:
                        if old_ap.proof_object:
                            old_ap.proof_object.delete() 
                        old_ap.delete()
                    else:
                        new_proof_list.append(old_ap)

        return assignment
    
    def _clone_and_bind_proof(self, assignment, p_id, p_type, p_name):
        """Helper to handle the cloning logic you used in create()"""
        # Logic for EquationalProof
        if p_type == 'equationalproof':
            try:
                orig = EquationalProof.objects.get(id=p_id)
                cloned = EquationalProof.objects.get(id=p_id)
                cloned.name = p_name
                cloned.pk = cloned.id = None
                cloned.user = None
                cloned.save()
                for line in orig.proof_lines.all():
                    line.pk = line.id = None
                    line.proof = cloned
                    line.save()
                ctype = ContentType.objects.get(app_label='equational_reasoning_api', model='equationalproof')
                return AssignmentProof.objects.create(assignment=assignment, content_type=ctype, object_id=cloned.id)
            except EquationalProof.DoesNotExist: return None

        # Logic for InductionProof
        elif p_type == 'inductionproof':
            try:
                orig = InductionProof.objects.get(id=p_id)
                cloned = InductionProof.objects.get(id=p_id)
                cloned.name = p_name
                cloned.pk = cloned.id = None
                cloned.user = None
                cloned.save()
                for line in orig.proof_lines.all():
                    line.pk = line.id = None
                    line.proof = cloned
                    line.save()
                ctype = ContentType.objects.get(app_label='induction_api', model='inductionproof')
                return AssignmentProof.objects.create(assignment=assignment, content_type=ctype, object_id=cloned.id)
            except InductionProof.DoesNotExist: return None
        return None

# serializers.py
class CourseInvitationSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    instructor_name = serializers.CharField(source='course.instructor.name', read_only=True)

    class Meta:
        model = CourseInvitation
        fields = ['id', 'course', 'course_name', 'instructor_name', 'student', 'status', 'sent_at']