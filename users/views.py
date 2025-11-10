from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomUserLoginForm, CustomUserUpdateForm, PasswordResetRequestForm, \
    PasswordResetConfirmForm
from .models import CustomUser
from .tasks import send_welcome_email, send_password_reset_email
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
import logging


logger = logging.getLogger(__name__)


def new_register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            send_welcome_email.delay(user.email, user.first_name)
            logger.info(f"Welcome email task queued for {user.email}")
            return redirect('users:profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})


def login_user(request):
    if request.method == 'POST':
        form = CustomUserLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('users:profile')
    else:
        form = CustomUserLoginForm()
    return render(request, 'users/login.html', {'form': form})


@login_required
def profile(request):
    return render(request, 'users/profile.html', {'user': request.user})


@login_required
def account_details(request):
    user = CustomUser.objects.get(id=request.user.id)
    return render(request, 'users/account_details.html',
                  {'user': user})


@login_required
def edit_account_details(request):
    form = CustomUserUpdateForm(instance=request.user)
    return render(request, 'users/edit_account_details.html',
                  {'user': request.user, 'form': form})


@login_required
def update_account_details(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.clean()
            user.save()
            return render(request, 'users/account_details.html', {'user': user})
        else:
            return render(request, 'users/edit_account_details.html', {'user': request.user, 'form': form})
    return render(request, 'users/account_details.html', {'user': request.user})


def logout_user(request):
    logout(request)
    return redirect('users:register')


def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.filter(email=email).first()
            if user:
                logger.info(f"Attempting to send password reset email to {email} for user ID {user.pk}")
                send_password_reset_email.delay(email, user.pk)
                messages.success(request, "Сообщение о восстановлении пароля отправлено. Пожалуйста, проверьте свой почтовый ящик или вкладку спам.")
                return render(request, 'users/password_reset_done.html')
            else:
                messages.warning(request, "Учетная запись с этой электронной почтой не найдена.")
        else:
            messages.error(request, "Пожалуйста, введите валидный email.")
    else:
        form = PasswordResetRequestForm()
    return render(request, 'users/password_reset_request.html', {'form': form})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = PasswordResetConfirmForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                messages.success(request, "Ваш пароль успешно воссановлен.")
                return render(request, 'users/password_reset_complete.html')
        else:
            form = PasswordResetConfirmForm()
        return render(request, 'users/password_reset_confirm.html', {'form': form, 'validlink': True})
    else:
        return render(request, 'users/password_reset_confirm.html', {'validlink': False})


def index(request):
    return render(request, 'index.html')


