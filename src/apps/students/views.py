from django.core.paginator import Paginator
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, FormView
from .models import Student, StudentAdmission, FeeStructure, FeeType, FeeDue
from .forms import StudentRegistrationForm, FeeStructureForm, FeeTypeForm, StudentUpdateForm, StudentDocumentForm
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Prefetch
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

User = get_user_model()






    

# Student Registration View
class StudentRegistrationView(View):
    template_name = 'students/registration_form.html'
    success_url = reverse_lazy('home')

    def get(self, request):
        
        form = StudentRegistrationForm()

        # Disable caching to ensure the form is always freshly rendered
        response = render(request, self.template_name, {'form': form})
        
        return response

    def post(self, request):
        
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()

            messages.success(request, 'Student registered successfully')
            return redirect(self.success_url)
        else:
            messages.error(request, 'Student registration failed. Please fix the errors.')
        
        return render(request, self.template_name, {'form': form})


class StudentDocumentUploadView(LoginRequiredMixin, FormView):
    template_name = 'students/student_document_upload.html'
    form_class = StudentDocumentForm
    success_url = reverse_lazy('student_admission_list')

    def get_student(self):
        """Fetch the student object using the primary key from the URL."""
        student = get_object_or_404(Student, pk=self.kwargs.get('pk'))
        return student

    def get_user(self):
        """Retrieve the user associated with the student."""
        student = self.get_student()
        return student.user  # Assuming the Student model has a ForeignKey to User

    def dispatch(self, request, *args, **kwargs):
        """Ensure only the student or an admin can upload documents."""
        student_user = self.get_user()
        if request.user != student_user and not request.user.is_staff:
            raise PermissionDenied("You are not allowed to upload documents for this student.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Save the documents for the student’s associated user."""
        user = self.get_user()  # Get the user associated with the student
        form.cleaned_data['user'] = user  # Pass the user to the form
        form.save()  # Save the documents
        return super().form_valid(form)
    

class StudentUpdateView(UpdateView):
    model = Student
    form_class = StudentUpdateForm
    template_name = 'students/student_update_form.html'
    success_url = reverse_lazy('student_admission_list')





class StudentAdmissionListView(ListView):
    model = StudentAdmission
    template_name = 'students/admission_list.html'
    context_object_name = 'student_admissions'
    paginate_by = 10

    def get_queryset(self):
        # Prefetch related data to reduce queries
        return StudentAdmission.objects.select_related(
            'student__user', 
            'serial_no', 
            'fee_structure'
        ).prefetch_related(
            Prefetch('student__user__phones'), 
            Prefetch('student__previous_institution')
        )



# Fee Structure Creation View
class FeeStructureCreateView(CreateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'students/fee_structure_form.html'
    success_url = reverse_lazy('fee_structure_list')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Fee structure created successfully')
        return redirect(self.success_url)
    
    
class FeeStructureListView(ListView):
    model = FeeStructure
    template_name = 'students/fee_structure_list.html'
    context_object_name = 'fee_structures'
    queryset = FeeStructure.active_objects.all()


# Fee Structure Update View
class FeeStructureUpdateView(UpdateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'students/fee_structure_form.html'
    success_url = reverse_lazy('fee_structure_list')



class AddFeeTypeView(CreateView):
    model = FeeType
    form_class = FeeTypeForm
    template_name = 'students/add_fee_type.html'

    def dispatch(self, request, *args, **kwargs):
        self.fee_structure = FeeStructure.objects.get(id=kwargs['fee_structure_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.fee_structure = self.fee_structure
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('fee_structure_list')
