from django.urls import path
from .views import FamilyPaymentDatesView, FamilyPaymentDetailsView

urlpatterns = [
    path('family/<uuid:family_id>/payments/', FamilyPaymentDatesView.as_view(), name='family_payment_dates'),
    path('family/<uuid:family_id>/payments/<str:date>/', FamilyPaymentDetailsView.as_view(), name='family_payment_details'),
] 