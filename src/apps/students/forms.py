from django import forms
from .models import Student, StudentSerial, StudentAdmission


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['user', 'height', 'weight', 'apaar_id', 'pen_number']


class StudentAdmissionForm(forms.ModelForm):
    class Meta:
        model = StudentAdmission
        fields = [
            'student', 'section', 'is_rte', 'session',
            'student_class', 'fee_structure', 'total_fee',
            'status'
        ]