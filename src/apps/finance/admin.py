from django.contrib import admin

from apps.finance.models import PaymentTransaction, Discount, LedgerEntry, LedgerAccountType, BankAccountDetail, WalletTransaction, ManagementExpense, PaymentSummary


admin.site.register(PaymentTransaction)
admin.site.register(Discount)
admin.site.register(LedgerEntry)
admin.site.register(LedgerAccountType)
admin.site.register(BankAccountDetail)
admin.site.register(WalletTransaction)
admin.site.register(ManagementExpense)
admin.site.register(PaymentSummary)