from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.views.generic import CreateView, ListView, DetailView, UpdateView, FormView
from django.views import View
from django.urls import reverse_lazy
from .forms import UserCreationForm, FamilyForm, FamilyMemberForm, UserProfileForm, UserProfilePhotoForm, WalletTopupForm
from django.contrib import messages
from .models import Family, UserDocument
from django.core.exceptions import PermissionDenied

User = get_user_model()
class HomeView(View):
    def get(self, request):
        return render(request, 'core/home.html')

class SignupView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, 'registration/signup.html', {'form': form})

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
                return render(request, 'registration/signup.html', {'form': form})
        
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
    success_url = reverse_lazy('family_list')


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
            return redirect('family_list')

        return render(request, self.template_name, {'form': form, 'family': family})
    




class WalletTopupView(FormView):
    template_name = "core/wallet_topup.html"  # Create a template for this view
    form_class = WalletTopupForm
    success_url = reverse_lazy("family_list")  # Redirect to a relevant page after top-up

    def get_family(self):
        return get_object_or_404(Family, id=self.kwargs.get("family_id"))
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['family'] = self.get_family()
        return context

    def form_valid(self, form):
        family = self.get_family()
        form.save(family=family)
        messages.success(self.request, "Wallet top-up successful!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid amount entered.")
        return super().form_invalid(form)
    





class UserProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'core/user_profile.html'
    context_object_name = 'user'

    def get_object(self):
        # Get the username from the URL
        username = self.kwargs.get('username')
        
        # Try to get the user by username, raise 404 if not found
        user_to_view = get_object_or_404(User, username=username)
        
        # Check if the logged-in user is the one trying to update their own profile
        # or if they are a manager/company owner
        if user_to_view != self.request.user and not self.request.user.is_staff:
            # Customize this line based on your permissions logic (manager/owner check)
            raise Http404("You are not authorized to view this user's profile.")
        
        return user_to_view


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'core/user_profile_update.html'
    success_url = reverse_lazy('user_profile')

    def get_object(self):
        # Get the username from the URL
        username = self.kwargs.get('username')
        
        # Try to get the user by username, raise 404 if not found
        user_to_edit = get_object_or_404(User, username=username)
        
        # Check if the logged-in user is the one trying to update their own profile
        # or if they are a manager/company owner
        if user_to_edit != self.request.user and not self.request.user.is_staff:
            # Customize this line based on your permissions logic (manager/owner check)
            raise Http404("You are not authorized to edit this user's profile.")
        
        return user_to_edit

    def form_valid(self, form):
        # Perform any additional checks or actions before saving the form
        return super().form_valid(form)




class UserProfilePhotoUpdateView(LoginRequiredMixin, FormView):
    template_name = 'core/user_profile_photo_update.html'
    form_class = UserProfilePhotoForm
    success_url = reverse_lazy('user_profile')  # Redirect to user profile after successful upload

    def get_object(self):
        """
        Fetches the user based on the username in the URL.
        """
        username = self.kwargs.get('username')
        user = get_object_or_404(User, username=username)
        
        # Ensure that a user can only update their own profile photo
        if self.request.user.username != username and not self.request.user.is_staff:
            raise PermissionDenied("You cannot update another user's profile photo.")
        
        return user

    def form_valid(self, form):
        """
        If the form is valid, save the new profile photo for the user.
        """
        user = self.get_object()  # Get the user object based on the URL username
        profile_photo = form.cleaned_data['cropped_image']  # Get the uploaded photo
        
        # Create a new UserDocument entry for the profile photo
        user.documents.create(
            file_path=profile_photo,
            document_name='profile_photo',
            document_type='profile_photo',
            document_context='general'
        )
        
        return super().form_valid(form)
