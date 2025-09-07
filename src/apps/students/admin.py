from django.contrib import admin
from .models import Student, StudentSerial, StudentAdmission, FeeStructure, PreviousInstitutionDetail, FeeDue, FeeType, BoardAcademicDetails

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
    list_display = ('student', 'student_class', 'section', 'session', 'roll_number', 'status', 'admission_date')
    search_fields = ('student__user__username', 'student_class', 'session')
    

@admin.register(FeeDue)
class FeeDueAdmin(admin.ModelAdmin):
    list_display = (
        'admission', 
        'get_student_name', 
        'amount', 
        'fee_type', 
        'paid',
        'get_fee_structure_name',
        'start_date',
    )
    search_fields = (
        'admission__student__user__username', 
        'fee_type__name', 
        'admission__student__user__first_name', 
        'admission__student__user__last_name'
    )

    def get_student_name(self, obj):
        return obj.admission.student.user.get_full_name()  # or just username or first_name
    get_student_name.short_description = 'Student Name'

    def get_fee_structure_name(self, obj):
        return obj.fee_type.fee_structure.name  # Or obj.admission.fee_structure.name if it's that way
    get_fee_structure_name.short_description = 'Fee Structure'

    def start_date(self, obj):
        return obj.fee_type.fee_structure.start_date
    start_date.short_description = 'Start Date'

@admin.register(PreviousInstitutionDetail)
class PreviousInstitutionDetailAdmin(admin.ModelAdmin):
    list_display = ('student', 'previous_institution', 'score', 'mm', 'percent', 'passing_year', 'rte', 'created_at')
    search_fields = ('student__user__username', 'previous_institution')

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)

@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount')
    search_fields = ('name',)

@admin.register(BoardAcademicDetails)
class BoardAcademicDetailsAdmin(admin.ModelAdmin):
    list_display = ('id','student', 'student_class', 'roll_no', 'board', 'passing_year', 'created_at','score', 'mm', 'percent', 'is_passed')
    search_fields = ('student__user__username', 'board', 'roll_no')