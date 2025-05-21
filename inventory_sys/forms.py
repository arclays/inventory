from django import forms
from .models import Customer, Product, ProductBatch , Supplier,Order
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime,date




class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'required': True}),
            'email': forms.EmailInput(attrs={'required': True}),
            'phone': forms.TextInput(attrs={'required': True}),
            'address': forms.Textarea(attrs={'required': True}),
        }       


# class ProductForm(forms.ModelForm):
#     class Meta:
#         model = Product
#         fields = ['name', 'quantity_in_stock', 'units', 'category', 
#                  'selling_price', 'reorder_quantity', 'reorder_level']
#         widgets = {
#             'category': forms.Select(),
#             'name': forms.TextInput(),
#             'quantity_in_stock': forms.NumberInput(attrs={'min': 0}),
#             'units': forms.Select(),
#             'selling_price': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
#             'reorder_quantity': forms.NumberInput(attrs={'min': 0}),
#             'reorder_level': forms.NumberInput(attrs={'min': 0}),
#         }

#     def clean_name(self):
#         name = self.cleaned_data.get('name')
#         if Product.objects.filter(name__iexact=name).exists():
#             raise forms.ValidationError(f"Product '{name}' already exists!")
#         return name

class UserProfileForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False, label="Confirm New Password")
    

class StockAdjustmentForm(forms.Form):
    product_id = forms.IntegerField(label='Product ID')
    adjustment_type = forms.ChoiceField(choices=[('add', 'Add'), ('subtract', 'Subtract')], label='Adjustment Type')
    quantity = forms.IntegerField(min_value=1, label='Quantity')
    reason = forms.CharField(max_length=255, label='Reason')
    batch_sku = forms.IntegerField(required=False, label='Batch SKU')

    def clean_product_id(self):
        product_id = self.cleaned_data['product_id']
        try:
            product = Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            raise ValidationError("Product not found.")
        return product

    def clean_batch_sku(self):
        batch_sku = self.cleaned_data.get('batch_sku')
        product = self.cleaned_data.get('product_id')
        if batch_sku:
            try:
                batch = ProductBatch.objects.get(id=batch_sku, product=product)
            except ProductBatch.DoesNotExist:
                raise ValidationError("Invalid Batch ID.")
            return batch
        return None

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        adjustment_type = self.cleaned_data['adjustment_type']
        batch = self.cleaned_data.get('batch_sku')

        if adjustment_type == 'subtract' and batch:
            if batch.current_quantity < quantity:
                raise ValidationError("Insufficient stock in selected batch to subtract.")
        return quantity

class DateRangeForm(forms.Form):
    start_date = forms.DateField(label='Start Date', required=False)
    end_date = forms.DateField(label='End Date', required=False)

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError("Start date must be before or equal to end date.")
        elif start_date or end_date:
            raise ValidationError("Both start date and end date must be provided.")

        if not start_date and not end_date:
            cleaned_data['start_date'] = timezone.now().date()
            cleaned_data['end_date'] = timezone.now().date()

        return cleaned_data    


class AddStockForm(forms.Form):
    product_id = forms.IntegerField()
    supplier_id = forms.IntegerField()
    new_stock = forms.IntegerField(min_value=1)
    batch_sku = forms.CharField(required=False)
    buying_price = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    manufacture_date = forms.DateField(required=False)
    expiry_date = forms.DateField(required=False)
    stock_date = forms.DateField(required=False)

    def clean_product_id(self):
        product_id = self.cleaned_data.get('product_id')
        try:
            product = Product.objects.get(product_id=product_id)
        except Product.DoesNotExist:
            raise ValidationError(f"Product with ID {product_id} does not exist.")
        return product_id

    def clean_supplier_id(self):
        supplier_id = self.cleaned_data.get('supplier_id')
        try:
            supplier = Supplier.objects.get(id=supplier_id)
        except Supplier.DoesNotExist:
            raise ValidationError(f"Supplier with ID {supplier_id} does not exist.")
        return supplier_id   


class ExportCSVForm(forms.Form):
    order_date = forms.DateField(required=False, input_formats=['%Y-%m-%d'])

    def clean_order_date(self):
        order_date = self.cleaned_data.get('order_date')
        if not order_date:
            order_date = datetime.now().date()
        return order_date    

class OrderFilterForm(forms.Form):
    start_date = forms.DateField(required=False, input_formats=['%Y-%m-%d'])
    end_date = forms.DateField(required=False, input_formats=['%Y-%m-%d'])
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), required=False)
    status = forms.ChoiceField(choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], required=False)
    payment_method = forms.ChoiceField(choices=[
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer')
    ], required=False)
    search = forms.CharField(required=False)
    sort_by = forms.ChoiceField(choices=[
        ('order_date', 'Order Date (Ascending)'),
        ('-order_date', 'Order Date (Descending)'),
        ('customer__name', 'Customer Name (Ascending)'),
        ('-customer__name', 'Customer Name (Descending)'),
        ('product__name', 'Product Name (Ascending)'),
        ('-product__name', 'Product Name (Descending)'),
        ('final_total', 'Final Total (Ascending)'),
        ('-final_total', 'Final Total (Descending)')
    ], required=False, initial='-order_date')
    page_size = forms.ChoiceField(choices=[
        (10, '10'),
        (25, '25'),
        (50, '50'),
        (100, '100')
    ], required=False, initial=10)

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if not start_date:
            start_date = datetime.now().date()
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        if not end_date:
            end_date = datetime.now().date()
        return end_date


