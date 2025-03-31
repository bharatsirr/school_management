import boto3
import os
import shutil
from django.conf import settings
from django.core.files.storage import default_storage
from apps.students.models import FeeDue, Student, StudentAdmission
from datetime import date
from django.utils.timezone import now
from django.utils import timezone
from decimal import Decimal


def delete_files_from_s3(relative_path):
    # Construct the full path using the relative path provided
    user_documents_prefix = os.path.join(settings.AWS_LOCATION, relative_path)

    # Use Django's default storage to list files with a specific prefix (directory)
    bucket = default_storage.bucket

    # List all files that start with the given prefix (i.e., the relative path)
    blobs = bucket.list_blobs(prefix=user_documents_prefix)

    # Loop through the files and delete them
    for blob in blobs:
        try:
            blob.delete()  # Delete the file from S3
            print(f"Deleted file: {blob.name}")
        except Exception as e:
            print(f"Error deleting file {blob.name}: {e}")

def delete_files_from_local(relative_path):
    # Join the relative path with the MEDIA_ROOT to get the absolute path
    user_documents_dir = os.path.join(settings.MEDIA_ROOT, relative_path)

    # Check if the directory exists
    if os.path.exists(user_documents_dir) and os.path.isdir(user_documents_dir):
        # Delete all files in the directory
        for filename in os.listdir(user_documents_dir):
            file_path = os.path.join(user_documents_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Delete individual file
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Delete sub-directory, if any
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
        
        # After deleting files, remove the directory itself
        os.rmdir(user_documents_dir)
        print(f"Deleted all files and the directory for path: {relative_path}")
    else:
        print(f"Directory does not exist: {relative_path}")


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
    """Pays fee dues for all active students in a family within the given budget.
    
    Args:
        family (Family): The family whose students' fees are being paid.
        transaction (PaymentTransaction): The transaction associated with this payment.

    Returns:
        Decimal: The remaining budget that couldn't be used.
    """
    budget = family.wallet_balance
    family_members = family.members.all()  # Get all users in the family
    students = Student.objects.filter(user__in=family_members, admissions__status="active").distinct()

    for student in students:
        if budget <= Decimal("0.00"):
            break  # Stop if the budget is exhausted

        budget = pay_fee_dues(student, transaction, budget)  # Pay fees for this student

    return budget  # Return leftover money that couldn't be used