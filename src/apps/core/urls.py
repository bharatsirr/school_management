from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import HomeView, SignupView, LoginView, LogoutView, FamilyListView, FamilyCreateView, AddFamilyMemberView, UserProfileView, UserProfileUpdateView, UserProfilePhotoUpdateView, WalletTopupView


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('user/signup/', SignupView.as_view(), name='signup'),
    path('user/login/', LoginView.as_view(), name='login'),
    path('user/logout/', LogoutView.as_view(), name='logout'),
    path('user/profile/', UserProfileView.as_view(), name='user_profile'),
    path('user/profile/update/<str:username>/', UserProfileUpdateView.as_view(), name='user_profile_update'),
    path('user/profile/photo/update/<str:username>/', UserProfilePhotoUpdateView.as_view(), name='user_profile_photo_update'),
    path('families/', FamilyListView.as_view(), name='family_list'),
    path('families/create/', FamilyCreateView.as_view(), name='family_create'),
    path('families/<int:family_id>/add_member/', AddFamilyMemberView.as_view(), name='add_family_member'),
    path('families/<int:family_id>/wallet_topup/', WalletTopupView.as_view(), name='wallet_topup'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)