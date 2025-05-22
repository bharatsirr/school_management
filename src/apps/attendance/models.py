from django.db import models
from django.db.models import Count
from django.contrib.auth import get_user_model
import datetime
import uuid
User = get_user_model()

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField(help_text="Attendance date")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_attendance')
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')  # Ensure one attendance record per user per day
        ordering = ['-date']

    def __str__(self):
        return f"{self.user} - {self.date} - {self.status}"
    



class HolidayTable(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True, help_text="Holiday date")
    name = models.CharField(max_length=255, help_text="Holiday name (e.g., Independence Day)")
    is_sunday_override = models.BooleanField(default=False, help_text="Is a working day on Sunday?")

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.date})"
    


class AttendanceSummary(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_summaries')
    month = models.PositiveSmallIntegerField(help_text="Month (1-12)")
    year = models.PositiveSmallIntegerField(help_text="Year (e.g., 2024)")
    total_working_days = models.PositiveIntegerField(default=0)
    present_days = models.PositiveIntegerField(default=0)
    absent_days = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'month', 'year')
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.user} - {self.month}/{self.year}"

    @property
    def attendance_percentage(self):
        if self.total_working_days == 0:
            return 0
        return (self.present_days / self.total_working_days) * 100
    





def generate_attendance_summary(user, month, year):
    working_days = 0
    today = datetime.date.today()
    
    # Identify all days in the month excluding weekends and holidays
    for day in range(1, 32):
        try:
            date = datetime.date(year, month, day)
        except ValueError:
            break  # Handles invalid days like Feb 30

        # Check if it's a working day (not Sunday and not a holiday)
        if date.weekday() == 6 and not HolidayTable.objects.filter(date=date, is_sunday_override=True).exists():
            continue  # Skip Sundays unless overridden
        if HolidayTable.objects.filter(date=date).exists():
            continue  # Skip holidays
        working_days += 1

    # Count present and absent records
    attendance_counts = Attendance.objects.filter(user=user, date__year=year, date__month=month).values('status').annotate(count=Count('status'))
    present_days = sum(item['count'] for item in attendance_counts if item['status'] == 'present')
    absent_days = sum(item['count'] for item in attendance_counts if item['status'] == 'absent')

    # Update or create the summary record
    summary, created = AttendanceSummary.objects.update_or_create(
        user=user,
        month=month,
        year=year,
        defaults={
            'total_working_days': working_days,
            'present_days': present_days,
            'absent_days': absent_days
        }
    )

    return summary, created