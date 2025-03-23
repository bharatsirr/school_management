from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from apps.core.models import Phone

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = None

        if '@' in username:
            user = User.objects.filter(email=username).first()
        elif username.isdigit():
            phone = Phone.objects.filter(phone_number=username).select_related('user').first()
            user = phone.user if phone else None
        else:
            user = User.objects.filter(username=username).first()

        if user and user.check_password(password):
            return user
        return None