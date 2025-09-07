import datetime
from apps.core.utils import fee_due_generate
import logging
from PIL import Image
from django.db import transaction
from django.forms import ModelChoiceField
from django.db.models import Subquery, OuterRef
from django.contrib.auth import get_user_model
from django import forms
from .models import Student, StudentSerial, StudentAdmission, PreviousInstitutionDetail, FeeStructure, FeeType, FeeDue, BoardAcademicDetails
from apps.finance.models import BankAccountDetail, PaymentTransaction, PaymentSummary, LedgerEntry, LedgerAccountType, WalletTransaction
from apps.core.utils import pay_family_fee_dues
from apps.core.models import FamilyMember, Family
from django.core.validators import RegexValidator
import uuid

logger = logging.getLogger(__name__)

User = get_user_model()




class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['height', 'weight', 'apaar_id', 'pen_number', 'is_active']





class StudentRegistrationForm(forms.Form):

    # user creation fields
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    father_name = forms.CharField(max_length=150, required=False)
    mother_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    aadhar_number = forms.CharField(
        max_length=12, 
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\d{12}$',
                message='Enter a valid 12-digit Aadhar number.'
            )
        ]
    )
    village = forms.CharField(max_length=255)
    pincode = forms.CharField(max_length=10)
    dob = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    blood_group = forms.ChoiceField(choices=User.BLOOD_GROUPS)
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES)
    religion = forms.CharField(max_length=255, required=False)
    caste = forms.CharField(max_length=255, required=False)
    category = forms.CharField(max_length=255, required=False)
    phone_number = forms.CharField(
        max_length=15, 
        required=False,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='Enter a valid 10-digit phone number.'
            )
        ]
    )
    is_whatsapp = forms.TypedChoiceField(
        choices=[(True, 'Yes'), (False, 'No')],
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        required=False
    )

    # student creation fields
    height = forms.FloatField(required=False)
    weight = forms.FloatField(required=False)
    apaar_id = forms.CharField(max_length=20, required=False)
    pen_number = forms.CharField(max_length=20, required=False)

    # student admission creation fields
    section = forms.ChoiceField(choices=StudentAdmission.SECTION_CHOICES)
    is_rte = forms.TypedChoiceField(
        choices=[(False, 'No'), (True, 'Yes')],
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        required=False
    )
    student_class = forms.ChoiceField(choices=StudentAdmission.CLASS_CHOICES)
    
    # previous institution detail creation fields
    previous_institution = forms.CharField(max_length=255, required=False)
    score = forms.DecimalField(max_digits=7, decimal_places=2, required=False)
    mm = forms.DecimalField(max_digits=7, decimal_places=2, required=False)
    percent = forms.DecimalField(max_digits=5, decimal_places=2, required=False)
    passing_year = forms.IntegerField(
        label='Passing Year',
        min_value=1000,  # Enforces 4-digit minimum
        max_value=9999,  # Enforces 4-digit maximum
        widget=forms.NumberInput(attrs={
            'type': 'number',
            'placeholder': 'Enter year like 2002',
            'min': '1000',
            'max': '9999'
        })
    )
    rte = forms.TypedChoiceField(
        choices=[(False, 'No'), (True, 'Yes')],
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        required=False
    )

    # bank details creation fields
    account_holder_name = forms.CharField(max_length=150, required=False)
    account_number = forms.CharField(max_length=15, required=False)
    ifsc = forms.CharField(max_length=20, required=False)
    branch_name = forms.CharField(max_length=255, required=False)
    account_type = forms.ChoiceField(choices=BankAccountDetail.ACCOUNT_TYPES, required=False)


    def clean(self):
        cleaned_data = super().clean()
        
        # Handle required fields
        cleaned_data["first_name"] = cleaned_data.get("first_name", "").strip().title()
        
        # Handle optional text fields - use empty string if None or empty
        optional_fields = [
            "last_name", "father_name", "mother_name", "village",
            "religion", "caste", "category", "previous_institution"
        ]
        for field in optional_fields:
            value = cleaned_data.get(field, "")
            cleaned_data[field] = value.strip().title() if value else ""

        # Handle fields that should be None if empty
        nullable_fields = ["apaar_id", "pen_number"]
        for field in nullable_fields:
            value = cleaned_data.get(field, "")
            cleaned_data[field] = value.strip() if value else None

        # Handle email separately since it needs to be lowercase
        email = cleaned_data.get("email", "")
        cleaned_data["email"] = email.strip().lower() if email else None

        # Handle Aadhar number - ensure it's None if empty
        aadhar = cleaned_data.get("aadhar_number", "")
        if aadhar:
            if not aadhar.isdigit() or len(aadhar) != 12:
                raise forms.ValidationError({"aadhar_number": "Enter a valid 12-digit Aadhar number."})
            cleaned_data["aadhar_number"] = aadhar
        else:
            cleaned_data["aadhar_number"] = None

        # Handle phone number validation
        phone = cleaned_data.get("phone_number", "")
        if phone:
            if not phone.isdigit() or len(phone) != 10:
                raise forms.ValidationError({"phone_number": "Enter a valid 10-digit phone number."})
        
        # Generate username dynamically based on first name, last name, and dob
        first_name = cleaned_data.get("first_name", "").strip().lower()
        last_name = cleaned_data.get("last_name", "").strip().lower()
        dob = str(cleaned_data.get("dob", "")).replace("-", "")  # Remove dashes from DOB

        # Create a username and password based on these values
        if last_name:
            username = f"{first_name}{last_name}{dob}".replace(" ", "")
            password = f"{first_name.capitalize()}{last_name}{dob}@123".replace(" ", "")
        else:
            username = f"{first_name}{dob}".replace(" ", "")
            password = f"{first_name.capitalize()}{dob}@123".replace(" ", "")

        # Set the generated username and password in cleaned_data
        cleaned_data["username"] = username
        cleaned_data["password"] = password

        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("This email is already in use.")
        return email
    
    
    def clean_aadhar_card(self):
        aadhar_card = self.cleaned_data.get("aadhar_card")
        if aadhar_card:
            if aadhar_card.content_type not in ['application/pdf']:
                raise forms.ValidationError("Invalid file type. Use PDF.")
            if aadhar_card.size > 1 * 1024 * 1024:  # 1 MB limit
                raise forms.ValidationError("File size exceeds 1MB.")
            return aadhar_card
        return None
    
    def clean_birth_certificate(self):
        birth_certificate = self.cleaned_data.get("birth_certificate")
        if birth_certificate:
            if birth_certificate.content_type not in ['application/pdf']:
                raise forms.ValidationError("Invalid file type. Use PDF.")
            if birth_certificate.size > 1 * 1024 * 1024:  # 1 MB limit
                raise forms.ValidationError("File size exceeds 1MB.")
            return birth_certificate
        return None
    
    def clean_caste_certificate(self):
        caste_certificate = self.cleaned_data.get("caste_certificate")  
        if caste_certificate:
            if caste_certificate.content_type not in ['application/pdf']:
                raise forms.ValidationError("Invalid file type. Use PDF.")
            if caste_certificate.size > 1 * 1024 * 1024:  # 1 MB limit
                raise forms.ValidationError("File size exceeds 1MB.")
            return caste_certificate
        return None

    def clean_mark_sheet(self):
        mark_sheet = self.cleaned_data.get("mark_sheet")
        if mark_sheet:
            if mark_sheet.content_type not in ['application/pdf']:
                raise forms.ValidationError("Invalid file type. Use PDF.")
            if mark_sheet.size > 1 * 1024 * 1024:  # 1 MB limit
                raise forms.ValidationError("File size exceeds 1MB.")
            return mark_sheet
        return None
    
    def clean_transfer_certificate(self):
        transfer_certificate = self.cleaned_data.get("transfer_certificate")
        if transfer_certificate:
            if transfer_certificate.content_type not in ['application/pdf']:
                raise forms.ValidationError("Invalid file type. Use PDF.")
            if transfer_certificate.size > 1 * 1024 * 1024:  # 1 MB limit
                raise forms.ValidationError("File size exceeds 1MB.")
            return transfer_certificate
        return None
    
    def clean_is_rte(self):
        is_rte = self.cleaned_data.get("is_rte")
        if is_rte == True:
            self.cleaned_data["is_rte"] = True
        else:
            self.cleaned_data["is_rte"] = False
        return self.cleaned_data["is_rte"]
    
    def clean_rte(self):
        rte = self.cleaned_data.get("rte")
        if rte == True:
            self.cleaned_data["rte"] = True
        else:
            self.cleaned_data["rte"] = False
        return self.cleaned_data["rte"]
    
    def clean_apaar_id(self):
        apaar_id = self.cleaned_data.get("apaar_id")
        if apaar_id:
            if apaar_id == "":
                self.cleaned_data["apaar_id"] = None
        return self.cleaned_data["apaar_id"]
    
    def clean_pen_number(self):
        pen_number = self.cleaned_data.get("pen_number")
        if pen_number:
            if pen_number == "":
                self.cleaned_data["pen_number"] = None
        return self.cleaned_data["pen_number"]
    
    def clean_mm(self):
        mm = self.cleaned_data.get("mm")
        if mm:
            if mm < self.cleaned_data.get("score"):
                raise forms.ValidationError("Score cannot be greater than MM.")
            return mm
    
    def save(self, commit=True):
        try:
            with transaction.atomic():
                user_data = {
                    "username": self.cleaned_data["username"],
                    "first_name": self.cleaned_data["first_name"],
                    "last_name": self.cleaned_data["last_name"],
                    "father_name": self.cleaned_data["father_name"],
                    "mother_name": self.cleaned_data["mother_name"],
                    "village": self.cleaned_data["village"],
                    "pincode": self.cleaned_data["pincode"],
                    "dob": self.cleaned_data["dob"],
                    "blood_group": self.cleaned_data["blood_group"],
                    "aadhar_number": self.cleaned_data["aadhar_number"],
                    "gender": self.cleaned_data["gender"],
                    "religion": self.cleaned_data["religion"],
                    "caste": self.cleaned_data["caste"],
                    "category": self.cleaned_data["category"],
                    "password": self.cleaned_data["password"]
                }
                if self.cleaned_data["email"]:
                    user_data["email"] = self.cleaned_data["email"]
                
                user = User.objects.create_user(**user_data)

                phone = self.cleaned_data.get("phone_number", "")
                if phone:
                    user.phones.create(
                        phone_number=phone,
                        is_whatsapp=self.cleaned_data["is_whatsapp"]
                        
                    )
            
                student = Student.objects.create(
                    user=user,
                    height=self.cleaned_data["height"],
                    weight=self.cleaned_data["weight"],
                    apaar_id=self.cleaned_data["apaar_id"],
                    pen_number=self.cleaned_data["pen_number"]
                )

                student_admission = StudentAdmission.objects.create(
                    student=student,
                    section=self.cleaned_data["section"],
                    is_rte=self.cleaned_data["is_rte"],
                    student_class=self.cleaned_data["student_class"],
                    
                )

                fee_due_generate(student)

                if self.cleaned_data["previous_institution"] and self.cleaned_data["score"] and self.cleaned_data["mm"]:
                    PreviousInstitutionDetail.objects.create(
                        student=student,
                        previous_institution=self.cleaned_data["previous_institution"],
                        score=self.cleaned_data["score"],
                        mm=self.cleaned_data["mm"],
                        rte=self.cleaned_data["rte"],
                        passing_year=self.cleaned_data["passing_year"]
                    )
                
                return student_admission
        except Exception as e:
            raise e
            


class StudentDocumentForm(forms.Form):
    # Student document upload fields
    aadhar_card = forms.FileField(required=False)
    birth_certificate = forms.FileField(required=False)
    caste_certificate = forms.FileField(required=False)
    mark_sheet = forms.FileField(required=False)
    transfer_certificate = forms.FileField(required=False)

    def save(self, commit=True):
        """Save the uploaded documents for the associated user."""
        user = self.cleaned_data.get('user')  # Get the user passed from the view
        if not user:
            raise ValueError("User not provided for document upload.")

        try:
            with transaction.atomic():
                document_fields = {
                    "aadhar_card": ("Aadhar Card", "ID Card"),
                    "birth_certificate": ("Birth Certificate", "Certificate"),
                    "caste_certificate": ("Caste Certificate", "Certificate"),
                    "mark_sheet": ("Mark Sheet", "Mark Sheet"),
                    "transfer_certificate": ("Transfer Certificate", "Certificate"),
                }

                for field_name, (doc_name, doc_type) in document_fields.items():
                    file = self.cleaned_data.get(field_name)
                    if file:
                        user.documents.create(
                            file_path=file,
                            document_name=doc_name,
                            document_type=doc_type,
                            document_context="student_admission",
                        )
        except Exception as e:
            raise e



class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['name', 'start_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'})
        }


class FeeTypeForm(forms.ModelForm):
    add_quarterly_fee = forms.BooleanField(required=False,
                                           label="Add Quarterly Fee",
                                           help_text="Check this box to add a quarterly fee for this fee type."
                                           )

    class Meta:
        model = FeeType
        fields = ['name', 'amount', 'add_quarterly_fee']

    def clean(self):
        cleaned_data = super().clean()
        # You can handle any custom validation logic here if needed.
        return cleaned_data


class PayFamilyFeeDuesForm(forms.Form):
    due_ids = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select Fee Dues to Pay"
    )
    pay_all = forms.BooleanField(required=False, label="Pay All Dues")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)

        # Populate due choices dynamically
        if self.family:
            member_users = self.family.members.values_list('user', flat=True)
            dues = FeeDue.objects.filter(
                admission__student__user__in=member_users,
                paid=False
            ).select_related('fee_type', 'admission')

            choices = []
            for due in dues:
                label = f"{due.admission.student.user.get_full_name()} - {due.fee_type.name} - ₹{due.amount}"
                choices.append((str(due.id), label))

            self.fields['due_ids'].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        pay_all = cleaned_data.get("pay_all", False)

        if not pay_all:
            # Manually override due_ids from raw POST in case HTML checkboxes were manually rendered
            selected_due_ids = self.data.getlist("due_ids")
            cleaned_data["due_ids"] = selected_due_ids

        return cleaned_data

    def save(self):
        family = self.family
        pay_all = self.cleaned_data.get('pay_all', False)

        # Always pull raw due_ids from form data directly
        raw_selected_ids = self.data.getlist("due_ids")  # <-- critical fix

        if not family:
            raise ValueError("Family not provided.")

        with transaction.atomic():
            old_balance = family.wallet_balance
            if old_balance <= 0:
                raise ValueError("Family wallet balance is 0.")

            family_parent = family.members.filter(
                member_type=FamilyMember.MemberType.PARENT, user__gender='Male'
            ).first() or family.members.filter(
                member_type=FamilyMember.MemberType.PARENT, user__gender='Female'
            ).first() or family.members.filter(
                member_type=FamilyMember.MemberType.GRANDPARENT, user__gender='Male'
            ).first() or family.members.filter(
                member_type=FamilyMember.MemberType.GRANDPARENT, user__gender='Female'
            ).first() or family.members.filter(
                member_type=FamilyMember.MemberType.OTHER, user__gender='Male'
            ).first() or family.members.filter(
                member_type=FamilyMember.MemberType.OTHER, user__gender='Female'
            ).first()

            if not family_parent:
                raise ValueError("No family user found.")

            family_user = family_parent.user

            payment_transaction = PaymentTransaction.objects.create(
                user=family_user,
                agent=self.user,
                method='WALLET',
                status='SUCCESSFUL',
            )

            selected_due_ids = None if pay_all else list(map(uuid.UUID, raw_selected_ids))
            
            left_over_budget, payment_data = pay_family_fee_dues(family, payment_transaction, selected_due_ids)

            family.wallet_balance = left_over_budget
            family.save()

            amount_paid = old_balance - left_over_budget
            payment_transaction.amount = amount_paid
            payment_transaction.description = f"Fee dues payment of ₹{amount_paid}"
            payment_transaction.save()

            WalletTransaction.objects.create(
                family=family,
                current_balance=family.wallet_balance,
                previous_balance=old_balance,
                transaction_type='DEBIT',
                payment_transaction=payment_transaction
            )

            PaymentSummary.objects.create(
                payment_transaction=payment_transaction,
                customer=family_user,
                amount=amount_paid,
                details={"type": "fee", **payment_data}
            )

            fee_account = LedgerAccountType.objects.get(name='FEE')
            wallet_account = LedgerAccountType.objects.get(name='WALLET')

            LedgerEntry.objects.create(
                payment_transaction=payment_transaction,
                amount=amount_paid,
                entry_type='DEBIT',
                account_type=wallet_account,
                description=f"Fee dues payment of ₹{amount_paid}"
            )
            LedgerEntry.objects.create(
                payment_transaction=payment_transaction,
                amount=amount_paid,
                entry_type='CREDIT',
                account_type=fee_account,
                description=f"Fee dues payment of ₹{amount_paid}"
            )

CLASS_CHOICES = [(i, str(i)) for i in range(9, 13)]
BOARD_CHOICES = [
    ('UPMSP', 'UPMSP'),
    ('CBSE', 'CBSE'),
    ('ICSE', 'ICSE'),
]

class BoardAcademicDetailsForm(forms.ModelForm):
    student = ModelChoiceField(
        queryset=Student.objects.none(),  # Initially empty queryset
        label="Student",
    )
    
    student_class = forms.ChoiceField(choices=CLASS_CHOICES, label="Class")
    board = forms.ChoiceField(choices=BOARD_CHOICES, label="Board")
    passing_year = forms.IntegerField(min_value=1000, max_value=datetime.date.today().year, label="Year of Passing")
    is_passed = forms.TypedChoiceField(
        choices=[(True, 'Yes'), (False, 'No')],
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        required=False
    )

    class Meta:
        model = BoardAcademicDetails
        fields = ['student', 'student_class', 'roll_no', 'board', 'school', 'passing_year', 'is_passed', 'score', 'mm', 'subject_group']
        widgets = {
            'roll_no': forms.NumberInput(attrs={'min': 1}),
            'passing_year': forms.NumberInput(attrs={'min': 1000, 'max': datetime.date.today().year}),
            'school': forms.TextInput(attrs={'placeholder': 'School name'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Get the queryset for the student field
        queryset = Student.objects.filter(
            admissions__student_class__in=[9, 10, 11, 12]
        ).distinct()

        # Annotate students
        students = queryset.annotate(
            student_class=Subquery(
                StudentAdmission.objects.filter(student=OuterRef('pk')).values('student_class')[:1]
            ),
            family_name=Subquery(
                Family.objects.filter(
                    members__user=OuterRef('user')
                ).values('family_name')[:1]
            )
        )

        # Update the queryset of the student field
        self.fields['student'].queryset = students

        # Set the label of the student field
        self.fields['student'].label_from_instance = lambda student: f"{student.user.first_name} {student.user.last_name} - Class: {student.admissions.order_by('admission_date').last().student_class} ({student.family_name})"

        # If a user is provided, filter students based on the user
        if user and hasattr(user, 'student'):
            self.fields['student'].queryset = self.fields['student'].queryset.filter(user=user)
