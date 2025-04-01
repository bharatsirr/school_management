from django.contrib import admin

from apps.attendance.models import Attendance, AttendanceSummary, HolidayTable

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'date', 'status')
    search_fields = ('user__username', 'date')
    list_filter = ('status',)


@admin.register(AttendanceSummary)
class AttendanceSummaryAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'month', 'year')
    search_fields = ('user__username', 'month', 'year')
    list_filter = ('month', 'year')


@admin.register(HolidayTable)
class HolidayTableAdmin(admin.ModelAdmin):
    list_display = ('date', 'name')
    search_fields = ('date', 'name')
    list_filter = ('date',)

