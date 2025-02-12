from django.db import models
from django.utils import timezone

# Create your models here.
class Product(models.Model):
    product_id = models.AutoField(primary_key=True) 
    name = models.CharField(max_length=100, unique=True)
    sku = models.CharField(max_length=100)
    category =models.CharField(max_length=10)
    price = models.FloatField()
    units = models.CharField(max_length=50, default='pcs') 
    quantity_in_stock = models.IntegerField()
    supplier = models.CharField(max_length=100)


class User(models.Model):
    email = models.EmailField(max_length=100, unique=True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=100)
    confirm_password = models.CharField(max_length=100)   

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    
# Order Model 
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, to_field="product_id", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    units = models.IntegerField(default=1, help_text="Number of units ordered")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Set a default value
    order_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Order {self.id} by {self.customer.name}"

    def save(self, *args, **kwargs):
        # Calculate total price before saving
        self.total_price = self.quantity * self.product.price
        super(Order, self).save(*args, **kwargs)


class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    initial_stock = models.IntegerField()
    new_stock = models.IntegerField()
    total_stock = models.IntegerField()
    stock_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.product.name} - {self.total_stock}"
                           
