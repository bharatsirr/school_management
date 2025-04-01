from django.urls import path
from .views import BulkAttendanceView, attendance_error, attendance_success, attendance_already_taken

urlpatterns = [
    path("students/attendance/<str:class_name>/", BulkAttendanceView.as_view(), name="bulk_attendance"),
    path("attendance-error/", attendance_error, name="attendance_error"),
    path("attendance-success/", attendance_success, name="attendance_success"),
    path("attendance-already-taken/", attendance_already_taken, name="attendance_already_taken"),
]