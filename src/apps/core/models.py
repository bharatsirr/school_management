import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings



class UserManager(BaseUserManager):
    def create_user(self, username, first_name, last_name, password, **extra_fields):
        if not username:
            raise ValueError('The Username is required')
        if not first_name:
            raise ValueError('First name is required')
        if not password:
            raise ValueError('Password is required')

        email = extra_fields.pop('email', None)
        phone_number = extra_fields.pop('phone_number', None)
        # No need to check for last_name, it will use default empty string if not provided

        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name or '',  # Use empty string if last_name is None or empty
            email=self.normalize_email(email) if email else None,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)

        # Create phone number if provided
        if phone_number:
            Phone.objects.create(user=user, phone_number=phone_number)

        return user

    def create_superuser(self, username, first_name, last_name, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, first_name, last_name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [
    ('Other', 'Other'),
    ('Male', 'Male'),
    ('Female', 'Female'),
    ]
    BLOOD_GROUPS = [
    ('None', 'None'), ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
    ('O+', 'O+'), ('O-', 'O-'), 
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True, default='')
    father_name = models.CharField(max_length=150, blank=True, default='')
    mother_name = models.CharField(max_length=150, blank=True, default='')
    email = models.EmailField(unique=True, null=True, blank=True)
    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    village = models.CharField(max_length=255, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    dob = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=5, blank=True, choices=BLOOD_GROUPS)
    gender = models.CharField(max_length=10, blank=True, choices=GENDER_CHOICES)
    religion = models.CharField(max_length=255, blank=True)
    caste = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=255, blank=True)
    aadhar_number = models.CharField(max_length=12, null=True, blank=True, unique=True)
    occupation = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name']

    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.caste:
            self.caste = self.caste.upper()

        if self.category:
            self.category = self.category.upper()

        if self.religion:
            self.religion = self.religion.upper()

        if self.occupation:
            self.occupation = self.occupation.upper()

        if self.email:
            self.email = self.email.strip().lower().replace(" ", "")

        if self.email == "":
            self.email = None
        super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}" if self.last_name else f"{self.first_name}"
    
    @property
    def profile_photo(self):
        latest = UserDocument.objects.filter(
            user=self,
            document_name='profile_photo'
        ).order_by('-uploaded_at').first()
        if latest and latest.file_path:
            return latest.file_path.url
        return None
    
    def __str__(self):
        return self.username


class Phone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phones')
    phone_number = models.CharField(max_length=10, unique=True)
    is_whatsapp = models.BooleanField(default=False)

    def __str__(self):
        return self.phone_number
    

def user_document_upload_path(instance, filename):
    # Extract file extension
    ext = filename.split('.')[-1]
    # Generate unique filename
    new_filename = f"user_document/{instance.user.username}/{instance.document_name.replace(' ', '_')}_{uuid.uuid4().hex}.{ext}"
    return new_filename

class UserDocument(models.Model):
    DOCUMENT_CONTEXT_CHOICES = [
        ('student_admission', 'Student Admission'),
        ('staff_certification', 'Staff Certification'),
        ('previous_institution', 'Previous Institution'),
        ('rte', 'Right to Education (RTE)'),
        ('general', 'General'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    file_path = models.FileField(upload_to=user_document_upload_path)
    document_name = models.CharField(max_length=100)  # e.g., Aadhar, PAN Card
    document_number = models.CharField(max_length=100, blank=True, null=True)  # Optional for non-ID docs
    document_type = models.CharField(max_length=50)  # e.g., ID Card, Certificate, Passport, License
    document_context = models.CharField(max_length=50, choices=DOCUMENT_CONTEXT_CHOICES, default='general')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "User Document"
        verbose_name_plural = "User Documents"

    def __str__(self):
        return f"{self.document_name} - {self.user.username}"
    


class Family(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family_name = models.CharField(max_length=255, unique=True)
    wallet_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Family"
        verbose_name_plural = "Families"

    def __str__(self):
        return self.family_name


class FamilyMember(models.Model):
    class MemberType(models.TextChoices):
        CHILD = 'child', 'Child'
        PARENT = 'parent', 'Parent'
        GRANDPARENT = 'grandparent', 'Grandparent'
        OTHER = 'other', 'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='members')
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='family_member')
    member_type = models.CharField(max_length=20, choices=MemberType.choices)
    is_alive = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.member_type}"