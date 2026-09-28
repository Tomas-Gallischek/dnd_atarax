from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import Player


class PlayerLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Uživatelské jméno",
        widget=forms.TextInput(attrs={'placeholder': 'Uživatelské jméno', 'autofocus': True})
    )
    password = forms.CharField(
        label="Heslo",
        widget=forms.PasswordInput(attrs={'placeholder': 'Heslo'})
    )


class PlayerRegistrationForm(forms.ModelForm):
    nickname = forms.CharField(
        max_length=100,
        required=False,
        label="Přezdívka hráče",
        help_text="Volitelné jméno nebo přezdívka, která se bude zobrazovat v aplikaci.",
        widget=forms.TextInput(attrs={'placeholder': 'Přezdívka (volitelné)'})
    )
    password = forms.CharField(
        label="Heslo",
        widget=forms.PasswordInput(attrs={'placeholder': 'Zadejte heslo'})
    )
    password_confirm = forms.CharField(
        label="Potvrzení hesla",
        widget=forms.PasswordInput(attrs={'placeholder': 'Zopakujte heslo'})
    )

    class Meta:
        model = User
        fields = ('username', 'email')
        labels = {
            'username': 'Uživatelské jméno',
            'email': 'E-mail',
        }
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Uživatelské jméno'}),
            'email': forms.EmailInput(attrs={'placeholder': 'E-mail (volitelné)'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Uživatel s tímto uživatelským jménem již existuje.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Zadaná hesla se neshodují.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            nickname = self.cleaned_data.get('nickname') or user.username
            Player.objects.create(user=user, nickname=nickname)
        return user
