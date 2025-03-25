from django.urls import path
from .views import StudentCreateView, StudentAdmissionCreateView

urlpatterns = [
    path('create-student/', StudentCreateView.as_view(), name='create-student'),
    path('student-admission/', StudentAdmissionCreateView.as_view(), name='student-admission'),
]