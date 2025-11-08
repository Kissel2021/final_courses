from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, authenticate
from django.utils.html import strip_tags
from django.core.validators import RegexValidator

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        max_length=30,
        widget=forms.EmailInput(attrs={'class': 'input-register form-control', 'placeholder': 'Ваш email'})
    )
    first_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Имя'})
    )
    last_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Фамилия'})
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'input-register form-control', 'placeholder': 'Пароль'})
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={'class': 'input-register form-control', 'placeholder': 'Подтвердите свой пароль'})
    )
    marketing_consent1 = forms.BooleanField(
        required=False,
        label="I agree to receive commercial, promotional, and marketing communications.",
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input-register'})
    )
    marketing_consent2 = forms.BooleanField(
        required=False,
        label="I agree to receive personalized commercial communications.",
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input-register'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2',
                  'marketing_consent1', 'marketing_consent2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже используется.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = None
        user.marketing_consent1 = self.cleaned_data['marketing_consent1']
        user.marketing_consent2 = self.cleaned_data['marketing_consent2']
        if commit:
            user.save()
        return user


class CustomUserLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Email',
        widget=forms.TextInput(
            attrs={'autofocus': True, 'class': 'input-register form-control', 'placeholder': 'Ваш email'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'input-register form-control', 'placeholder': 'Ваш пароль'})
    )

    def clean(self):
        email = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(self.request, username=email,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError('Неверный email или пароль.')
            elif not self.user_cache.is_active:
                raise forms.ValidationError('Этот аккаунт не активен.')
        return self.cleaned_data


class CustomUserUpdateForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', "Enter a valid phone number.")],
        widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Ваш номер телефона'})
    )
    first_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Ваше имя'})
    )
    last_name = forms.CharField(
        required=True,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'input-register form-control', 'placeholder': 'Ваша фамилия'})
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'input-register form-control', 'placeholder': 'Ваш email'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'patronymic', 'email', 'address1', 'address2',
                  'city', 'country', 'region', 'shipping_method', 'shipping_location', 'postal_code', 'phone')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'input-register form-control',
                                             'placeholder': 'Ваш email'}),
            'first_name': forms.TextInput(attrs={'class': 'input-register form-control',
                                                 'placeholder': 'Ваше имя'}),
            'last_name': forms.TextInput(attrs={'class': 'input-register form-control',
                                                'placeholder': 'Ваша фамилия'}),
            'address1': forms.TextInput(attrs={'class': 'input-register form-control',
                                               'placeholder': 'Улица'}),
            'address2': forms.TextInput(attrs={'class': 'input-register form-control',
                                               'placeholder': 'Дом'}),
            'city': forms.TextInput(attrs={'class': 'input-register form-control',
                                           'placeholder': 'Город'}),
            'country': forms.TextInput(attrs={'class': 'input-register form-control',
                                              'placeholder': 'Страна'}),
            'region': forms.TextInput(attrs={'class': 'input-register form-control',
                                             'placeholder': 'ПГТ/село'}),
            'shipping_method': forms.TextInput(attrs={'class': 'input-register form-control',
                                               'placeholder': 'Служба доставки'}),
            'shipping_location': forms.TextInput(attrs={'class': 'input-register form-control',
                                                 'placeholder': '№ отделения'}),
            'postal_code': forms.TextInput(attrs={'class': 'input-register form-control',
                                                  'placeholder': 'Почтовый индекс'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Этот email уже используется.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('email'):
            cleaned_data['email'] = self.instance.email

        for field in ['address1', 'address2', 'city', 'country', 'region',
                      'shipping_method', 'shipping_location', 'postal_code', 'phone', ]:
            if cleaned_data.get(field):
                cleaned_data[field] = strip_tags(cleaned_data[field])

        return cleaned_data