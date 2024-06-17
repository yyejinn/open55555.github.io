from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['author', 'content']

class AdminAuthForm(forms.Form):
    admin_id = forms.CharField(label='Admin ID', max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
