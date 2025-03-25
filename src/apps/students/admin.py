from django.contrib import admin
from .models import Student, StudentSerial, StudentAdmission, FeeStructure, PreviousInstitutionDetail, FeeDue, FeeType

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'apaar_id', 'pen_number', 'is_active')
    search_fields = ('user__username', 'apaar_id', 'pen_number')

@admin.register(StudentSerial)
class StudentSerialAdmin(admin.ModelAdmin):
    list_display = ('student', 'school_name', 'serial_number', 'is_active')
    search_fields = ('student__user__username', 'school_name')

@admin.register(StudentAdmission)
class StudentAdmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'student_class', 'section', 'session', 'roll_number', 'status')
    search_fields = ('student__user__username', 'student_class', 'session')
    
admin.site.register(PreviousInstitutionDetail)
admin.site.register(FeeStructure)
admin.site.register(FeeDue)
admin.site.register(FeeType)