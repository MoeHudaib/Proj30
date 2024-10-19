from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CreateUserForm, ProfileUpdateForm, UpdateUserForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
def register(request):
    """Register a new user."""
    if request.method != "POST":
        # Display blank registration form.
        form = CreateUserForm()
    else:
        # Process completed form.
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            staff_name = form.cleaned_data.get('username')
            messages.success(request, f'Hello {staff_name}, your account has been successfully created.')
            return redirect("user:user-login")

    # Display a blank or invalid form.
    context = {
        "form": form
        }
    return render(request, "user/register.html", context)

@login_required(login_url='user:user-login')
def user_profile(request):

    return render(request, 'user/profile.html')

@login_required(login_url='user:user-login')
def update_profile(request):
    if request.method == 'POST':
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        user_form = UpdateUserForm(request.POST, instance=request.user)
        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(request, 'Your profile has been successfully updated.')
            return redirect('user:user-profile')
    else:
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        user_form = UpdateUserForm(instance=request.user)

    context = {
        'profile_form': profile_form,
        'user_form': user_form
    }
    return render(request, 'user/update_profile.html', context)

from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.shortcuts import render

class CustomPasswordResetView(PasswordResetView):
    template_name = 'user/password_reset.html'
    email_template_name = 'user/password_reset_email.html'
    subject_template_name = 'user/password_reset_subject.txt'
    success_url = reverse_lazy('user:password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'user/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'user/password_reset_confirm.html'
    success_url = reverse_lazy('user:password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'user/password_reset_complete.html'
