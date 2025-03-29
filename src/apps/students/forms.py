import logging
from django.conf import settings
from apps.core.utils import delete_files_from_local, delete_files_from_s3
from PIL import Image
from django.db import transaction
from django.contrib.auth import get_user_model
from django import forms
from .models import Student, StudentSerial, StudentAdmission, PreviousInstitutionDetail, FeeStructure, FeeType, FeeDue
from apps.finance.models import BankAccountDetail

logger = logging.getLogger(__name__)

User = get_user_model()




class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['height', 'weight', 'apaar_id', 'pen_number', 'is_active']





class StudentRegistrationForm(forms.Form):

    # user creation fields
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    father_name = forms.CharField(max_length=150)
    mother_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    village = forms.CharField(max_length=255)
    pincode = forms.CharField(max_length=10)
    dob = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    blood_group = forms.ChoiceField(choices=User.BLOOD_GROUPS)
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES)
    cropped_image = forms.FileField(required=True)
    phone_number = forms.CharField(max_length=15)
    is_whatsapp = forms.RadioSelect(choices=[(True, 'Yes'), (False, 'No')])

    # student creation fields
    height = forms.FloatField(required=False)
    weight = forms.FloatField(required=False)
    apaar_id = forms.CharField(max_length=20, required=False)
    pen_number = forms.CharField(max_length=20, required=False)

    # student admission creation fields
    section = forms.ChoiceField(choices=StudentAdmission.SECTION_CHOICES)
    is_rte = forms.ChoiceField(choices=[(True, 'Yes'), (False, 'No')])
    student_class = forms.ChoiceField(choices=StudentAdmission.CLASS_CHOICES)
    
    # previous institution detail creation fields
    previous_institution = forms.CharField(max_length=255, required=False)
    score = forms.DecimalField(max_digits=7, decimal_places=2, required=False)
    mm = forms.DecimalField(max_digits=7, decimal_places=2, required=False)
    percent = forms.DecimalField(max_digits=5, decimal_places=2, required=False)
    rte = forms.ChoiceField(choices=[(True, 'Yes'), (False, 'No')], required=False)

    # bank details creation fields
    account_holder_name = forms.CharField(max_length=150, required=False)
    account_number = forms.CharField(max_length=15, required=False)
    ifsc = forms.CharField(max_length=20, required=False)
    branch_name = forms.CharField(max_length=255, required=False)
    account_type = forms.ChoiceField(choices=BankAccountDetail.ACCOUNT_TYPES, required=False)
    # student document upload fields
    aadhar_card = forms.FileField(required=False)
    birth_certificate = forms.FileField(required=False)
    caste_certificate = forms.FileField(required=False)
    mark_sheet = forms.FileField(required=False)
    transfer_certificate = forms.FileField(required=False)


    def clean(self):
        cleaned_data = super().clean()
        
        cleaned_data["first_name"] = cleaned_data.get("first_name", "").strip().title()
        cleaned_data["last_name"] = cleaned_data.get("last_name", "").strip().title()
        cleaned_data["father_name"] = cleaned_data.get("father_name", "").strip().title()
        cleaned_data["mother_name"] = cleaned_data.get("mother_name", "").strip().title()
        cleaned_data["village"] = cleaned_data.get("village", "").strip().title()
        cleaned_data["email"] = cleaned_data.get("email", "").strip().lower()
        cleaned_data["apaar_id"] = cleaned_data.get("apaar_id", "").strip()
        cleaned_data["pen_number"] = cleaned_data.get("pen_number", "").strip()
        cleaned_data["previous_institution"] = cleaned_data.get("previous_institution", "").strip().title()
        
        
        # Generate username dynamically based on first name, last name, and dob
        first_name = cleaned_data.get("first_name", "").strip().lower()
        last_name = cleaned_data.get("last_name", "").strip().lower()
        dob = str(cleaned_data.get("dob", "")).replace("-", "")  # Remove dashes from DOB

        # Create a username and password based on these values
        username = f"{first_name}_{last_name}_{dob}"
        password = f"{first_name.capitalize()}_{last_name}_{dob}_@123"

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
    
    def clean_cropped_image(self):
        image = self.cleaned_data.get('cropped_image')
        if image:
            if image.content_type not in ['image/jpeg', 'image/png']:
                raise forms.ValidationError("Invalid image type. Use JPEG or PNG.")

            if image.size > 1/2 * 1024 * 1024:  # .5 MB limit
                raise forms.ValidationError("Image size exceeds 0.5MB.")
            
            try:
                with Image.open(image) as img:
                    width, height = img.size
                    if width < 300 or height < 400:
                        raise forms.ValidationError("Image must be at least 300x400 pixels.")
            except Exception:
                raise forms.ValidationError("Invalid image file.")
            
            return image
        raise forms.ValidationError("Profile image is required.")
    
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
    
    def clean_is_whatsapp(self):
        is_whatsapp = self.cleaned_data.get("is_whatsapp")
        if is_whatsapp == True:
            self.cleaned_data["is_whatsapp"] = True
        return self.cleaned_data["is_whatsapp"]
    
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
                    "gender": self.cleaned_data["gender"],
                    "password": self.cleaned_data["password"]
                }
                if self.cleaned_data["email"]:
                    user_data["email"] = self.cleaned_data["email"]
                
                user = User.objects.create_user(**user_data)

                user.documents.create(
                    file_path=self.cleaned_data["cropped_image"],
                    document_name="profile photo".title(),
                    document_type="profile photo".title(),
                    document_context="general"
                )

                user.phones.create(
                    phone_number=self.cleaned_data["phone_number"]
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

                if self.cleaned_data["aadhar_card"]:
                    user.documents.create(
                        file_path=self.cleaned_data["aadhar_card"],
                        document_name="aadhar card".title(),
                        document_type="id card".title(),
                        document_context="student_admission"
                    )
                
                if self.cleaned_data["birth_certificate"]:
                    user.documents.create(
                        file_path=self.cleaned_data["birth_certificate"],
                        document_name="birth certificate".title(),
                        document_type="certificate".title(),
                        document_context="student_admission"
                    )
                
                if self.cleaned_data["caste_certificate"]:
                    user.documents.create(
                        file_path=self.cleaned_data["caste_certificate"],
                        document_name="caste certificate".title(),
                        document_type="certificate".title(),
                        document_context="student_admission"
                    )
                    
                if self.cleaned_data["mark_sheet"]:
                    user.documents.create(
                        file_path=self.cleaned_data["mark_sheet"],
                        document_name="mark sheet".title(),
                        document_type="mark sheet".title(),
                        document_context="student_admission"
                    )
                
                if self.cleaned_data["transfer_certificate"]:
                    user.documents.create(
                        file_path=self.cleaned_data["transfer_certificate"],
                        document_name="transfer certificate".title(),
                        document_type="certificate".title(),
                        document_context="student_admission"
                    )

                if self.cleaned_data["previous_institution"] and self.cleaned_data["score"] and self.cleaned_data["mm"] and self.cleaned_data["rte"]:
                    percent = (self.cleaned_data["score"] / self.cleaned_data["mm"]) * 100
                    PreviousInstitutionDetail.objects.create(
                        student=student,
                        previous_institution=self.cleaned_data["previous_institution"],
                        score=self.cleaned_data["score"],
                        mm=self.cleaned_data["mm"],
                        percent=percent,
                        rte=self.cleaned_data["rte"]
                    )
                
                return student_admission
        except Exception as e:
            existingUser = User.objects.filter(username=self.cleaned_data["username"]).exists()
            if not existingUser:
                
                if settings.DEBUG:
                    try:
                        delete_files_from_local(f"user_document/{self.cleaned_data['username']}")
                    except Exception as delete_error:
                        # Log deletion error but continue the process
                        logger.error(f"Failed to delete files locally: {delete_error}")
                else:
                    try:
                        delete_files_from_s3(f"user_document/{self.cleaned_data['username']}")
                    except Exception as delete_error:
                        # Log deletion error but continue the process
                        logger.error(f"Failed to delete files from S3: {delete_error}")
                # Re-raise the original error to propagate further
                raise e
            






class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['name', 'start_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'})
        }


class FeeTypeForm(forms.ModelForm):
    class Meta:
        model = FeeType
        fields = ['name', 'amount']




