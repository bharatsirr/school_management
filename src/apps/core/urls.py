from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import HomeView, SignupView, LoginView, LogoutView, FamilyListView, FamilyCreateView, AddFamilyMemberView


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('user/signup/', SignupView.as_view(), name='signup'),
    path('user/login/', LoginView.as_view(), name='login'),
    path('user/logout/', LogoutView.as_view(), name='logout'),

    path('families/', FamilyListView.as_view(), name='family-list'),
    path('families/create/', FamilyCreateView.as_view(), name='family-create'),
    path('families/<int:family_id>/add-member/', AddFamilyMemberView.as_view(), name='add-family-member'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)