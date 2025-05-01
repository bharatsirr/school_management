from django.core.paginator import Paginator
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, FormView
from .models import Student, StudentAdmission, FeeStructure, FeeType, FeeDue
from .forms import StudentRegistrationForm, FeeStructureForm, FeeTypeForm, StudentUpdateForm, StudentDocumentForm, PayFamilyFeeDuesForm
from django.views import View
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from collections import defaultdict
from django.urls import reverse_lazy, reverse
from django.db import transaction
from django.db.models import Prefetch, Sum
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from apps.core.models import Family, FamilyMember
from django.templatetags.static import static
from apps.core.utils import fee_due_generate
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
        # Fetch the FeeStructure instance based on the URL parameter
        self.fee_structure = FeeStructure.objects.get(id=kwargs['fee_structure_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Add the FeeStructure to the form instance before saving
        form.instance.fee_structure = self.fee_structure

        # Get the value of 'add_quarterly_fee' from the form
        add_quarterly_fee = form.cleaned_data.get('add_quarterly_fee', False)

        # If add_quarterly_fee is True, create four FeeType instances for Q1-Q4
        if add_quarterly_fee:
            # Create four new FeeType instances for each quarter
            for i in range(1, 5):  # For Q1 to Q4
                new_fee_type = FeeType(
                    name=f"{form.instance.name}_q{i}",
                    amount=form.cleaned_data['amount'],
                    fee_structure=self.fee_structure,  # Associate with the FeeStructure
                )
                new_fee_type.save()  # Save each new FeeType instance

            # After creating the quarterly instances, we don't save the original FeeType instance
            # We only want to save the quarterly FeeType instances (tuition_q1 to tuition_q4).
            return HttpResponseRedirect(self.get_success_url())

        # If add_quarterly_fee is False, just save the regular FeeType instance
        return super().form_valid(form)
    

    def get_success_url(self):
        # Redirect to the FeeStructure list page or another page
        return reverse('fee_structure_list')



class PayFamilyFeeDuesView(FormView):
    form_class = PayFamilyFeeDuesForm
    template_name = 'students/pay_family_fee_dues.html'
    success_url = reverse_lazy('family_list')

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




def admission_print_view(request, studentadmission_id):
    """Generates a final admission printout for a student based on the specific admission ID."""
    student_admission = get_object_or_404(StudentAdmission, id=studentadmission_id)
    student = student_admission.student  # Fetch the related student
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
    family = Family.objects.filter(members__user=student.user).first()

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
    context_object_name = 'fee_dues_by_session'

    def get_family(self):
        return get_object_or_404(Family, id=self.kwargs.get('family_id'))

    def get_students(self):
        family = self.get_family()
        family_members_users = family.members.values_list('user', flat=True)
        return Student.objects.filter(user__in=family_members_users)

    def get_queryset(self):
        students = self.get_students()

        # All dues: both paid and unpaid
        all_dues = FeeDue.objects.filter(
            admission__student__in=students
        ).select_related(
            'admission__student__user',
            'admission__serial_no',
            'admission__fee_structure',
            'fee_type',
            'transaction'
        ).order_by(
            'admission__session',
            'admission__student__user__first_name',
            'fee_type__name'
        )
        return all_dues

    def group_fee_dues_by_session(self, fee_dues):
        grouped = defaultdict(list)
        for due in fee_dues:
            session = due.admission.session
            grouped[session].append(due)

        def session_sort_key(session_str):
            try:
                return int(session_str.split('-')[0])
            except (ValueError, IndexError):
                return 0

        return dict(sorted(grouped.items(), key=lambda x: session_sort_key(x[0]), reverse=True))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family = self.get_family()
        current_session = StudentAdmission.generate_session()
        all_dues = self.get_queryset()

        grouped_dues = self.group_fee_dues_by_session(all_dues)

        total_paid = all_dues.filter(paid=True).aggregate(total=Sum('amount'))['total'] or 0
        total_pending = all_dues.filter(paid=False).aggregate(total=Sum('amount'))['total'] or 0
        total_dues = total_pending + total_paid  # can also be computed as (total_due - total_paid)

        context.update({
            'family': family,
            'current_session': current_session,
            'fee_dues_by_session': grouped_dues,
            'total_paid': total_paid,
            'total_dues': total_dues,
            'total_pending': total_pending,
        })
        return context





def promotion_class_selection(request):
    class_choices = StudentAdmission.CLASS_CHOICES
    return render(request, 'students/promotion_class_selection.html', {'class_choices': class_choices})



def bulk_promote_view(request, class_code):
    current_session = StudentAdmission.generate_session()
    start_year = int(current_session.split('-')[0])
    previous_session = StudentAdmission.generate_session(year=start_year - 1)

    class_index = StudentAdmission.CLASS_ORDER.index(class_code)

    valid_class_choices = [
        (code, name) for code, name in StudentAdmission.CLASS_CHOICES
        if StudentAdmission.CLASS_ORDER.index(code) >= class_index
    ]

    previous_admissions = StudentAdmission.objects.filter(
        session=previous_session,
        student_class=class_code,
        status='active'
    ).exclude(
        student__admissions__session=current_session,
        student__admissions__status='active'
    ).select_related('student', 'student__user')

    if request.method == 'POST':
        processed_count = 0
        for admission in previous_admissions:
            promote_to = request.POST.get(f'promote_to_{admission.id}')
            status = request.POST.get(f'status_{admission.id}')
            is_rte = request.POST.get(f'is_rte_{admission.id}') == 'yes'
            if not promote_to or not status:
                continue  # skip if missing

            # Convert to index for proper comparison
            try:
                promote_to_index = StudentAdmission.CLASS_ORDER.index(promote_to)
                current_class_index = StudentAdmission.CLASS_ORDER.index(admission.student_class)
            except ValueError:
                continue  # invalid class code

            if status == 'skip':
                continue

            if status == 'dropped':
                admission.status = 'dropped'
                admission.save()
                continue  # no new admission

            if status == 'graduated':
                admission.status = 'graduated'
                admission.save()
                continue  # no new admission

            if promote_to_index <= current_class_index and status == 'failed':
                # Student is not promoted, mark as failed and keep in same class
                with transaction.atomic():
                    admission.status = 'failed'
                    admission.save()

                    StudentAdmission.objects.create(
                        student=admission.student,
                        session=current_session,
                        student_class=admission.student_class,
                        status='active',
                        is_rte=is_rte
                    )
                    fee_due_generate(admission.student)

            elif promote_to_index > current_class_index and status == 'passed':
                # Student is promoted, mark as passed and promote to requested class
                with transaction.atomic():
                    admission.status = 'passed'
                    admission.save()

                    StudentAdmission.objects.create(
                        student=admission.student,
                        session=current_session,
                        student_class=promote_to,
                        status='active',
                        is_rte=is_rte
                    )
                    fee_due_generate(admission.student)
            else:
                # Student promoted to next class in the order
                with transaction.atomic():
                    admission.status = 'passed'
                    admission.save()

                    try:
                        current_class_index = StudentAdmission.CLASS_ORDER.index(admission.student_class)
                        next_class = StudentAdmission.CLASS_ORDER[current_class_index + 1]
                    except (ValueError, IndexError):
                        # In case current class is not found or already the last class
                        continue

                    StudentAdmission.objects.create(
                        student=admission.student,
                        session=current_session,
                        student_class=next_class,
                        status='active',
                        is_rte=is_rte
                    )
                    fee_due_generate(admission.student)

            processed_count += 1

        messages.success(request, f'{processed_count} students processed successfully.')
        return redirect('promotion_class_selection')

    return render(request, 'students/bulk_promote.html', {
        'class_code': class_code,
        'current_session': current_session,
        'previous_session': previous_session,
        'students_to_promote': previous_admissions,
        'class_choices': valid_class_choices,
    })



class StudentAdmissionListView(ListView):
    model = StudentAdmission
    template_name = 'students/admission_list.html'
    context_object_name = 'student_admissions'
    paginate_by = 500

    def get_queryset(self):
        session = self.request.GET.get('session')
        class_code = self.request.GET.get('class_code')

        if not session:
            session = StudentAdmission.generate_session()

        queryset = StudentAdmission.objects.select_related(
            'student__user__family_member__family', 
            'serial_no', 
            'fee_structure'
        ).prefetch_related(
            Prefetch('student__user__phones'), 
            Prefetch('student__previous_institution')
        ).filter(
            session=session,
        ).order_by('-admission_date')

        if class_code:
            queryset = queryset.filter(student_class=class_code)

        for admission in queryset:
            admission.profile_photo_url = admission.student.user.profile_photo

            # Correct fetching of family name
            family_member = getattr(admission.student.user, 'family_member', None)
            admission.family_name = family_member.family.family_name if family_member and family_member.family else ''

            admission.student_serial_number = admission.serial_no.serial_number if admission.serial_no else ''

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Build session list from 2023 to current
        start_year = 2022
        current_year = timezone.localtime(timezone.now()).date().year
        sessions = []
        for year in range(start_year, current_year + 2):  # +2 to include session like 2024-2025
            sessions.append(f"{year}-{year + 1}")

        context['class_choices'] = StudentAdmission.CLASS_CHOICES
        context['current_session'] = self.request.GET.get('session') or StudentAdmission.generate_session()
        context['selected_class_code'] = self.request.GET.get('class_code', '')
        context['session_list'] = sessions
        return context