from django import forms
from .models import Product
from django.contrib.auth.models import User
from .models import Customer, Order

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        labels = {
            'product_id': 'Product ID',
            'name': 'Product Name',
            'sku': 'SKU',
            'price': 'Price', 
            'units': 'units',
            ' quantity_in_stock': ' quantity_in_stock',
        }
            
        widgets = {
           'product_id': forms.NumberInput(attrs={ 'placeholder': 'e.g 1 ', 'class': 'form-control'}),
        #    'selling_price': forms.NumberInput(attrs={ 'placeholder': 'e.g shs1000 ', 'class': 'form-control'}),
           'units': forms.TextInput(attrs={ 'placeholder': 'e.g peice/dozen', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={ 'placeholder': 'e.g skirt ', 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={ 'placeholder': 'e.g shs1000.0 ', 'class': 'form-control'}),
            'category': forms.TextInput(attrs={ 'placeholder': 'your category', 'class': 'form-control'}),
            'quantity_in_stock': forms.NumberInput(attrs={ 'placeholder': 'e.g 1 ', 'class': 'form-control'}),
            'supplier': forms.TextInput(attrs={ 'placeholder': 'your supplier ', 'class': 'form-control'}),
            'reorder_level': forms.NumberInput(attrs={ 'placeholder': 'e.g 5 ', 'class': 'form-control'}),
            'reorder_quantity': forms.NumberInput(attrs={ 'placeholder': 'e.g 10 ', 'class': 'form-control'}),
        
        }  

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
  

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone']

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'        

        

