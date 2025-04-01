from django.contrib import admin
from apps.staff.models import Staff, Qualification, TeachingStaff, TeachingStaffSubject, OtherStaff, Timetable


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'staff_type', 'is_active')
    search_fields = ('user__username',)
    list_filter = ('staff_type', 'is_active')
    list_select_related = ('user',)

    def get_username(self, obj):
        return obj.user.username
    get_username.admin_order_field = 'user__username'
    get_username.short_description = 'Username'


@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ('get_staff_username', 'degree', 'year_of_completion')
    search_fields = ('staff__user__username', 'degree')
    list_filter = ('year_of_completion',)
    list_select_related = ('staff', 'staff__user')

    def get_staff_username(self, obj):
        return obj.staff.user.username
    get_staff_username.admin_order_field = 'staff__user__username'
    get_staff_username.short_description = 'Staff Username'


@admin.register(TeachingStaff)
class TeachingStaffAdmin(admin.ModelAdmin):
    list_display = ('get_staff_username', 'teacher_level')
    search_fields = ('staff__user__username',)
    list_filter = ('teacher_level',)
    list_select_related = ('staff', 'staff__user')

    def get_staff_username(self, obj):
        return obj.staff.user.username
    get_staff_username.admin_order_field = 'staff__user__username'
    get_staff_username.short_description = 'Teacher Username'


@admin.register(TeachingStaffSubject)
class TeachingStaffSubjectAdmin(admin.ModelAdmin):
    list_display = ('get_teacher_username', 'subject', 'preference')
    search_fields = ('staff__staff__user__username', 'subject')
    list_filter = ('subject',)
    list_select_related = ('staff', 'staff__staff', 'staff__staff__user')

    def get_teacher_username(self, obj):
        return obj.staff.staff.user.username
    get_teacher_username.admin_order_field = 'staff__staff__user__username'
    get_teacher_username.short_description = 'Teacher Username'


@admin.register(OtherStaff)
class OtherStaffAdmin(admin.ModelAdmin):
    list_display = ('get_staff_username', 'position')
    search_fields = ('staff__user__username', 'position')
    list_filter = ('position',)
    list_select_related = ('staff', 'staff__user')

    def get_staff_username(self, obj):
        return obj.staff.user.username
    get_staff_username.admin_order_field = 'staff__user__username'
    get_staff_username.short_description = 'Staff Username'


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('get_teacher_username', 'class_name', 'period', 'subject', 'time_start', 'time_end', 'is_active')
    search_fields = ('teacher__staff__user__username', 'subject', 'class_name')
    list_filter = ('class_name', 'period', 'is_active')
    list_select_related = ('teacher', 'teacher__staff', 'teacher__staff__user')

    def get_teacher_username(self, obj):
        return obj.teacher.staff.user.username
    get_teacher_username.admin_order_field = 'teacher__staff__user__username'
    get_teacher_username.short_description = 'Teacher Username'