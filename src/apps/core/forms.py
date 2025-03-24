from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]

BLOOD_GROUPS = [
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
    ('O+', 'O+'), ('O-', 'O-'),
]

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput())
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput())

    phone_number = forms.CharField(max_length=15, required=False)

    blood_group = forms.ChoiceField(choices=BLOOD_GROUPS, required=False)

    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
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
        cleaned_data["email"] = cleaned_data.get("email", "").strip().lower()

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            # Save phone number
            phone_number = self.cleaned_data.get('phone_number')
            if phone_number:
                user.phones.create(phone_number=phone_number)
        return user