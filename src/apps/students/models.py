from django.db import transaction
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Max
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


User = get_user_model()


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student', unique=True)
    height = models.FloatField(help_text="Height in cm", blank=True, null=True)
    weight = models.FloatField(help_text="Weight in kg", blank=True, null=True)
    apaar_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    pen_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    def save(self, *args, **kwargs):
        if self.apaar_id == "":
            self.apaar_id = None
        if self.pen_number == "":
            self.pen_number = None
        super().save(*args, **kwargs)
    



class PreviousInstitutionDetail(models.Model):
    student = models.OneToOneField('Student', on_delete=models.CASCADE, related_name='previous_institution')
    previous_institution = models.CharField(max_length=255, help_text="Name of the last attended institution")
    score = models.DecimalField(max_digits=7, decimal_places=2, help_text="Obtained marks")
    mm = models.DecimalField(max_digits=7, decimal_places=2, help_text="Maximum marks")
    percent = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Percentage (auto-calculated)")
    rte = models.BooleanField(default=False, help_text="Was the student a Right to Education (RTE) beneficiary in the previous institution ?")

    def __str__(self):
        return f"{self.student.user.first_name} {self.student.user.last_name} - {self.previous_institution}"
    
    def calculate_percent(self):
        """Auto-calculate percentage."""
        if self.mm > 0:
            return (self.score / self.mm) * 100
        return 0

    def save(self, *args, **kwargs):
        # Auto-calculate percentage before saving
        self.percent = self.calculate_percent()
        super().save(*args, **kwargs)





class ActiveFeeStructureManager(models.Manager):
    """Custom manager to return only active fee structures."""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
    

class FeeStructure(models.Model):
    name = models.CharField(max_length=255, help_text="e.g., class_6_fees")
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(help_text="Fee structure validity start date", default=date.today)
    end_date = models.DateField(help_text="Fee structure validity end date", blank=True, null=True)

    # Custom manager for active fee structures
    objects = models.Manager()  # Default manager
    active_objects = ActiveFeeStructureManager()  # Custom manager

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Fee Structure"
        verbose_name_plural = "Fee Structures"

    def deactivate(self):
        """Deactivate this fee structure."""
        self.is_active = False
        self.save()



class FeeType(models.Model):
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name="fee_types")
    name = models.CharField(max_length=100, help_text="e.g., tuition, exam")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount for this fee type")

    def __str__(self):
        return f"{self.name} - {self.amount}"

    class Meta:
        verbose_name = "Fee Type"
        verbose_name_plural = "Fee Types"



from django.utils import timezone

class FeeDue(models.Model):
    admission = models.ForeignKey('StudentAdmission', on_delete=models.CASCADE, related_name="fee_dues")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Due amount")
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE, related_name="fee_dues")
    transaction = models.ForeignKey('finance.PaymentTransaction', on_delete=models.SET_NULL, null=True, blank=True, related_name="fee_dues")
    paid = models.BooleanField(default=False, help_text="Has this fee been paid?")
    paid_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when fee was paid")

    def __str__(self):
        return f"Due: {self.amount} for {self.fee_type.name}"

    class Meta:
        verbose_name = "Fee Due"
        verbose_name_plural = "Fee Dues"

    def mark_as_paid(self, transaction=None):
        """Mark the fee as paid."""
        self.paid = True
        self.paid_at = timezone.now()
        if transaction:
            self.transaction = transaction
        self.save()


class StudentSerial(models.Model):
    SCHOOL_CHOICES = [
        ('KDIC', 'KDIC'),
        ('KDPV', 'KDPV'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='serials')
    school_name = models.CharField(max_length=10, choices=SCHOOL_CHOICES)
    serial_number = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        # Check if a StudentSerial already exists for this student and school_name
        if StudentSerial.objects.filter(student=self.student, school_name=self.school_name).exists():
            raise ValidationError(f"A serial number already exists for {self.student} at {self.school_name}.")

    def save(self, *args, **kwargs):
        # Ensure validation before saving
        self.full_clean()  # Calls the clean() method
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.user.first_name} {self.student.user.last_name} - {self.school_name} - {self.serial_number}"

    


class StudentAdmission(models.Model):
    
    def generate_session():
        today = datetime.today()  # Get the current date
        year = today.year
        month = today.month
        
        if month >= 4:  # From April to December
            session = f"{year}-{year + 1}"
        else:  # From January to March
            session = f"{year - 1}-{year}"
        
        return session
    
    @staticmethod
    def get_roll_number(student_class, section, session):
        """
        Returns the next roll number for a given class, section, and session.
        """
        last_roll_number = StudentAdmission.objects.filter(
            student_class=student_class,
            section=section,
            session=session
        ).aggregate(Max('roll_number'))

        # If no previous roll numbers, start from 1. Otherwise, increment the last roll number by 1.
        if last_roll_number['roll_number__max']:
            return last_roll_number['roll_number__max'] + 1
        return 1  # Start from 1 if no roll number exists yet.

    SECTION_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('dropped', 'Dropped'),
    ]

    CLASS_CHOICES = [
        ('NUR', 'NUR'),
        ('LKG', 'LKG'),
        ('UKG', 'UKG'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='admissions')
    section = models.CharField(max_length=1, choices=SECTION_CHOICES, default='A')
    serial_no = models.ForeignKey(StudentSerial, on_delete=models.CASCADE, related_name='admissions')
    is_rte = models.BooleanField(default=False)
    admission_date = models.DateTimeField(auto_now_add=True)
    session = models.CharField(max_length=9, help_text="e.g., 2023-2024 leave blank to set to current session", default=generate_session)
    student_class = models.CharField(max_length=20, help_text="Class (e.g., 10, 12, etc.)" , choices=CLASS_CHOICES)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name="student_admissions")
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total fee amount")
    no_dues = models.BooleanField(default=False)
    roll_number = models.PositiveIntegerField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.student.user.first_name} {self.student.user.last_name} - {self.student_class} {self.section}"


        super().save(*args, **kwargs)

    def generate_kdpv_serial(self, student):
        """
        Generate or retrieve the KDPV serial number for students in class below 6.
        """
        year = datetime.now().year
        school_code = 'kdpv'
        
        # Check if the student already has a KDPV serial number for this year
        serial = StudentSerial.objects.filter(
            student=student,
            school_name='KDPV'
        ).order_by('-serial_number').first()  # Get the last created serial for KDPV
        
        if serial:
            return serial.serial_number
        
        # If no serial exists, generate a new one
        last_serial = StudentSerial.objects.filter(
            school_name='KDPV'
        ).order_by('-serial_number').first()
        
        new_serial_number = f"{school_code}00001" if not last_serial else f"{school_code}{int(last_serial.serial_number[-5:]) + 1:05}"

        
        # Create and return the new serial number
        new_serial = StudentSerial.objects.create(
            student=student,
            school_name='KDPV',
            serial_number=new_serial_number
        )
        return new_serial.serial_number

    def generate_kdic_serial(self, student):
        """
        Generate or retrieve the KDIC serial number for students in class 6-12.
        """
        year = datetime.now().year
        school_code = 'kdic'
        
        # Check if the student already has a KDIC serial number for this section
        serial = StudentSerial.objects.filter(
            student=student,
            school_name='KDIC'
        ).order_by('-serial_number').first()  # Get the last created serial for KDIC
        
        if serial:
            return serial.serial_number
        
        # If no serial exists, generate a new one
        last_serial = StudentSerial.objects.filter(
            school_name='KDIC'
        ).order_by('-serial_number').first()
        
        new_serial_number = f"{school_code}00001" if not last_serial else f"{school_code}{int(last_serial.serial_number[-5:]) + 1:05}"

        
        # Create and return the new serial number
        new_serial = StudentSerial.objects.create(
            student=student,
            school_name='KDIC',
            serial_number=new_serial_number
        )
        return new_serial.serial_number

    def save(self, *args, **kwargs):
        try:
            with transaction.atomic():
                # Ensure serial number is created based on the class and student
                if not self.pk:  # Only do this for new records

                    # Auto assign fee structure
                    fee_structure_name = f"class_{self.student_class}_fees".lower()
                    try:
                        self.fee_structure = FeeStructure.active_objects.get(name=fee_structure_name)
                        # Log fee structure
                        logger.debug(f"Fee structure found: {self.fee_structure.name}")
                    except FeeStructure.DoesNotExist:
                        logger.error(f"Fee structure for class {self.student_class} not found.")
                        raise ValueError(f"Fee structure for class {self.student_class} not found.")
                    
                    # Check if fee_types exist for the FeeStructure
                    fee_types = self.fee_structure.fee_types.all()
                    logger.debug(f"Found {fee_types.count()} fee types for {fee_structure_name}")

                    if fee_types.count() == 0:
                        logger.error(f"No FeeTypes found for FeeStructure {self.fee_structure.name}.")
                        raise ValueError(f"No FeeTypes found for FeeStructure {self.fee_structure.name}.")
                    
                    # Calculate the total fee
                    total_fee = fee_types.aggregate(total_fee=Sum('amount'))['total_fee'] or 0
                    if total_fee <= 0:
                        logger.warning(f"Total fee for class {self.student_class} is zero or undefined.")
                    self.total_fee = total_fee
                    if self.student_class in ['NUR', 'LKG', 'UKG', '1', '2', '3', '4', '5']:  # Class below 6
                        serial_number = self.generate_kdpv_serial(self.student)
                        serial = StudentSerial.objects.get_or_create(
                            student=self.student,
                            school_name='KDPV',
                            serial_number=serial_number
                        )[0]  # [0] to get the instance
                        self.serial_no = serial
                    elif self.student_class in ['6', '7', '8', '9', '10', '11', '12']:  # Class 6 and above
                        # deactivate existing kdpv serial
                        existing_kdpv_serial = StudentSerial.objects.filter(
                            student=self.student,
                            school_name='KDPV',
                            is_active=True
                        )
                        # deactivate existing kdpv serial
                        if existing_kdpv_serial:
                            existing_kdpv_serial.is_active = False
                            existing_kdpv_serial.save()

                        # generate new kdic serial
                        serial_number = self.generate_kdic_serial(self.student)
                        serial = StudentSerial.objects.get_or_create(
                            student=self.student,
                            school_name='KDIC',
                            serial_number=serial_number
                        )[0]  # [0] to get the instance
                        self.serial_no = serial
                
                    # Ensure roll number is assigned only for new entries
                    self.roll_number = self.get_roll_number(self.student_class, self.section, self.session)
                super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in saving student admission: {e}")
            raise e
