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
    path('leave-course', views.leave_course, name='leave-course')
]
