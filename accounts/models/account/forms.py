from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm, ReadOnlyPasswordHashField, UserCreationForm, \
    UsernameField

from .models import Account


class RegistrationForm(UserCreationForm):
    class Meta:
        model = Account
        fields = ("email", "username")
        field_classes = {'email': UsernameField}

    def save(self, commit=True):
        user = Account.objects.create_user(
            password=self.cleaned_data['password1'],
            email=self.cleaned_data['email'],
            username=self.cleaned_data['username']
        )
        return user


class LoginForm(AuthenticationForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput())

    class Meta:
        model = Account
        fields = ("username", "password")


class AccountUpdateForm(UserChangeForm):
    password = ReadOnlyPasswordHashField(
        label="Password",
        help_text=f'Raw passwords are not stored, so there is no way to see this '
                  'user’s password, but you can change the password using '
                  '<a href="/accounts/change_password">this form</a>.'
    )

    class Meta:
        model = Account
        fields = (
            'username',
            'email'
        )


class UpdatePasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = Account
        fields = ("password", "confirm_password")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Your passwords don't match!")
