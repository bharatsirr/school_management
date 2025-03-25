from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.views.generic import CreateView, ListView
from django.views import View
from django.urls import reverse_lazy
from .forms import UserCreationForm, FamilyForm, FamilyMemberForm
from django.contrib import messages
from .models import Family


User = get_user_model()
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
        
        return render(request, 'registration/signup.html', {'form': form})
    

class LoginView(View):
    def get(self, request):
        return render(request, 'registration/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        return render(request, 'registration/login.html', {'error': 'Invalid credentials'})
    

class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('login')



class FamilyCreateView(LoginRequiredMixin, CreateView):
    model = Family
    form_class = FamilyForm
    template_name = 'core/family_form.html'
    success_url = reverse_lazy('family-list')


# List Families and Members View
class FamilyListView( LoginRequiredMixin, ListView):
    model = Family
    template_name = 'core/family_list.html'
    context_object_name = 'families'


# Add Member to Family View
class AddFamilyMemberView( LoginRequiredMixin, View):
    template_name = 'core/add_family_member.html'

    def get(self, request, family_id):
        family = get_object_or_404(Family, id=family_id)
        form = FamilyMemberForm(family=family)
        return render(request, self.template_name, {'form': form, 'family': family})

    def post(self, request, family_id):
        family = get_object_or_404(Family, id=family_id)
        form = FamilyMemberForm(request.POST, family=family)

        if form.is_valid():
            family_member = form.save(commit=False)
            family_member.family = family
            family_member.save()
            return redirect('family-list')

        return render(request, self.template_name, {'form': form, 'family': family})