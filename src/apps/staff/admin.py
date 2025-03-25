from django.contrib import admin

from apps.staff.models import Staff, Qualification, TeachingStaff, TeachingStaffSubject, OtherStaff, Timetable


admin.site.register(Staff)
admin.site.register(Qualification)
admin.site.register(TeachingStaff)
admin.site.register(TeachingStaffSubject)
admin.site.register(OtherStaff)
admin.site.register(Timetable)