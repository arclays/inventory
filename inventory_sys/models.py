from django.db import models
from django.utils import timezone

class Product(models.Model):
    product_id = models.AutoField(primary_key=True) 
    name = models.CharField(max_length=100, unique=True)
    sku = models.CharField(max_length=100)
    category = models.CharField(max_length=10)
    price = models.FloatField()
    units = models.CharField(max_length=50, default='pcs') 
    quantity_in_stock = models.IntegerField()
    supplier = models.CharField(max_length=100)
    reorder_level = models.PositiveIntegerField(default=40)  # Set a default reorder level
    reorder_quantity = models.PositiveIntegerField(default=50) 

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

    def __str__(self):
        return self.name


# ✅ Updated Order Model 
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
    units = models.CharField(max_length=50, default='pcs')  # Changed from IntegerField to CharField
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Added for clarity
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default="cash")  # Added Payment Method
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Added Discount
    final_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Added Final Total
    order_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Order {self.id} by {self.customer.name}"

    def save(self, *args, **kwargs):
    # Ensure price per unit is greater than product price
     if self.product:  # Ensure product exists
        if self.price_per_unit <= self.product.price:
            self.price_per_unit = self.product.price * 1.1  # Example: Set 10% higher than base price

      # Ensure discount is a valid float
     try:
        self.discount = float(self.discount) if self.discount else 0.00
     except (ValueError, TypeError):
        self.discount = 0.00  # Default to 0.00 if invalid      

    # Calculate total price
     self.total_price = self.quantity * self.price_per_unit

    # Apply discount
     discount_amount = (self.total_price * self.discount) / 100.00
     self.final_total = self.total_price - discount_amount

     super().save(*args, **kwargs)  # Call parent save method

    


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
    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPES)
    quantity = models.IntegerField()
    reason = models.TextField()
    adjustment_date = models.DateField(default=timezone.now)