from .models import Assignment, StudentProofMapping, Course, CourseInvitation
from .serializers import AssignmentSerializer, CourseSerializer, CreateCourseSerializer, CreateAssignmentSerializer, CourseInvitationSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
import hashlib
import secrets
import string
from datetime import timedelta
from django.utils import timezone
from equational_reasoning_api.models import EquationalProof
from induction_api.models import InductionProof
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

# Create your views here.

class CourseViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # GET /courses/course_id
    # GET /courses/
    """
        [
            {
                "id": 42,
                "name": "Test 2",
                "instructor": {
                    "id": 3,
                    "email": "testmail@mail.com",
                    "username": "int566",
                    "first_name": "John",
                    "last_name": "Instructor"
                },
                "students": [
                    {
                        "id": 4,
                        "email": "teststu@mail.com",
                        "username": "test22",
                        "first_name": "John",
                        "last_name": "Test"
                    }
                ],
                "created_by": {
                    "id": 3,
                    "email": "testmail@mail.com",
                    "username": "int566",
                    "first_name": "John",
                    "last_name": "Instructor"
                }
            }
        ]
    """
    def get(self, request, *args, **kwargs):
        user = request.user

        if kwargs.get("course_id"):
            try:
                course = Course.objects.get(id=kwargs.get("course_id"))
            except Course.DoesNotExist:
                return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

            if not (user.is_instructor and course.instructor == user) and user not in course.students.all() and not user.is_superuser:
                return Response({"message": "You are not authorized to view this course."}, status=status.HTTP_403_FORBIDDEN)

            serializer = CourseSerializer(course, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        courses = Course.objects.filter(instructor=user) if user.is_instructor else Course.objects.filter(students=user, is_active = True)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /courses/
    # e.g. post data
    """
        {
            "name": "Test 4",
            "students": ["pryceja"] # a list of students username or email
        }
    """
    def post(self, request):
        if not (request.user.is_instructor or request.user.is_superuser):
            return Response({"message": "You are not authorized to create a course"}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateCourseSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            course = serializer.save()
            return Response(course, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, *args, **kwargs):
        course_id = kwargs.get("course_id")
        
        if not course_id:
            return Response({"message": "Course ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_superuser and course.instructor != request.user:
            return Response({"message": "You are not authorized to manage this course."}, status=status.HTTP_403_FORBIDDEN)

        # ROUTE 1: Regenerate Join Code
        if request.data.get("action") == "regenerate_code":
            raw_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            course.join_code_hash = hashlib.sha256(raw_code.encode('utf-8')).hexdigest()
            course.join_code_expires_at = timezone.now() + timedelta(days=7)
            course.save()
            return Response({
                "join_code": raw_code,
                "join_code_expires_at": course.join_code_expires_at
            }, status=status.HTTP_200_OK)

        # ROUTE 2: Standard Field Updates (Dynamic)
        serializer = CourseSerializer(course, data=request.data, partial=True, context={"request": request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssignmentViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # GET /assignments/course_id
    """
        [
            {
                "id": 6,
                "title": "Test 2",
                "description": "Lorem ipsum dolor sit amet, consectetur",
                "due_date": "2024-12-12T00:00:00-05:00",
                "submissions": [
                    {
                        "id": 5,
                        "student": {
                            "id": 1,
                            "email": "javanpryce1@gmail.com",
                            "username": "pryceja",
                            "first_name": "Javan",
                            "last_name": "Test"
                        },
                        "submission_date": "2024-12-01T20:13:42.764919-05:00",
                        "proofs": [
                            14,
                            30,
                            33
                        ],
                        "grade": 0.0
                    }
                ],
                "created_by": {
                    "id": 2,
                    "email": "admin@localhost",
                    "username": "admin",
                    "first_name": "",
                    "last_name": ""
                }
            }
        ]
    """
    def get(self, request, course_id):
        user = request.user

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

        if not (user.is_instructor and course.instructor == user) and user not in course.students.all() and not user.is_superuser:
            return Response({"message": "You are not authorized to view any assignments for this course."}, status=status.HTTP_403_FORBIDDEN)

        assignments = Assignment.objects.filter(course=course)
        serializer = AssignmentSerializer(assignments, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /assignments/
    # e.g. post data
    """
    {
        "title": "Test 7",
        "description": "test assignment",
        "due_date": "2024-12-12",
        "course": 55
    }
    """
    def post(self, request):
        if not (request.user.is_instructor or request.user.is_superuser):
            return Response({"message": "You are not authorized to create an assignment"}, status=status.HTTP_403_FORBIDDEN)

        course_id = request.data.get("course")
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not request.user.is_superuser and course.instructor != request.user:
            return Response({"message": "You can only create assignments for your own courses."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateAssignmentSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            assignment = AssignmentSerializer(
                serializer.instance, context={"request": request}
            ).data
            return Response(assignment, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def check_user(request):
    data = request.data
    student = data.get("student")

    try:
        User.objects.get(username=student) if "@" not in student else User.objects.get(email=student)
        return Response(status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def remove_student(request):
    data = request.data
    course = data.get("course")
    student = data.get("student")

    try:
        course = Course.objects.get(id=course)
    except Course.DoesNotExist:
        return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

    if (
        not (request.user.is_instructor and course.instructor == request.user)
        and not request.user.is_superuser
    ):
        return Response(
            {"message": "You are not authorized to remove a student from this course."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        student = (
            User.objects.get(username=student)
            if "@" not in student
            else User.objects.get(email=student)
        )
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    course.students.remove(student)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def add_student(request):
    data = request.data
    course_id = data.get("course")
    student_identifier = data.get("student")

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

    # 1. Authorization Check
    if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_superuser:
        return Response(
            {"message": "You are not authorized to add a student to this course."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # 2. Find Student Candidates
    students = None
    if "@" in student_identifier:
        students = User.objects.filter(email=student_identifier, is_instructor=False, is_superuser=False)
    
    # If no results by email (or no @ in string), check by username
    if students is None or students.count() == 0:
        students = User.objects.filter(username=student_identifier, is_instructor=False, is_superuser=False)

    # 3. Handle Empty Results
    if students.count() == 0:
        # Check if the user exists but is an instructor
        if User.objects.filter(email=student_identifier, is_superuser=False).exists() or User.objects.filter(username=student_identifier, is_superuser=False).exists():
             return Response({"message": "Instructors cannot be added as students."}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Student not found. Check the spelling and try again."}, status=status.HTTP_404_NOT_FOUND)
    
    # 4. Handle Disambiguation (Multiple Results)
    elif students.count() > 1:
        candidates = [
            {
                "username": s.username,
                "email": s.email,
                "name": f"{s.first_name} {s.last_name}".strip() or "No Name Provided"
            } for s in students
        ]
        return Response({
            "message": "Multiple students share this identifier. Please select the correct one.",
            "requires_disambiguation": True,
            "candidates": candidates
        }, status=status.HTTP_409_CONFLICT)

    # 5. Success: Single Student Targeted
    student = students.first()

    # check if student is ALREADY enrolled
    if course.students.filter(pk=student.pk).exists():
        return Response({"message": "Student is already in the course."}, status=status.HTTP_204_NO_CONTENT)
    
    # NEW: Create or Update Invitation instead of adding directly to ManyToMany
    invitation, created = CourseInvitation.objects.update_or_create(
        course=course,
        student=student,
        defaults={'status': 'pending'}
    )
    serializer = CourseInvitationSerializer(invitation)
    if created:
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        # Invitation already existed (was either pending or rejected)
        return Response(
            {"message": "Existing invitation updated to pending.", "invitation": serializer.data}, 
            status=status.HTTP_200_OK
        )

class InstructorLibraryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        equational = EquationalProof.objects.filter(user=request.user, is_active=True)
        induction = InductionProof.objects.filter(user=request.user, is_active=True)
        
        library = []
        
        for proof in equational:
            library.append({
                'id': proof.id,
                'title': proof.name or "Untitled Equational Proof",
                'type': 'equationalproof',
                'displayType': 'Equational Reasoning',
                'category': proof.tag or 'General'
            })
            
        for proof in induction:
            library.append({
                'id': proof.id,
                'title': proof.name or "Untitled Induction Proof",
                'type': 'inductionproof',
                'displayType': 'Induction',
                'category': proof.tag or 'General'
            })
            
        return Response(library)

class AssignmentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, assignment_id):
        try:
            assignment = Assignment.objects.get(id=assignment_id)
        except Assignment.DoesNotExist:
            return Response({"message": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_superuser and assignment.course.instructor != request.user:
            return Response(
                {"message": "You are not authorized to delete this assignment."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Deleting the assignment will automatically cascade and delete the 
        # AssignmentProof mappings (and submissions, if any) tied to it.
        assignment.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def patch(self, request, assignment_id):
        try:
            assignment = Assignment.objects.get(id=assignment_id)
        except Assignment.DoesNotExist:
            return Response({"message": "Assignment not found"}, status=status.HTTP_404_NOT_FOUND)

        # Authorization check
        if not request.user.is_superuser and assignment.course.instructor != request.user:
            return Response(
                {"message": "You are not authorized to edit this assignment."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CreateAssignmentSerializer(
            assignment, 
            data=request.data, 
            partial=True, 
            context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                AssignmentSerializer(assignment, context={"request": request}).data, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def join_course(request):
    join_code = request.data.get("code", "").strip()

    if not join_code:
        return Response({"message": "Please provide a join code."}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Filter for active courses where the join code hasn't expired
    potential_courses = Course.objects.filter(
        is_active=True,
        join_code_expires_at__gt=timezone.now()
    ).exclude(join_code_hash="")

    # 2. Hash the incoming code using the exact same method as generation
    input_hash = hashlib.sha256(join_code.encode('utf-8')).hexdigest()
    print(input_hash)
    # 3. Iterate and compare the raw hashes
    for course in potential_courses:
        if course.join_code_hash == input_hash:
            
            # 4. Prevent duplicate enrollments
            if request.user in course.students.all():
                return Response({"message": "You are already enrolled in this course."}, status=status.HTTP_400_BAD_REQUEST)

            # 5. Enroll the student
            course.students.add(request.user)

            # 6. Remove an invitation if it exists
            CourseInvitation.objects.filter(course=course, student=request.user).delete()
            
            return Response({
                "message": "Successfully joined the course!",
                "course": CourseSerializer(course).data
            }, status=status.HTTP_200_OK)

    # If the loop finishes without returning, no valid code was found
    return Response({"message": "Invalid or expired join code."}, status=status.HTTP_404_NOT_FOUND)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def leave_course(request):
    course_id = request.data.get("course")
    
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check if the student is actually in the course
    if request.user in course.students.all():
        course.students.remove(request.user)
        return Response({"message": "Successfully left the course."}, status=status.HTTP_200_OK)
        
    return Response({"message": "You are not enrolled in this course."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def start_assignment_proof(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    template_proof_id = request.data.get("proof_id")
    proof_type = request.data.get("proof_type")

    if not template_proof_id or not proof_type:
        return Response({"message": "Proof ID and type are required."}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Figure out which app the proof belongs to dynamically
    app_label = 'equational_reasoning_api' if proof_type == 'equationalproof' else 'induction_api'
    content_type = ContentType.objects.get(app_label=app_label, model=proof_type)
    ProofModel = content_type.model_class()

    # 2. Check if the student already cloned this
    existing_mapping = StudentProofMapping.objects.filter(
        assignment=assignment,
        student=request.user,
        template_proof_id=template_proof_id,
        content_type=content_type
    ).first()

    if existing_mapping:
        return Response({
            "success": True, 
            "new_proof_id": existing_mapping.object_id,
            "type": proof_type
        }, status=status.HTTP_200_OK)

    # 3. DEEP CLONE THE PROOF
    try:
        # A. Grab the untouched original to read lines from
        orig_proof = ProofModel.objects.get(id=template_proof_id)
        
        # B. Grab a fresh instance to mutate into the clone
        cloned_proof = ProofModel.objects.get(id=template_proof_id)
        
        # Clone the Proof Header
        cloned_proof.pk = None
        cloned_proof.id = None
        cloned_proof.user = request.user  # The student now owns this copy
        cloned_proof.name = f"{getattr(cloned_proof, 'name', 'Untitled')} (Assignment Copy)"
        cloned_proof.is_complete = False # force student proof to be marked incomplete in case instructor version was marked complete
        cloned_proof.save()

        # C. Clone the Proof Lines dynamically
        # This relies on both EquationalProofLine and InductionProofLine using related_name='proof_lines'
        for line in orig_proof.proof_lines.all():
            line.pk = None
            line.id = None
            line.proof = cloned_proof  # Link the line to the new student clone
            line.save()
            
    except ProofModel.DoesNotExist:
        return Response({"message": "Template proof not found."}, status=status.HTTP_404_NOT_FOUND)

    # 4. Save the mapping linking the assignment, student, and the new clone
    StudentProofMapping.objects.create(
        assignment=assignment,
        student=request.user,
        template_proof_id=template_proof_id,
        content_type=content_type,
        object_id=cloned_proof.id
    )

    return Response({
        "success": True, 
        "new_proof_id": cloned_proof.id,
        "type": proof_type
    }, status=status.HTTP_201_CREATED)

class AssignmentProgressMatrixView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, assignment_id):
        assignment = get_object_or_404(Assignment, id=assignment_id)
        course = assignment.course

        # 1. Instructor Authorization Check
        if not (request.user.is_instructor and course.instructor == request.user) and not request.user.is_superuser:
            return Response(
                {"message": "You are not authorized to view progress for this assignment."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Fetch the Template Proofs
        template_links = assignment.proof_items.all()
        
        proof_columns = []
        for link in template_links:
            # Access the actual generic proof via the GenericForeignKey 'proof_object'
            proof = link.proof_object
            proof_columns.append({
                "id": link.object_id,
                # Fallback to a generic name if the proof is missing or has no name
                "title": getattr(proof, 'name', f"Proof {link.object_id}") if proof else f"Proof {link.object_id}",
                "type": link.content_type.model
            })

        # 3. Fetch all Student Mappings
        mappings = StudentProofMapping.objects.filter(assignment=assignment).prefetch_related('student_proof')
        
        # Structure: { student_id: { template_proof_id: { status_data } } }
        mapping_dict = {}
        for m in mappings:
            student_id = m.student.id
            cloned_proof = m.student_proof
            
            if not cloned_proof:
                proof_status = "error" 
            elif getattr(cloned_proof, 'is_complete', False):
                proof_status = "complete"
            else:
                proof_status = "in progress"

            if student_id not in mapping_dict:
                mapping_dict[student_id] = {}

            mapping_dict[student_id][str(m.template_proof_id)] = {
                "status": proof_status,
                "cloned_proof_id": m.object_id,
                "proof_type": m.content_type.model
            }

        # 4. Build the Students Matrix
        students_data = []
        for student in course.students.all():
            student_data = {
                "id": student.id,
                "username": student.username,
                "email": student.email,
                "firstName": student.first_name,
                "lastName": student.last_name,
                "statuses": {}
            }

            student_mappings = mapping_dict.get(student.id, {})
            
            # Guarantee every column has a corresponding cell for this student
            for link in template_links:
                tp_id = str(link.object_id)
                
                if tp_id in student_mappings:
                    student_data["statuses"][tp_id] = student_mappings[tp_id]
                else: # only started proofs have a database link to the student
                    student_data["statuses"][tp_id] = {
                        "status": "not started",
                        "cloned_proof_id": None,
                        "proof_type": None
                    }
                    
            students_data.append(student_data)

        return Response({
            "columns": proof_columns,
            "students": students_data
        }, status=status.HTTP_200_OK)

class CourseInvitationView(APIView):
    """
    Instructor-facing view to manage course invitations.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_id):
        # List all invitations for a specific course
        invitations = CourseInvitation.objects.filter(
            course_id=course_id, 
            course__instructor=request.user
        )
        serializer = CourseInvitationSerializer(invitations, many=True)
        return Response(serializer.data)

    def delete(self, request, course_id):
        # Cancel a specific invitation
        invitation_id = request.data.get('invitation_id')
        invitation = get_object_or_404(
            CourseInvitation, 
            id=invitation_id, 
            course_id=course_id, 
            course__instructor=request.user
        )
        invitation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class StudentInvitationView(APIView):
    """
    Student-facing view to fetch and respond to invitations.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Students fetch only their PENDING invitations
        invites = CourseInvitation.objects.filter(student=request.user, status='pending')
        serializer = CourseInvitationSerializer(invites, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Accept or Reject an invitation
        invitation_id = request.data.get('invitation_id')
        action = request.data.get('action') # 'accept' or 'reject'
        
        # only search for invitations for requesting account
        invitation = get_object_or_404(CourseInvitation, id=invitation_id, student=request.user)

        if action == 'accept':
            invitation.course.students.add(request.user)
            invitation.delete()
            return Response({"message": "Joined course."}, status=status.HTTP_200_OK)

        elif action == 'reject':
            invitation.status = 'rejected'
            invitation.save()
            return Response({"message": "Invitation declined."}, status=status.HTTP_200_OK)

        return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)