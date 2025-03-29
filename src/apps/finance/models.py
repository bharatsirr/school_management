from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class BankAccountDetail(models.Model):
    ACCOUNT_TYPES = [
        ('SAVINGS', 'Savings'),
        ('CURRENT', 'Current'),
        ('SALARY', 'Salary'),
        ('BUSINESS', 'Business'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50, unique=True)
    ifsc = models.CharField(max_length=20, help_text="Indian Financial System Code (IFSC)")
    branch_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_holder_name} - {self.account_number}"
    



class LedgerAccountType(models.Model):
    ACCOUNT_TYPES = [
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
    ]

    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_accounts')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    code = models.CharField(max_length=20, unique=True, help_text="Account identifier (e.g., 1001)")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "Ledger Account Type"
        verbose_name_plural = "Ledger Account Types"



class PaymentTransaction(models.Model):
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('ONLINE', 'Online'),
        ('WALLET', 'Wallet'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
        ('SUCCESSFUL', 'Successful'),
    ]

    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    agent = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_transactions')
    method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"{self.user} - {self.amount} ({self.status})"
    


class LedgerEntry(models.Model):
    ENTRY_TYPES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]

    payment_transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='ledger_entries')
    date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)
    account_type = models.ForeignKey(LedgerAccountType, on_delete=models.CASCADE, related_name='entries')
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.account_type} - {self.amount} ({self.entry_type})"

    class Meta:
        verbose_name = "Ledger Entry"
        verbose_name_plural = "Ledger Entries"



class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ]

    family = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, help_text="Balance after the transaction")
    previous_balance = models.DecimalField(max_digits=12, decimal_places=2, help_text="Balance before the transaction")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    transaction_id = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, unique=True, related_name='wallet_transaction')

    def __str__(self):
        return f"{self.family} - {self.transaction_type} ({self.current_balance})"
    


class Discount(models.Model):
    DISCOUNT_TYPES = [
        ('RTE_DISCOUNT', 'RTE Discount'),
        ('GENERAL_DISCOUNT', 'General Discount'),
    ]

    payment_transaction = models.ForeignKey('PaymentTransaction', on_delete=models.CASCADE, related_name='discounts')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount of discount given")
    discount_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discounts_given')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Ensure only Directors can give discounts
        if not self.discount_by.groups.filter(name='Director').exists():
            raise PermissionError("Only Directors can apply discounts.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.payment_transaction} - {self.discount_amount} ({self.discount_type})"
    



class ManagementExpense(models.Model):
    EXPENSE_CATEGORIES = [
        ('SALARY', 'Salary'),
        ('UTILITY', 'Utility'),
        ('MAINTENANCE', 'Maintenance'),
        ('MISC', 'Miscellaneous'),
        ('SUPPLIES', 'Supplies'),
        ('TRANSPORT', 'Transport'),
    ]

    spent_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    description = models.TextField(help_text="Details of the expense")
    expense_category = models.CharField(max_length=50, choices=EXPENSE_CATEGORIES)
    date = models.DateField(help_text="Date of the expense")
    transaction = models.ForeignKey('PaymentTransaction', on_delete=models.CASCADE, related_name='expenses')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.expense_category} - {self.amount} - {self.date}"
    



class Invoice(models.Model):
    payment_transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, related_name='invoices')
    invoice_date = models.DateField(auto_now_add=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    details = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.customer} - {self.total_amount} - {self.invoice_date}"
    
    
