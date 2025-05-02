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
from apps.core.s3_signed_storage import S3SignedUrlStorage

logger = logging.getLogger(__name__)


from django.utils import timezone

def fee_due_generate(student):
    """Generates fee dues for a student's latest active admission."""
    today = timezone.localtime(timezone.now()).date()
    current_session = StudentAdmission.generate_session()
    previous_session = StudentAdmission.generate_session(today.year - 1)

    active_admission = student.admissions.filter(
        status="active", session=current_session
    ).order_by("-admission_date").first()

    if not active_admission:
        return False

    is_rte = active_admission.is_rte
    fee_structure = active_admission.fee_structure
    fee_types = fee_structure.fee_types.all()

    # Determine current academic quarter
    month = today.month
    if 4 <= month <= 6:
        current_quarter = 1
    elif 7 <= month <= 9:
        current_quarter = 2
    elif 10 <= month <= 12:
        current_quarter = 3
    else:  # January to March
        current_quarter = 4

    for fee_type in fee_types:
        if FeeDue.objects.filter(admission=active_admission, fee_type=fee_type).exists():
            continue

        fee_name = fee_type.name.lower()
        is_quarterly_fee = False
        quarter_num = None

        for q in range(1, 5):
            if f"_q{q}" in fee_name:
                is_quarterly_fee = True
                quarter_num = q
                break

        if is_quarterly_fee:
            if is_rte and fee_name.startswith("tuition"):
                continue  # Skip tuition fees for RTE students
            if quarter_num <= current_quarter:
                FeeDue.objects.create(
                    admission=active_admission, fee_type=fee_type, amount=fee_type.amount
                )
            # else: skip future quarter
        else:
            if is_rte and fee_name.startswith("tuition"):
                continue  # Skip tuition for RTE
            if student.admissions.filter(session=previous_session).exists() and fee_name == "registration" and active_admission.student_class not in ["10", "12"]:
                continue
            FeeDue.objects.create(
                admission=active_admission, fee_type=fee_type, amount=fee_type.amount
            )

    return True


def fee_due_generate_all():
    """Generates fee dues for all students with an active admission."""
    students = Student.objects.filter(admissions__status="active").distinct()
    for student in students:
        fee_due_generate(student)
    return True




def pay_fee_dues(student, transaction, budget, dues=None):
    """Pays student's fee dues from the oldest to the newest within the given budget.
    
    Args:
        student (Student): The student whose fees are being paid.
        transaction (PaymentTransaction): The transaction associated with this payment.
        budget (Decimal): The available amount to pay dues.

    Returns:
        Decimal: The remaining budget that couldn't be used.
    """

    # Fetch all unpaid dues for all admissions of the student, ordered from oldest to newest
    if dues is None:
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


def pay_family_fee_dues(family, transaction, selected_due_ids=None):
    """
    Pays fee dues for selected or all active students in a family within the given budget.

    Args:
        family (Family): The family whose students' fees are being paid.
        transaction (PaymentTransaction): The transaction associated with this payment.
        selected_due_ids (list, optional): List of FeeDue IDs to pay. If None, pays all.

    Returns:
        tuple: (remaining_budget, payment_data)
    """
    budget = family.wallet_balance
    family_members = family.members.all()
    family_members_users = family_members.values_list('user', flat=True)
    students = Student.objects.filter(user__in=family_members_users, admissions__status="active").distinct()

    payment_data = {"students": {}}
    dues_found = False

    for student in students:
        student_fees = {}

        all_dues = FeeDue.objects.filter(admission__student=student, paid=False)
        if selected_due_ids is not None:
            dues = all_dues.filter(id__in=selected_due_ids).order_by("admission__admission_date", "id")
        else:
            dues = all_dues.order_by("admission__admission_date", "id")

        if not dues.exists():
            continue

        dues_found = True

        for due in dues:
            if budget >= due.amount:
                due.mark_as_paid(transaction)
                budget -= due.amount
                key = f'{due.fee_type.name}({due.admission.student_class} {due.admission.section} - {due.admission.session})'
                student_fees[key] = float(due.amount)
            else:
                continue

        if student_fees:
            key = f"{student.user.first_name} {student.user.last_name} - {student.admissions.order_by('-admission_date').first().student_class} {student.admissions.order_by('-admission_date').first().section} - {student.admissions.order_by('-admission_date').first().session}"
            payment_data["students"][key] = {"fees": student_fees}
        elif selected_due_ids:
            raise ValidationError("Insufficient budget for selected dues.")

    if not dues_found:
        raise ValidationError("No fee dues found for selected dues.")

    return budget, payment_data