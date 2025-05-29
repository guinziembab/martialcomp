# competitions/auth_forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Requis. Entrez une adresse email valide.')
    first_name = forms.CharField(max_length=30, required=True, help_text='Requis.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Requis.')
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')