from django.contrib import admin

from apps.core.models import User, Phone, UserDocument, Family, FamilyMember

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'aadhar_number', 'is_staff', 'is_superuser', 'religion', 'caste', 'category', 'created_at', 'last_login')
    search_fields = ('username', 'email', 'aadhar_number', 'religion', 'caste', 'category')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'religion', 'caste', 'category')

@admin.register(Phone)
class PhoneAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'is_whatsapp')
    search_fields = ('user__username', 'phone_number')

@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'created_at')
    search_fields = ('user__username', 'document_type')


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('family_name', 'wallet_balance')
    search_fields = ('family_name',)


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'family', 'member_type', 'is_alive')
    list_filter = ('member_type', 'is_alive')
    search_fields = ('user__username', 'family__family_name')