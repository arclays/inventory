from django.db import models
from django.utils import timezone
from django.db.models import F
from datetime import date
from django.db import transaction

class Product(models.Model):
    product_id = models.AutoField(primary_key=True) 
    name = models.CharField(max_length=100, unique=True) 
    category = models.CharField(max_length=10)
    selling_price = models.FloatField()
    units = models.CharField(max_length=50, default='pcs') 
    manufacture_date = models.DateField(null=True, blank=True, default=date.today)
    quantity_in_stock = models.IntegerField()
    supplier = models.CharField(max_length=100)
    reorder_quantity = models.PositiveIntegerField(default=0) 
    reorder_level = models.PositiveIntegerField(default=0)  # 
    buying_price = models.FloatField() 

    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level

    def __str__(self):
        return self.name


class User(models.Model):
    email = models.EmailField(max_length=100, unique=True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=100)
    confirm_password = models.CharField(max_length=100)   


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=40)

    def __str__(self):
        return self.name



class Order(models.Model):
    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("credit_card", "Credit Card"),
        ("mobile_money", "Mobile Money"),
        ("bank_transfer", "Bank Transfer"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, to_field="product_id", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    units = models.CharField(max_length=50, default='pcs')  
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default="cash") 
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00) 
    final_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) 
    order_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Order {self.id} by {self.customer.name}"

    def save(self, *args, **kwargs):
     if self.product:
        if not self.price_per_unit or self.price_per_unit == 0.00:
            self.price_per_unit = self.product.selling_price 

     try:
        self.discount = float(self.discount) if self.discount else 0.00
     except (ValueError, TypeError):
        self.discount = 0.00  

     self.total_price = (self.quantity * self.price_per_unit ) - ((self.quantity * self.price_per_unit) * ( self.discount/ 100.00))

     self.final_total += self.total_price  

     super().save(*args, **kwargs)

    


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    initial_stock = models.IntegerField()
    new_stock = models.IntegerField()
    total_stock = models.IntegerField()
    stock_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.total_stock}"
    

class StockAdjustment(models.Model):
    ADJUSTMENT_TYPES = (
        ('add', 'Addition'),
        ('subtract', 'Subtraction')
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    quantity = models.IntegerField()
    reason = models.TextField()
    adjustment_date = models.DateField(default=timezone.now)



    def apply_adjustment(self):
        """Update product stock based on adjustment type"""
        with transaction.atomic(): 
         self.product.refresh_from_db() 

        if self.adjustment_type == 'add':
            self.product.quantity_in_stock = F('quantity_in_stock') + self.quantity
        elif self.adjustment_type == 'subtract':
            if self.product.quantity_in_stock >= self.quantity:
                self.product.quantity_in_stock = F('quantity_in_stock') - self.quantity
            else:
                raise ValueError("Insufficient stock to subtract")

        self.product.save(update_fields=['quantity_in_stock'])

    def __str__(self):
        return f"{self.adjustment_type} {self.quantity} of {self.product.name}"    