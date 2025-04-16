from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import now
from apps.students.models import Student
from apps.attendance.models import Attendance, HolidayTable
from django.views.generic.edit import FormView
from .forms import BulkAttendanceForm
import datetime


def attendance_error(request):
    return render(request, "attendance/attendance_error.html")

def attendance_success(request):
    return render(request, "attendance/attendance_success.html")

def attendance_already_taken(request):
    return render(request, "attendance/attendance_already_taken.html")

def class_selection(request):
    """Renders a page with buttons to select a class for attendance marking."""
    class_options = [
        {"name": "Nursery", "value": "NUR"},
        {"name": "LKG", "value": "LKG"},
        {"name": "UKG", "value": "UKG"},
    ] + [{"name": f"Class {i}", "value": str(i)} for i in range(1, 13)]  # Classes 1 to 12

    return render(request, "attendance/class_selection.html", {"class_options": class_options})

class BulkAttendanceView(FormView):
    template_name = "attendance/bulk_attendance.html"
    form_class = BulkAttendanceForm

    def dispatch(self, request, *args, **kwargs):
        """ Prevent attendance marking if today is a holiday or Sunday. """
        today = datetime.date.today()

        # Check if today is a holiday
        if HolidayTable.objects.filter(date=today, is_sunday_override=False).exists():
            messages.error(request, "Attendance cannot be taken on holidays.")
            return redirect("attendance_error")  # Redirect to an error page (we'll create it later)

        # Check if today is a Sunday and not overridden
        if today.weekday() == 6 and not HolidayTable.objects.filter(date=today, is_sunday_override=True).exists():
            messages.error(request, "Attendance cannot be taken on Sundays.")
            return redirect("attendance_error")

        return super().dispatch(request, *args, **kwargs)

    def get_students(self):
        """ Get students filtered by class from the URL. """
        student_class = self.kwargs.get("class_name")  # e.g., '7', 'nur', 'lkg'
        return Student.objects.filter(admissions__student_class=student_class, is_active=True)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["students"] = self.get_students()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["student_class"] = self.kwargs.get("class_name")
        return context

    def get(self, request, *args, **kwargs):
        """ If attendance is already taken for today, redirect. """
        today = datetime.date.today()
        students = self.get_students()

        # Check if attendance is already taken for all students
        attendance_taken = Attendance.objects.filter(
            user__in=[student.user for student in students], date=today
        ).exists()

        if attendance_taken:
            messages.info(request, "Attendance for today is already taken.")
            return redirect("attendance_already_taken")  # Redirect to another page

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        """ Save attendance records when the form is submitted. """
        form.save_attendance(recorded_by=self.request.user)
        messages.success(self.request, "Attendance marked successfully!")
        return redirect("attendance_success")  # Redirect after success