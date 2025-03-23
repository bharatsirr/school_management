from django.contrib import admin

from apps.core.models import User, Phone

admin.site.register(User)
admin.site.register(Phone)