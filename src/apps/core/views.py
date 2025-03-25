from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views import View
from .forms import UserCreationForm
from django.contrib import messages


class HomeView(View):
    def get(self, request):
        return render(request, 'core/home.html')

class SignupView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'core/signup.html', {'form': form})

    def post(self, request):
        # Pass both POST data and FILES
        form = UserCreationForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Save the user
                user = form.save()
                
                # Log the user in
                login(request, user)
                
                # Add a success message
                messages.success(request, 'Account created successfully!')
                
                # Redirect to home page
                return redirect('home')
            
            except Exception as e:
                # Log the error (you might want to use Django's logging)
                messages.error(request, f'An error occurred: {str(e)}')
                return render(request, 'core/signup.html', {'form': form})
        
        else:
            # If form is not valid, add form-level errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.capitalize()}: {error}')
        
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
    