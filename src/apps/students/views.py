from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import Student, StudentAdmission
from .forms import StudentForm, StudentAdmissionForm

# Student Creation View
class StudentCreateView(CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/student_form.html'
    success_url = reverse_lazy('student-admission')

    def form_valid(self, form):
        # You can add any custom logic here if needed
        return super().form_valid(form)

# Student Admission Creation View
class StudentAdmissionCreateView(CreateView):
    model = StudentAdmission
    form_class = StudentAdmissionForm
    template_name = 'students/admission_form.html'
    success_url = reverse_lazy('student-admission')

    def form_valid(self, form):
        # Auto-assign roll number and serial number via model's save() method
        return super().form_valid(form)