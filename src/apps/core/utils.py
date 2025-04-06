import boto3
import os
import shutil
from django.conf import settings
from django.core.files.storage import default_storage
from apps.students.models import FeeDue, Student, StudentAdmission
from datetime import date
from django.utils.timezone import now
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging
from django.core.files.storage import S3SignedUrlStorage

logger = logging.getLogger(__name__)

def delete_document(document):
    """
    Delete a document and its associated file from storage.
    Args:
        document: A UserDocument instance to delete
    """
    try:
        file_path = document.file_path.name
        if settings.USE_S3_STORAGE:
            # Use the configured S3 storage backend
            storage = S3SignedUrlStorage()
            # Construct the full S3 path including AWS_LOCATION
            s3_path = os.path.join(settings.AWS_LOCATION, file_path) if settings.AWS_LOCATION else file_path
            storage.delete(s3_path)
            logger.info(f"Successfully deleted S3 file: {s3_path}")
        else:
            # Local storage deletion
            absolute_path = os.path.join(settings.MEDIA_ROOT, file_path)
            if os.path.exists(absolute_path):
                os.remove(absolute_path)
                logger.info(f"Successfully deleted local file: {absolute_path}")
            else:
                logger.warning(f"Local file does not exist: {absolute_path}")
    except Exception as e:
        logger.error(f"Error deleting document file {file_path}: {str(e)}")
        raise

def delete_files_from_local(file_path):
    """
    Delete a file from local storage.
    Args:
        file_path: The path of the file to delete (relative to MEDIA_ROOT)
    """
    try:
        # Get the absolute path
        absolute_path = os.path.join(settings.MEDIA_ROOT, file_path)
        
        # Check if it's a file or directory
        if os.path.isfile(absolute_path):
            # Delete the file
            os.remove(absolute_path)
            logger.info(f"Successfully deleted file: {absolute_path}")
        elif os.path.isdir(absolute_path):
            # Delete the directory and its contents
            shutil.rmtree(absolute_path)
            logger.info(f"Successfully deleted directory: {absolute_path}")
        else:
            logger.warning(f"Path does not exist: {absolute_path}")
    except Exception as e:
        logger.error(f"Error deleting file/directory {file_path}: {str(e)}")
        raise

def fee_due_generate(student):
    """Generates fee dues for a student's latest active admission."""
    today = timezone.localtime(timezone.now()).date()
    # get the current session
    current_session = StudentAdmission.generate_session()
    active_admission = student.admissions.filter(status="active" , session=current_session).order_by("-admission_date").first()
    is_rte = active_admission.is_rte

    if not active_admission:
        return False  # No active admission found, skip processing

    fee_structure = active_admission.fee_structure
    fee_types = fee_structure.fee_types.all()

    for fee_type in fee_types:
        # Check if a due already exists to avoid duplication
        if not FeeDue.objects.filter(admission=active_admission, fee_type=fee_type).exists():
            
            # Handle tuition fees based on the date conditions
            if fee_type.name in ["tuition_q1", "tuition_q2", "tuition_q3", "tuition_q4"] and is_rte == False:
                if (fee_type.name == "tuition_q1" and today >= date(today.year, 4, 1)) or \
                   (fee_type.name == "tuition_q2" and today >= date(today.year, 7, 1)) or \
                   (fee_type.name == "tuition_q3" and today >= date(today.year, 10, 1)) or \
                   (fee_type.name == "tuition_q4" and today >= date(today.year, 1, 1)):
                    FeeDue.objects.create(admission=active_admission, fee_type=fee_type, amount=fee_type.amount)

            else:
                # Add all other fee types immediately
                FeeDue.objects.create(admission=active_admission, fee_type=fee_type, amount=fee_type.amount)

    return True


def fee_due_generate_all():
    """Generates fee dues for all students with an active admission."""
    students = Student.objects.filter(admissions__status="active").distinct()
    for student in students:
        fee_due_generate(student)
    return True




def pay_fee_dues(student, transaction, budget):
    """Pays student's fee dues from the oldest to the newest within the given budget.
    
    Args:
        student (Student): The student whose fees are being paid.
        transaction (PaymentTransaction): The transaction associated with this payment.
        budget (Decimal): The available amount to pay dues.

    Returns:
        Decimal: The remaining budget that couldn't be used.
    """

    # Fetch all unpaid dues for all admissions of the student, ordered from oldest to newest
    dues = FeeDue.objects.filter(admission__student=student, paid=False).order_by("admission__admission_date", "id")

    for due in dues:
        if budget >= due.amount:
            # Pay the fee due and subtract from the budget
            due.mark_as_paid(transaction)
            budget -= due.amount
        else:
            # If budget is not enough for this due, stop processing
            break

    return budget  # Return the remaining amount that couldn't be used


def pay_family_fee_dues(family, transaction):
    """
    Pays fee dues for all active students in a family within the given budget.

    Args:
        family (Family): The family whose students' fees are being paid.
        transaction (PaymentTransaction): The transaction associated with this payment.

    Returns:
        tuple: (remaining_budget, payment_data)
    """
    budget = family.wallet_balance
    family_members = family.members.all()  # Get all users in the family
    family_members_users = family_members.values_list('user', flat=True)

    students = Student.objects.filter(user__in=family_members_users, admissions__status="active").distinct()

    payment_data = {"students": {}}  # Store payment details here
    dues_found = False  # Flag to check if any dues exist

    for student in students:
        student_fees = {}  # Fees paid for this student
        dues = FeeDue.objects.filter(admission__student=student, paid=False).order_by("admission__admission_date", "id")

        if not dues.exists():  # Check if there are no dues for this student
            continue  # Skip to the next student

        dues_found = True  # Dues exist for at least one student

        for due in dues:
            if budget >= due.amount:
                due.mark_as_paid(transaction)
                budget -= due.amount
                student_fees[due.fee_type.name] = float(due.amount)  # Convert to float for JSON compatibility
            else:
                # Budget is insufficient for this fee, skip it
                continue

        if student_fees:
            payment_data["students"][f"{student.user.first_name} {student.user.last_name}"] = {"fees": student_fees}
        else:
            raise ValidationError("Insufficient budget.")

    # Raise an error if no dues were found for any student
    if not dues_found:
        raise ValidationError("No fee dues found for any student in the family.")

    remaining_budget = budget  # Ensure compatibility with JSON

    return remaining_budget, payment_data