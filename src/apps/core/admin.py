from django.contrib import admin

from apps.core.models import User, Phone, UserDocument, Family, FamilyMember

admin.site.register(User)
admin.site.register(Phone)
admin.site.register(UserDocument)


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('family_name', 'wallet_balance')
    search_fields = ('family_name',)


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'family', 'member_type', 'is_alive')
    list_filter = ('member_type', 'is_alive')
    search_fields = ('user__username', 'family__family_name')