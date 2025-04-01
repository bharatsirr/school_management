from django.urls import path
from .views import BulkAttendanceView, attendance_error, attendance_success, attendance_already_taken, class_selection

urlpatterns = [
    path("students/attendance/<str:class_name>/", BulkAttendanceView.as_view(), name="bulk_attendance"),
    path("attendance_error/", attendance_error, name="attendance_error"),
    path("students/attendance/attendance_success/", attendance_success, name="attendance_success"),
    path("students/attendance/attendance_already_taken/", attendance_already_taken, name="attendance_already_taken"),
    path("students/attendance/", class_selection, name="class_selection"),
]