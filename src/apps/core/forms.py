import logging
from django.db import transaction
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from PIL import Image
from apps.core.utils import delete_files_from_local, delete_files_from_s3
from django.conf import settings

from apps.core.models import Family, FamilyMember

logger = logging.getLogger(__name__)

User = get_user_model()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'dob', 'gender', 'village', 'pincode']


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password", 
        widget=forms.PasswordInput(),
        validators=[
            RegexValidator(
                regex=r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$',
                message='Password must be at least 8 characters long, contain a letter, a number, and a special character'
            )
        ]
    )
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput())
    cropped_image = forms.FileField(required=True)
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

    blood_group = forms.ChoiceField(choices=User.BLOOD_GROUPS, required=False)

    gender = forms.ChoiceField(choices=User.GENDER_CHOICES, required=False)
    dob = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="Format: dd/mm/yyyy"
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'password1', 'password2', 'father_name', 'mother_name',
            'village', 'pincode', 'dob', 'blood_group', 'gender'
        ]

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        
        if password1 and password1 != password2:
            raise ValidationError("Passwords do not match!")

        # Normalize text fields (lowercase consistency)
        cleaned_data["username"] = cleaned_data.get("username", "").strip().lower()
        cleaned_data["first_name"] = cleaned_data.get("first_name", "").strip().title()
        cleaned_data["last_name"] = cleaned_data.get("last_name", "").strip().title()
        cleaned_data["father_name"] = cleaned_data.get("father_name", "").strip().title()
        cleaned_data["mother_name"] = cleaned_data.get("mother_name", "").strip().title()
        cleaned_data["village"] = cleaned_data.get("village", "").strip().title()
        cleaned_data["email"] = cleaned_data.get("email", "").strip().lower()

        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists
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

            # Optional: Validate image dimensions
            try:
                with Image.open(image) as img:
                    width, height = img.size
                    if width < 300 or height < 400:
                        raise forms.ValidationError("Image must be at least 300x400 pixels.")
            except Exception:
                raise forms.ValidationError("Invalid image file.")
            
            self.cleaned_data["cropped_image"] = image
            return self.cleaned_data["cropped_image"]
        raise forms.ValidationError("Profile image is required.")

    def save(self, commit=True):
        try:
            with transaction.atomic():
                user = super().save(commit=False)
                user.set_password(self.cleaned_data["password1"])
                
                if commit:
                    user.save()
                    
                    # Save phone number
                    phone_number = self.cleaned_data.get('phone_number')
                    if phone_number:
                        # Assuming there's a related PhoneNumber model
                        # You might need to adjust this based on your exact model
                        user.phones.create(phone_number=phone_number)
                    
                    # Save profile photo
                    profile_photo = self.cleaned_data.get('cropped_image')
                    if profile_photo:
                        # Assuming you have a Documents model for storing files
                        # Adjust the creation method to match your exact model
                        user.documents.create(
                            file_path=profile_photo,
                            document_name='profile_photo',
                            document_type='profile_photo',
                            document_context='general',
                        )
            
            return user
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


class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ['family_name']


class FamilyMemberForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)

        existing_users = family.members.values_list('user', flat=True) if family else []
        self.fields['user'].queryset = User.objects.exclude(id__in=existing_users).order_by('-created_at')
    class Meta:
        model = FamilyMember
        fields = ['user','member_type', 'is_alive']
        widgets = {
            'member_type': forms.Select(choices=FamilyMember.MemberType.choices),
        }