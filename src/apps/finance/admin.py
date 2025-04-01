from django.contrib import admin

from apps.finance.models import PaymentTransaction, Discount, LedgerEntry, LedgerAccountType, BankAccountDetail, WalletTransaction, ManagementExpense, PaymentSummary


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'date', 'status')
    search_fields = ('user__username', 'amount')
    list_filter = ('status',)





@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('payment_transaction', 'discount_amount', 'discount_by', 'discount_type')
    search_fields = ('payment_transaction__user__username', 'discount_by__username')
    list_filter = ('discount_type',)


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('payment_transaction', 'amount', 'entry_type', 'account_type')
    search_fields = ('payment_transaction__user__username', 'account_type__name')
    list_filter = ('entry_type',)


@admin.register(LedgerAccountType)
class LedgerAccountTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type')
    search_fields = ('name',)
    list_filter = ('account_type',)


@admin.register(BankAccountDetail)
class BankAccountDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_number', 'account_type')
    search_fields = ('user__username', 'account_number')
    list_filter = ('account_type',)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('family', 'current_balance', 'previous_balance', 'transaction_type')
    search_fields = ('family__family_name',)
    list_filter = ('transaction_type',)


@admin.register(ManagementExpense)
class ManagementExpenseAdmin(admin.ModelAdmin):
    list_display = ('spent_by', 'expense_category', 'date')
    search_fields = ('spent_by__username', 'expense_category')
    list_filter = ('expense_category',)


@admin.register(PaymentSummary)
class PaymentSummaryAdmin(admin.ModelAdmin):
    list_display = ('payment_transaction', 'amount', 'date')
    search_fields = ('payment_transaction__user__username',)
    list_filter = ('date',)
