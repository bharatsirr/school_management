from django.core.paginator import Paginator
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, FormView
from .models import Student, StudentAdmission, FeeStructure, FeeType, FeeDue
from .forms import StudentRegistrationForm, FeeStructureForm, FeeTypeForm, StudentUpdateForm, StudentDocumentForm, PayFamilyFeeDuesForm
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Prefetch
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from apps.core.models import Family, FamilyMember
from django.templatetags.static import static
from django.db import models
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
        """Save the documents for the student's associated user."""
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
    paginate_by = 50

    def get_queryset(self):
        # Prefetch related data to reduce queries
        queryset = StudentAdmission.objects.select_related(
            'student__user', 
            'serial_no', 
            'fee_structure'
        ).prefetch_related(
            Prefetch('student__user__phones'), 
            Prefetch('student__previous_institution')
        ).order_by('-admission_date')
    
        # Add profile_photo to each admission
        for admission in queryset:
            admission.profile_photo = admission.student.user.documents.filter(document_name="profile_photo").first()
        
        return queryset



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



class PayFamilyFeeDuesView(FormView):
    form_class = PayFamilyFeeDuesForm
    template_name = 'students/pay_family_fee_dues.html'
    success_url = reverse_lazy('student_admission_list')

    def get_family(self):
        return get_object_or_404(Family, id=self.kwargs.get("family_id"))
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['family'] = self.get_family()
        return context

    def form_valid(self, form):
        family = self.get_family()
        form.save(family=family)
        messages.success(self.request, "Fee dues paid successfully")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Invalid amount entered.")
        return super().form_invalid(form)




def admission_print_view(request, student_id):
    """Generates a final admission printout for a student."""
    student = get_object_or_404(Student, id=student_id)
    student_admission = student.admissions.first()  # Fetch admission record
    student_class = student_admission.student_class if student_admission else None
    # Determine School Name
    if student_admission:
        if student_admission.student_class.lower() in ['nur', 'lkg', 'ukg'] or (student_admission.student_class and student_admission.student_class.isdigit() and int(student_admission.student_class) <= 5):
            school_name = "Keshmati Devi Prathmik Vidyalaya"
            school_logo = static('images/kdpv.png')
            student_serial = student_admission.serial_no.serial_number if student_admission.serial_no.school_name == 'KDPV' else None
            school_code = "Recognition no: 05/10-08-2020 U-DISE Code: 09600104003"
        else:
            school_name = "Keshmati Devi Intermediate College"
            school_logo = static('images/kdic.png')
            student_serial = student_admission.serial_no.serial_number if student_admission.serial_no.school_name == 'KDIC' else None
            school_code = "Affiliation no: 86/20-05-2023 College Code: 1553 U-DISE Code: 09600104005"
    else:
        school_name = "Unknown School"
        school_logo = None
        student_serial = None

    # Initialize default values for parent-related variables
    mother_name = f"{student.user.mother_name}"
    mother_aadhar = "Not Provided"
    mother_occupation = "Not Provided"
    mother_phones = []
    father_name = f"{student.user.father_name}"
    father_aadhar = "Not Provided"
    father_occupation = "Not Provided"
    father_phones = []
    mother = None
    father = None

    # Fetch Parent Details
    family = Family.objects.filter(members__user=student.user).first()  # Find family of student
    
    if family:
        mother = FamilyMember.objects.filter(family=family, member_type='parent', user__gender='Female').first()
        father = FamilyMember.objects.filter(family=family, member_type='parent', user__gender='Male').first()
        
        if mother:
            mother_aadhar = mother.user.aadhar_number
            mother_occupation = mother.user.occupation
            mother_phones = mother.user.phones.all()
        
        if father:
            father_aadhar = father.user.aadhar_number
            father_occupation = father.user.occupation
            father_phones = father.user.phones.all()

    # Fetch the profile photo URL
    profile_photo_url = None
    profile_photo = student.user.documents.filter(document_name='profile_photo').first()
    if profile_photo:
        profile_photo_url = profile_photo.file_path.url

    context = {
        "mother": mother,
        "father": father,
        "student": student,
        "school_name": school_name,
        "student_admission": student_admission,
        "mother_name": mother_name,
        "mother_aadhar": mother_aadhar,
        "mother_phones": mother_phones,
        "father_name": father_name,
        "father_aadhar": father_aadhar,
        "father_phones": father_phones,
        "father_occupation": father_occupation,
        "mother_occupation": mother_occupation,
        "profile_photo_url": profile_photo_url,
        "school_logo": school_logo,
        "student_serial": student_serial,
        "school_code": school_code,
    }
    
    return render(request, "students/admission_printout.html", context)


class FamilyFeeDuesView(LoginRequiredMixin, ListView):
    template_name = 'students/family_fee_dues.html'
    context_object_name = 'fee_dues'

    def get_family(self):
        """Get the family object from the URL parameter."""
        return get_object_or_404(Family, id=self.kwargs.get('family_id'))

    def get_queryset(self):
        """Get all fee dues for the family's students in the current session."""
        family = self.get_family()
        current_session = StudentAdmission.generate_session()
        
        # Get all students in the family with active admissions
        family_members = family.members.all()
        family_members_users = family_members.values_list('user', flat=True)
        students = Student.objects.filter(user__in=family_members_users)
        
        # Get all fee dues for these students in the current session
        return FeeDue.objects.filter(
            admission__student__in=students,
            admission__session=current_session,
            admission__status='active'
        ).select_related(
            'admission__student__user',
            'fee_type',
            'transaction'
        ).order_by('admission__student__user__first_name', 'fee_type__name')

    def get_context_data(self, **kwargs):
        """Add additional context data to the template."""
        context = super().get_context_data(**kwargs)
        context['family'] = self.get_family()
        context['current_session'] = StudentAdmission.generate_session()
        
        # Calculate total dues and paid amounts
        total_dues = self.get_queryset().aggregate(
            total_amount=models.Sum('amount'),
            paid_amount=models.Sum('amount', filter=models.Q(paid=True))
        )
        
        context['total_dues'] = total_dues['total_amount'] or 0
        context['total_paid'] = total_dues['paid_amount'] or 0
        context['total_pending'] = context['total_dues'] - context['total_paid']
        
        return context



