from django.urls import path
from .views import StudentCreateView, StudentAdmissionCreateView, StudentRegistrationView

urlpatterns = [
    path('create-student/', StudentCreateView.as_view(), name='create-student'),
    path('student-admission/', StudentAdmissionCreateView.as_view(), name='student-admission'),
    path('register-student/', StudentRegistrationView.as_view(), name='register-student'),
]