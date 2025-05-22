from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Staff(models.Model):
    TEACHING = 'teaching'
    NON_TEACHING = 'non-teaching'
    STAFF_TYPES = [
        (TEACHING, 'Teaching'),
        (NON_TEACHING, 'Non-Teaching'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="staff_profile")
    staff_type = models.CharField(max_length=20, choices=STAFF_TYPES)
    joining_date = models.DateField(help_text="Date when the staff joined")
    leaving_date = models.DateField(null=True, blank=True, help_text="Date when the staff left")
    leaving_reason = models.TextField(blank=True, null=True, help_text="Reason for leaving")
    salary = models.DecimalField(max_digits=12, decimal_places=2, help_text="Monthly salary")
    is_active = models.BooleanField(default=True, help_text="Is the staff member currently active?")
    employment_history = models.JSONField(default=dict, help_text="History of employment in JSON format")

    def __str__(self):
        return f"{self.user.username} - {self.staff_type}"

    class Meta:
        verbose_name = "Staff"
        verbose_name_plural = "Staff Members"

    def mark_inactive(self, reason=None):
        """Mark staff as inactive and update leaving date and reason."""
        self.is_active = False
        self.leaving_date = models.DateField(auto_now=True)
        if reason:
            self.leaving_reason = reason
        self.save()



class Qualification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="qualifications")
    degree = models.CharField(max_length=255, help_text="Degree name (e.g., B.Ed, M.Sc.)")
    institution = models.CharField(max_length=255, help_text="Institution name")
    year_of_completion = models.PositiveIntegerField(help_text="Year of completion")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage obtained")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.degree} - {self.staff.user.username}"

    class Meta:
        verbose_name = "Qualification"
        verbose_name_plural = "Qualifications"




class TeachingStaff(models.Model):
    PRE_PRIMARY = 'pre_primary'
    PRIMARY = 'primary'
    JRT = 'jrt'
    SENIOR_SECONDARY = 'senior_secondary'

    TEACHER_LEVEL_CHOICES = [
        (PRE_PRIMARY, 'Pre-Primary'),
        (PRIMARY, 'Primary'),
        (JRT, 'Junior Secondary (JRT)'),
        (SENIOR_SECONDARY, 'Senior Secondary'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name="teaching_info")
    national_teacher_id = models.CharField(max_length=50, unique=True, help_text="National Teacher ID")
    state_teacher_id = models.CharField(max_length=50, unique=True, help_text="State Teacher ID")
    teacher_level = models.CharField(max_length=20, choices=TEACHER_LEVEL_CHOICES)

    def __str__(self):
        return f"{self.staff.user.username} - {self.teacher_level}"

    class Meta:
        verbose_name = "Teaching Staff"
        verbose_name_plural = "Teaching Staff"




class TeachingStaffSubject(models.Model):
    SUBJECT_CHOICES = [
        ('mathematics', 'Mathematics'),
        ('science', 'Science'),
        ('english', 'English'),
        ('history', 'History'),
        ('geography', 'Geography'),
        ('computer_science', 'Computer Science'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    staff = models.ForeignKey(TeachingStaff, on_delete=models.CASCADE, related_name="subjects")
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES, help_text="Subject specialization")
    preference = models.PositiveSmallIntegerField(help_text="Subject preference (1 for highest)")

    def __str__(self):
        return f"{self.staff.staff.user.username} - {self.subject} (Preference {self.preference})"

    class Meta:
        unique_together = ('staff', 'subject')
        ordering = ['preference']
        verbose_name = "Teaching Staff Subject"
        verbose_name_plural = "Teaching Staff Subjects"


class OtherStaff(models.Model):
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, primary_key=True, related_name="other_info")
    position = models.CharField(max_length=255, help_text="Position (e.g., Accountant, Admin)")

    def __str__(self):
        return f"{self.staff.user.username} - {self.position}"

    class Meta:
        verbose_name = "Other Staff"
        verbose_name_plural = "Other Staff"




class Timetable(models.Model):
    PERIOD_CHOICES = [(i, f"Period {i}") for i in range(1, 9)]

    CLASS_CHOICES = [
        ('nursery', 'Nursery'),
        ('lkg', 'LKG'),
        ('ukg', 'UKG'),
    ] + [(str(i), f"Class {i}") for i in range(1, 13)]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey('TeachingStaff', on_delete=models.CASCADE, related_name="timetable_entries")
    period = models.PositiveSmallIntegerField(choices=PERIOD_CHOICES, help_text="Period number (1-8)")
    class_name = models.CharField(max_length=10, choices=CLASS_CHOICES, help_text="Class (Nursery-12)")
    subject = models.CharField(max_length=100, help_text="Subject taught during this period")
    time_start = models.TimeField(help_text="Start time of the period (e.g., 09:00 AM)")
    time_end = models.TimeField(help_text="End time of the period (e.g., 09:40 AM)")
    is_active = models.BooleanField(default=True, help_text="Is this timetable entry active?")

    def __str__(self):
        return f"{self.get_class_name_display()} - Period {self.period} ({self.subject})"

    class Meta:
        unique_together = ('period', 'class_name', 'time_start', 'teacher')
        ordering = ['class_name', 'period']
        verbose_name = "Timetable Entry"
        verbose_name_plural = "Timetable"