from django.urls import path
from .views import HomeView, SignupView, LoginView, LogoutView, FamilyListView, FamilyCreateView, AddFamilyMemberView, UserProfileView, UserProfileUpdateView, UserProfilePhotoUpdateView, WalletTopupView, UserDocumentUploadView, UserDocumentDeleteView, FamilyDiscountView, generate_fee_due_view, GenerateAllFeeDuesView


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('user/signup/', SignupView.as_view(), name='signup'),
    path('user/login/', LoginView.as_view(), name='login'),
    path('user/logout/', LogoutView.as_view(), name='logout'),
    path('user/profile/<str:username>/', UserProfileView.as_view(), name='user_profile'),
    path('user/profile/update/<str:username>/', UserProfileUpdateView.as_view(), name='user_profile_update'),
    path('user/profile/photo/update/<str:username>/', UserProfilePhotoUpdateView.as_view(), name='user_profile_photo_update'),
    path('user/profile/document/upload/<str:username>/', UserDocumentUploadView.as_view(), name='user_document_upload'),
    path('user/profile/document/delete/<uuid:document_id>/', UserDocumentDeleteView.as_view(), name='user_document_delete'),
    path('families/', FamilyListView.as_view(), name='family_list'),
    path('families/create/', FamilyCreateView.as_view(), name='family_create'),
    path('families/<uuid:family_id>/add_member/', AddFamilyMemberView.as_view(), name='add_family_member'),
    path('families/<uuid:family_id>/wallet_topup/', WalletTopupView.as_view(), name='wallet_topup'),
    path('families/<uuid:family_id>/discount_topup/', FamilyDiscountView.as_view(), name='discount_topup'),
    path('generate_fee_dues/', generate_fee_due_view, name='generate_fee_dues'),
    path('generate_all_fee_dues/', GenerateAllFeeDuesView.as_view(), name='generate_all_fee_dues'),
]
