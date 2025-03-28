from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import Student, StudentAdmission
from .forms import StudentForm, StudentAdmissionForm, StudentRegistrationForm
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.cache import never_cache
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
    

# Student Registration View
class StudentRegistrationView(View):
    template_name = 'students/registration_form.html'
    success_url = reverse_lazy('home')

    def get(self, request):
        
        form = StudentRegistrationForm()

        # Disable caching to ensure the form is always freshly rendered
        response = render(request, self.template_name, {'form': form})
        response['Cache-Control'] = 'no-store'  # Prevent caching
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response

    def post(self, request):
        
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            # Set session flag to indicate the form has been submitted
            request.session['form_submitted'] = True

            # Store the submission time as a string (use isoformat() for datetime)
            request.session['form_submission_time'] = timezone.now().isoformat()

            messages.success(request, 'Student registered successfully')
            return redirect(self.success_url)
        else:
            messages.error(request, 'Student registration failed. Please fix the errors.')
        
        return render(request, self.template_name, {'form': form})