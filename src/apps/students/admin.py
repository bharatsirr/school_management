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
    

@admin.register(FeeDue)
class FeeDueAdmin(admin.ModelAdmin):
    list_display = ('admission', 'amount', 'fee_type', 'paid')
    search_fields = ('admission__student__user__username', 'fee_type__name')

@admin.register(PreviousInstitutionDetail)
class PreviousInstitutionDetailAdmin(admin.ModelAdmin):
    list_display = ('student', 'previous_institution', 'score', 'mm', 'percent')
    search_fields = ('student__user__username', 'previous_institution')

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)

@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount')
    search_fields = ('name',)
