from django import forms
from django.contrib.auth.models import User
from .models import Customer
from django.core.exceptions import ValidationError


class  RegistrationForm(forms.Form):
    username = forms.CharField()
    email = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Password_confirm")


    class Meta:
        models = User
        feilds =[ 'username', 'email', 'password' , 'password_confirm'] 

        def clean(self): 
            cleaned_data = super().clean()
            password = cleaned_data.get('password')
            password_confirm = cleaned_data.get('password_confirm')

            if password and password_confirm and password_confirm.lower() != password:
                raise forms.validationerror('Invalid password')
            return cleaned_data
    #     def clean_email(self):
    #         email = self.cleaned_data['email'] 
    #         if 
    # User.objects.filter(email=email).exists():
    # raise ValidationError('Email already exists.')  return email      

  

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone' , 'address']










