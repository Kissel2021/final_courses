from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_welcome_email(email, first_name):
    subject = "Добро поджаловать!"
    message = f"""
    Здравствуйте {first_name},

    Спасибо, что присоединились к нам! Мы очень рады видеть вас на нашей платформе.
    Открывайте для себя новые возможности, изучайте функционал и просто наслаждайтесь процессом.
    """
    html_message = f"""
    <h1>Здравстуйте, {first_name}!</h1>
    <p>Спасибо, что присоединились к нам! Мы очень рады видеть вас на нашей платформе.</p>
    <p>Открывайте для себя новые возможности, изучайте функционал и просто наслаждайтесь процессом.</p>
    <p>С уважением,<br>Ваша команда платформы</p>
    """
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            html_message=html_message
        )
        logger.info(f"Welcome email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        raise


@shared_task
def send_password_reset_email(email, user_id):
    from .models import CustomUser
    from django.urls import reverse
    from django.contrib.auth.tokens import default_token_generator
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes

    logger.info(f"Starting password reset email task for {email}, user_id={user_id}")
    try:
        user = CustomUser.objects.get(pk=user_id)
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"{settings.SITE_URL}{reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
        subject = "Password Reset Request"
        message = f"""
        Здравствуйте, {user.first_name or user.email},

        Перейдите по ссылке ниже, чтобы сбросить пароль:
        {reset_url}

        Если вы не запрашивали смену пароля — просто проигнорируйте это письмо, никаких действий предпринимать не нужно.

        С уважением,
        Ваша команда платформы
        """
        html_message = f"""
        <h1>Password Reset Request</h1>
        <p>Здравствуйте, {user.first_name or user.email},</p>
        <p>Перейдите по ссылке ниже, чтобы сбросить пароль:</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>Если вы не запрашивали смену пароля — просто проигнорируйте это письмо, никаких действий предпринимать не нужно. </p>
        <p>С уважением,<br>Ваша команда платформы</p>
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
            html_message=html_message
        )
        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        raise
