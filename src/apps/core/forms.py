import logging
from django.db import transaction
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from PIL import Image
import uuid

from apps.core.models import Family, FamilyMember, UserDocument
from apps.finance.models import PaymentTransaction, WalletTransaction, Discount, ManagementExpense, PaymentSummary, LedgerEntry, LedgerAccountType

logger = logging.getLogger(__name__)

User = get_user_model()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'dob', 'gender', 'village', 'pincode', 'aadhar_number', 'religion', 'caste', 'category', 'occupation']


class UserDocumentForm(forms.ModelForm):
    class Meta:
        model = UserDocument
        fields = ['file_path', 'document_name', 'document_number', 'document_type', 'document_context']

    def save(self, user=None, commit=True):
        instance = super().save(commit=False)
        if user:
            instance.user = user
        if commit:
            instance.save()
        return instance


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

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'password1', 'password2', 'father_name', 'mother_name',
            'village', 'pincode', 'dob', 'blood_group', 'aadhar_number', 'gender', 'religion', 'caste', 'category', 'occupation'
        ]

    username = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        
        if password1 and password1 != password2:
            raise ValidationError("Passwords do not match!")

        # Normalize text fields (lowercase consistency)
        cleaned_data["username"] = cleaned_data.get("username", "").strip().lower().replace(" ", "")
        cleaned_data["first_name"] = cleaned_data.get("first_name", "").strip().title()
        
        # Handle optional fields - use empty string if None or empty
        optional_fields = ["last_name", "father_name", "mother_name", "village"]
        for field in optional_fields:
            value = cleaned_data.get(field, "")
            cleaned_data[field] = value.strip().title() if value else ""
            
        # Handle email separately since it needs to be lowercase
        email = cleaned_data.get("email", "")
        cleaned_data["email"] = email.strip().lower() if email else None

        # Handle Aadhar number - ensure it's None if empty
        aadhar = cleaned_data.get("aadhar_number", "")
        if aadhar:
            if not aadhar.isdigit() or len(aadhar) != 12:
                raise ValidationError({"aadhar_number": "Enter a valid 12-digit Aadhar number."})
        else:
            cleaned_data["aadhar_number"] = None

        # Handle phone number validation
        phone = cleaned_data.get("phone_number", "")
        if phone:
            if not phone.isdigit() or len(phone) != 10:
                raise ValidationError({"phone_number": "Enter a valid 10-digit phone number."})
            
        # Generate username if not provided
        if not cleaned_data.get("username"):
            first_name = cleaned_data.get("first_name", "").lower().replace(" ", "")
            last_name = cleaned_data.get("last_name", "").lower().replace(" ", "")
            dob = cleaned_data.get("dob")
            
            # Create username from first_name, last_name, dob (YYYYMMDD)
            if dob and first_name and last_name:
                cleaned_data["username"] = f'{first_name}{last_name}{dob.strftime("%Y%m%d")}'.replace(" ", "")
            elif first_name and dob:
                cleaned_data["username"] = f'{first_name}{dob.strftime("%Y%m%d")}'.replace(" ", "")

        # Check if the username already exists in the database
        if User.objects.filter(username=cleaned_data["username"]).exists():
            raise ValidationError({"username": "This username is already taken."})

        return cleaned_data
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("This email is already in use.")
        return email


    def save(self, commit=True):
        try:
            with transaction.atomic():
                user = super().save(commit=False)
                user.set_password(self.cleaned_data["password1"])

                if not user.username:
                    user.username = self.cleaned_data["username"].lower().replace(" ", "")
                
                if commit:
                    user.save()
                    
                    # Save phone number
                    phone_number = self.cleaned_data.get('phone_number')
                    if phone_number:
                        # Assuming there's a related PhoneNumber model
                        # You might need to adjust this based on your exact model
                        user.phones.create(phone_number=phone_number)
                    
            return user
        except Exception as e:
             raise e




class UserProfilePhotoForm(forms.Form):
    cropped_image = forms.FileField(required=True)

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
    
    

    

class FamilyForm(forms.Form):
    father_first_name = forms.CharField(max_length=100)
    mother_first_name = forms.CharField(max_length=100)
    title = forms.CharField(max_length=100)
    village = forms.CharField(max_length=100)

    def clean(self):
        cleaned_data = super().clean()

        for field in ["father_first_name", "mother_first_name", "title", "village"]:
            cleaned_data[field] = cleaned_data.get(field, "").strip().lower()

        if not cleaned_data.get("father_first_name") or not cleaned_data.get("mother_first_name"):
            raise forms.ValidationError("Both father's and mother's first names are required.")

        if not cleaned_data.get("title") or not cleaned_data.get("village"):
            raise forms.ValidationError("Title and village are required.")

        if cleaned_data["father_first_name"] == cleaned_data["mother_first_name"]:
            raise forms.ValidationError("Father's and mother's first names cannot be the same.")

        if cleaned_data["title"] == cleaned_data["village"]:
            raise forms.ValidationError("Title and village cannot be the same.")

        family_name = f"{cleaned_data['father_first_name']}_{cleaned_data['mother_first_name']}_{cleaned_data['title']}_{cleaned_data['village']}_{uuid.uuid4().hex[:8]}"
        cleaned_data["family_name"] = family_name.replace(" ", "_")

        return cleaned_data

    def save(self):
        # Save the Family instance, but the user will not be part of the model
        family = Family.objects.create(
            family_name=self.cleaned_data["family_name"].replace(" ", "_")
        )
        return family





class FamilyMemberForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        family = kwargs.pop('family', None)
        super().__init__(*args, **kwargs)

        # If the family is provided, exclude users who are already in any family (including the current one)
        if family:
            # Get all user IDs from FamilyMember where the user is part of any family, excluding the current family
            excluded_users = FamilyMember.objects.values_list('user', flat=True)
        else:
            excluded_users = []

        # Set queryset to exclude all the users already in any family
        self.fields['user'].queryset = User.objects.exclude(id__in=excluded_users).order_by('-created_at')

    class Meta:
        model = FamilyMember
        fields = ['user', 'member_type', 'is_alive']
        widgets = {
            'member_type': forms.Select(choices=FamilyMember.MemberType.choices),
        }



class WalletTopupForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0.")
        return amount

    def save(self, family):
        if not family:
            raise ValueError("A valid family instance is required.")

        try:
            with transaction.atomic():
                # get the old balance
                old_balance = family.wallet_balance
                # update the balance
                family.wallet_balance += self.cleaned_data['amount']
                family.save()

                # Try to get a male member first
                family_parent = family.members.filter(member_type=FamilyMember.MemberType.PARENT, user__gender='Male').first()

                # If no male member exists, get the first female member
                if not family_parent:
                    family_parent = family.members.filter(member_type=FamilyMember.MemberType.PARENT, user__gender='Female').first()

                if not family_parent:
                    raise ValueError("No family user found.")
                

                family_user = family_parent.user
                # Now family_user will be either the first male or female member

                # Create a transaction record
                payment_transaction = PaymentTransaction.objects.create(
                    amount=self.cleaned_data['amount'],
                    user=family_user,
                    agent=self.user,
                    method='CASH',
                    status='SUCCESSFUL',
                    description=f"Wallet top-up of ₹{self.cleaned_data['amount']}"
                )
                # Create a wallet transaction record
                WalletTransaction.objects.create(
                    family=family,
                    current_balance=family.wallet_balance,
                    previous_balance=old_balance,
                    transaction_type='CREDIT',
                    payment_transaction=payment_transaction
                )

                # Create a payment summary record
                PaymentSummary.objects.create(
                    payment_transaction=payment_transaction,
                    customer=family_user,
                    amount=self.cleaned_data['amount'],
                    details={'type': 'wallet_top_up', 'old_balance': float(old_balance), 'new_balance': float(family.wallet_balance)}
                )

                # create a ledger entry
                LedgerEntry.objects.create(
                    payment_transaction=payment_transaction,
                    amount=self.cleaned_data['amount'],
                    entry_type='DEBIT',
                    account_type=LedgerAccountType.objects.get(name='CASH'),
                    description=f"Wallet top-up of ₹{self.cleaned_data['amount']}"
                )
                LedgerEntry.objects.create(
                    payment_transaction=payment_transaction,
                    amount=self.cleaned_data['amount'],
                    entry_type='CREDIT',
                    account_type=LedgerAccountType.objects.get(name='WALLET'),
                    description=f"Wallet top-up of ₹{self.cleaned_data['amount']}"
                )
                
        except Exception as e:
            logger.error(f"Failed to save wallet top-up: {e}")
            raise forms.ValidationError(f"Failed to save wallet top-up. {e}")
        




class FamilyDiscountForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0.")
        return amount

    def save(self, family):
        if not family:
            raise ValueError("A valid family instance is required.")

        try:
            with transaction.atomic():
                # get the old balance
                old_balance = family.wallet_balance
                # update the balance
                family.wallet_balance += self.cleaned_data['amount']
                family.save()

                # Try to get a male member first
                family_parent = family.members.filter(member_type=FamilyMember.MemberType.PARENT, user__gender='Male').first()

                # If no male member exists, get the first female member
                if not family_parent:
                    family_parent = family.members.filter(member_type=FamilyMember.MemberType.PARENT, user__gender='Female').first()

                if not family_parent:
                    raise ValueError("No family Parent found.")
                

                family_user = family_parent.user
                # Now family_user will be either the first male or female member

                # Create a transaction record
                payment_transaction = PaymentTransaction.objects.create(
                    amount=self.cleaned_data['amount'],
                    user=family_user,
                    agent=self.user,
                    method='CASH',
                    status='SUCCESSFUL',
                    description=f"Discount top-up of ₹{self.cleaned_data['amount']} for {family.family_name}"
                )
                # Create a wallet transaction record
                WalletTransaction.objects.create(
                    family=family,
                    current_balance=family.wallet_balance,
                    previous_balance=old_balance,
                    transaction_type='CREDIT',
                    payment_transaction=payment_transaction
                )

                Discount.objects.create(
                    payment_transaction=payment_transaction,
                    discount_amount=self.cleaned_data['amount'],
                    discount_by=self.user,
                    discount_type='GENERAL_DISCOUNT'
                )

                # Create a payment summary record
                PaymentSummary.objects.create(
                    payment_transaction=payment_transaction,
                    customer=family_user,
                    amount=self.cleaned_data['amount'],
                    details={'type': 'discount_top_up_for_family', 'old_balance': float(old_balance), 'new_balance': float(family.wallet_balance)}
                )

                # create a ledger entry
                LedgerEntry.objects.create(
                    payment_transaction=payment_transaction,
                    amount=self.cleaned_data['amount'],
                    entry_type='DEBIT',
                    account_type=LedgerAccountType.objects.get(name='DISCOUNT'),
                    description=f"Discount top-up of ₹{self.cleaned_data['amount']} for {family.family_name}"
                )
                LedgerEntry.objects.create(
                    payment_transaction=payment_transaction,
                    amount=self.cleaned_data['amount'],
                    entry_type='CREDIT',
                    account_type=LedgerAccountType.objects.get(name='CASH'),
                    description=f"Discount top-up of ₹{self.cleaned_data['amount']} for {family.family_name}"
                )
                
        except Exception as e:
            logger.error(f"Failed to save discount top-up: {e}")
            raise forms.ValidationError(f"Failed to save discount top-up. {e}")
