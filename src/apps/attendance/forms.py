from django import forms
from apps.attendance.models import Attendance
from apps.students.models import Student
import datetime

class BulkAttendanceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        students = kwargs.pop("students", [])
        super().__init__(*args, **kwargs)

        # Create a radio button field for each student
        for student in students:
            self.fields[f"attendance_{student.id}"] = forms.ChoiceField(
                choices=[("present", "Present"), ("absent", "Absent")],
                widget=forms.RadioSelect,
                required=True,
                label=student.user.first_name + " " + student.user.last_name
            )

    def save_attendance(self, recorded_by):
        """ Saves attendance records for the given students """
        today = datetime.date.today()
        attendance_records = []

        for field_name, status in self.cleaned_data.items():
            student_id = int(field_name.split("_")[1])  # Extract student ID from field name
            student = Student.objects.get(id=student_id)

            # Create attendance instance
            attendance_records.append(
                Attendance(
                    user=student.user,
                    date=today,
                    status=status,
                    recorded_by=recorded_by
                )
            )

        # Bulk create attendance records for performance
        Attendance.objects.bulk_create(attendance_records)