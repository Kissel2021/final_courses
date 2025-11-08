from django.db import models
from django.contrib.auth.models import AbstractUser, \
    BaseUserManager
from django.utils.html import strip_tags
from django import forms


class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Необходимо заполнить поле email')
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name,
                          last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, first_name, last_name, password, **extra_fields)


SHIPPING_METHODS = [
    ('nova_poshta', 'Нова Пошта'),
    ('ukrposhta', 'Укрпошта'),
    ('meest', 'Meest Express'),
    ('pickup', 'Самовывоз'),
    ('courier', 'Курьер'),
    ('international', 'Международная почта'),
]


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, max_length=30)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    patronymic = models.CharField(max_length=30, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    country = models.CharField(max_length=128, blank=True, null=True)
    region = models.CharField(max_length=128, blank=True, null=True)
    city = models.CharField(max_length=128, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    shipping_method = models.CharField(max_length=50, choices=SHIPPING_METHODS, blank=True, null=True)
    shipping_location = models.CharField(max_length=128, blank=True, null=True)

    address1 = models.CharField(max_length=128, blank=True, null=True)
    address2 = models.CharField(max_length=128, blank=True, null=True)

    marketing_consent1 = models.BooleanField(default=False)
    marketing_consent2 = models.BooleanField(default=False)

    username = models.CharField(max_length=30, unique=True, null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    def clean(self):
        for field in ['address1', 'address2', 'city', 'country', 'region',
                      'shipping_method', 'shipping_location', 'postal_code', 'phone']:
            value = getattr(self, field)
            if value:
                setattr(self, field, strip_tags(value))