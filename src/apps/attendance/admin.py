from django.contrib import admin

from apps.attendance.models import Attendance, AttendanceSummary, HolidayTable

admin.site.register(Attendance)
admin.site.register(AttendanceSummary)
admin.site.register(HolidayTable)