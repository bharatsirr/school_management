from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views import View
from .forms import UserCreationForm


class HomeView(View):
    def get(self, request):
        return render(request, 'core/home.html')

class SignupView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'core/signup.html', {'form': form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        return render(request, 'core/signup.html', {'form': form})
    

class LoginView(View):
    def get(self, request):
        return render(request, 'core/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        return render(request, 'core/login.html', {'error': 'Invalid credentials'})
    

class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('login')
    