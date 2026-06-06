from django.urls import path
from . import views

urlpatterns = [
    path("courses", views.CourseViewSet.as_view()),
    path("courses/<int:course_id>", views.CourseViewSet.as_view()),
    path("<int:course_id>", views.AssignmentViewSet.as_view()),
    path("", views.AssignmentViewSet.as_view()),
    path("check-user", views.check_user),
    path("remove-student", views.remove_student),
    path("add-student", views.add_student),
    path("instructor/library", views.InstructorLibraryView.as_view()),
    path("assignments/detail/<int:assignment_id>", views.AssignmentDetailView.as_view()),
    path('join-course', views.join_course, name='join-course'),
    path('leave-course', views.leave_course, name='leave-course'),
    path('assignments/<int:assignment_id>/start-assignment-proof', views.start_assignment_proof, name='start-assignment-proof'),
    path('assignments/<int:assignment_id>/progress', views.AssignmentProgressMatrixView.as_view(), name='assignment-progress'),
    path('courses/<int:course_id>/invitations', views.CourseInvitationView.as_view(), name='course-invitations'),
    path('invitations/me', views.StudentInvitationView.as_view(), name='student-invitations'),
    path("assignments/shares", views.InstructorAssignmentShareView.as_view(), name='instructor-shares'),
    path("instructors/share-targets", views.get_share_targets)
]
