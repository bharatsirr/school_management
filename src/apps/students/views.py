from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, FormView
from .models import Student, StudentAdmission, FeeStructure, FeeType, FeeDue, BoardAcademicDetails
from .forms import StudentRegistrationForm, FeeStructureForm, FeeTypeForm, StudentUpdateForm, StudentDocumentForm, PayFamilyFeeDuesForm, StudentSerial, PreviousInstitutionDetail, BoardAcademicDetailsForm
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
from apps.core.models import Family, FamilyMember, Phone
from django.templatetags.static import static
from apps.core.utils import fee_due_generate
User = get_user_model()






    

# Student Registration View
class StudentRegistrationView(LoginRequiredMixin, View):
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
    

class StudentUpdateView(LoginRequiredMixin, UpdateView):
    model = Student
    form_class = StudentUpdateForm
    template_name = 'students/student_update_form.html'
    success_url = reverse_lazy('student_admission_list')




# Fee Structure Creation View
class FeeStructureCreateView(LoginRequiredMixin, CreateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'students/fee_structure_form.html'
    success_url = reverse_lazy('fee_structure_list')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Fee structure created successfully')
        return redirect(self.success_url)
    
    
class FeeStructureListView(LoginRequiredMixin, ListView):
    model = FeeStructure
    template_name = 'students/fee_structure_list.html'
    context_object_name = 'fee_structures'
    queryset = FeeStructure.active_objects.all()


# Fee Structure Update View
class FeeStructureUpdateView(LoginRequiredMixin, UpdateView):
    model = FeeStructure
    form_class = FeeStructureForm
    template_name = 'students/fee_structure_form.html'
    success_url = reverse_lazy('fee_structure_list')



class AddFeeTypeView(LoginRequiredMixin, CreateView):
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



class PayFamilyFeeDuesView(LoginRequiredMixin, FormView):
    form_class = PayFamilyFeeDuesForm
    template_name = 'students/pay_family_fee_dues.html'
    success_url = reverse_lazy('family_list')

    def get_family(self):
        return get_object_or_404(Family, id=self.kwargs.get("family_id"))
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['family'] = self.get_family()
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        family = self.get_family()
        context['family'] = family

        # Get family members' users
        family_members_users = family.members.values_list('user', flat=True)

        # Get active students associated with those users
        students = Student.objects.filter(user__in=family_members_users).distinct()

        # Build dues_by_student
        dues_by_student = defaultdict(list)
        for student in students:
            
            unpaid_dues = FeeDue.objects.filter(
                admission__student=student,
                paid=False
            ).select_related('fee_type', 'admission').order_by("admission__admission_date", "id")

            if unpaid_dues.exists():
                dues_by_student[student] = unpaid_dues
        context['dues_by_student'] = [(student, dues_by_student[student]) for student in dues_by_student]
        
        return context
    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Fee dues paid successfully")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Invalid amount entered.")
        return super().form_invalid(form)



@login_required
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




@login_required
def promotion_class_selection(request):
    class_choices = StudentAdmission.CLASS_CHOICES
    return render(request, 'students/promotion_class_selection.html', {'class_choices': class_choices})


@login_required
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



class StudentAdmissionListView(LoginRequiredMixin, ListView):
    model = StudentAdmission
    template_name = 'students/admission_list.html'
    context_object_name = 'student_admissions'
    paginate_by = 500

    def get_queryset(self):
        session = self.request.GET.get('session', '').strip()
        class_code = self.request.GET.get('class_code', '').strip()
        school = self.request.GET.get('school', '').strip()

        
        queryset = StudentAdmission.objects.select_related(
            'student__user__family_member__family', 
            'serial_no', 
            'fee_structure'
        ).prefetch_related(
            Prefetch('student__user__phones'), 
            Prefetch('student__previous_institution')
        ).order_by('-admission_date')

        filters = {}
        if class_code:
            filters['student_class'] = class_code
        if session:
            filters['session'] = session
        if school:
            filters['serial_no__serial_number__icontains'] = school

        queryset = queryset.filter(**filters)

        total_admissions = queryset.count()
        girls_admissions = queryset.filter(student__user__gender='Female').count()
        boys_admissions = queryset.filter(student__user__gender='Male').count()

        total_students = Student.objects.count()
        girls_students = Student.objects.filter(user__gender='Female').count()
        boys_students = Student.objects.filter(user__gender='Male').count()

        self.extra_context = {
            'total_admissions': total_admissions,
            'girls_admissions': girls_admissions,
            'boys_admissions': boys_admissions,
            'total_students': total_students,
            'girls_students': girls_students,
            'boys_students': boys_students
        }

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
        context['current_session'] = self.request.GET.get('session')
        context['selected_class_code'] = self.request.GET.get('class_code', '')
        context['selected_school'] = self.request.GET.get('school', '')
        context['session_list'] = sessions
        return context
    




class DownloadStudentsListView(LoginRequiredMixin, View):
    def get(self, request):
        
        return render(request, 'students/download_students_list.html')



    def post(self, request):
        school = request.POST.get('school', '').strip().upper()
        school_name = (
            "Keshmati Devi Intermediate College, Affi: 86/20-05-2023 Clg: 1553 U-DISE: 09600104005"
            if school == 'KDIC'
            else "Keshmati Devi Prathmik Vidyalaya, Recogn: 05/10-08-2020 U-DISE Code: 09600104003"
        )

        user_with_phones = Prefetch(
            'user__phones',
            queryset=Phone.objects.all(),
            to_attr='all_phones'
        )

        # Prefetch admissions, family members, and phones
        admissions_prefetch = Prefetch(
            'student__admissions',
            queryset=StudentAdmission.objects.order_by('admission_date'),
            to_attr='ordered_admissions'
        )

        family_members_prefetch = Prefetch(
            'student__user__family_member__family__members',
            queryset=FamilyMember.objects.select_related('user').prefetch_related(user_with_phones),
            to_attr='all_members'
        )

        previous_institution_prefetch = Prefetch(
            'student__previous_institution',
            queryset=PreviousInstitutionDetail.objects.all(),  # or by date, or whatever criteria
            to_attr='fetched_previous_institutions'
        )

        student_user_phones_prefetch = Prefetch(
            'student__user__phones',
            queryset=Phone.objects.all(),
            to_attr='all_phones'
        )

        # Optimized query
        serials = (
            StudentSerial.objects
            .filter(school_name=school)
            .select_related('student__user')
            .prefetch_related(admissions_prefetch, family_members_prefetch, previous_institution_prefetch, student_user_phones_prefetch)
            .order_by('serial_number')
        )

        # Populate additional data for PDF
        for serial in serials:
            # First admission
            admission = serial.student.ordered_admissions[0] if serial.student.ordered_admissions else None
            if not admission:
                continue
            student = admission.student
            serial.pen = student.pen_number
            serial.apaar_id = student.apaar_id

            previous_institution = getattr(student, 'fetched_previous_institutions', [None])
            if previous_institution:
                print(previous_institution.previous_institution)

            serial.previous_institution = previous_institution.previous_institution if previous_institution else ''
            serial.admission = admission
            serial.admission_date = admission.admission_date.strftime('%d-%m-%Y')
            serial.student_user = admission.student.user
            serial.student_dob = serial.student_user.dob.strftime('%d-%m-%Y')
            serial.student_photo = request.build_absolute_uri(serial.student_user.profile_photo)

            # Prefetched family members
            members = getattr(serial.student_user.family_member.family, 'all_members', [])

            father_user = next(
                (m.user for m in members if m.member_type == FamilyMember.MemberType.PARENT and m.user.gender == 'Male'),
                None
            )
            mother_user = next(
                (m.user for m in members if m.member_type == FamilyMember.MemberType.PARENT and m.user.gender == 'Female'),
                None
            )

            father_phone_obj = getattr(father_user, 'all_phones', [])
            serial.father_phone = father_phone_obj[0].phone_number if father_phone_obj else ''

            mother_phone_obj = getattr(mother_user, 'all_phones', [])
            serial.mother_phone = mother_phone_obj[0].phone_number if mother_phone_obj else ''

            student_phone_obj = getattr(serial.student_user, 'all_phones', [])
            serial.student_phone = student_phone_obj[0].phone_number if student_phone_obj else ''


        # Render HTML template
        return render(request, 'students/download_students_list_format.html', {'serials': serials, 'school_name': school_name})



class BoardAcademicCreateView(LoginRequiredMixin, CreateView):
    model = BoardAcademicDetails
    form_class = BoardAcademicDetailsForm
    template_name = 'students/board_academic_details_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        if hasattr(self.request.user, 'student'):
            obj.student = self.request.user.student
        obj.save()
        messages.success(self.request, "Board academic details saved.")
        return redirect('home')



class BoardAcademicUpdateView(LoginRequiredMixin, UpdateView):
    model = BoardAcademicDetails
    form_class = BoardAcademicDetailsForm
    template_name = 'students/board_academic_details_form.html'  # same template as create

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        if hasattr(self.request.user, 'student'):
            obj.student = self.request.user.student
        obj.save()
        messages.success(self.request, "Board academic details updated.")
        return redirect('board_list')  # change to wherever you want after update



class BoardAcademicListView(LoginRequiredMixin, ListView):
    model = BoardAcademicDetails
    template_name = 'students/board_academic_details_list.html'
    context_object_name = 'boards'
    paginate_by = 10  # optional, adds pagination

    def get_queryset(self):
        qs = super().get_queryset().select_related('student', 'student__user')
        if hasattr(self.request.user, 'student'):
            # If student logs in, only show their records
            qs = qs.filter(student=self.request.user.student)
        return qs