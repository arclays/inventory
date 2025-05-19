from django.db import models
from django.utils import timezone
from django.db.models import F
from django.db import transaction
from django.core.validators import MinLengthValidator, RegexValidator
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

class Category(models.Model):
    CATEGORY_TYPES = [
        ('raw_material', 'Raw Material'),
        ('finished_goods', 'Finished Goods'),
        ('wip', 'Work-in-Progress'),
        ('consumable', 'Consumable'),
        ('service', 'Service'),
    ]
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default='')
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, default='finished_goods')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Supplier(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=255)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')]
    )
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Product(models.Model):
    UNITS = [
        ('pcs', 'Pieces'),
        ('kg', 'Kilograms'),
        ('l', 'Liters'),
        ('m', 'Meters'),
    ]
    product_id = models.AutoField(primary_key=True) 
    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    units = models.CharField(max_length=10, choices=UNITS, default='pcs')
    quantity_in_stock = models.PositiveIntegerField(default=0)
    reorder_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0)

    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class ProductBatch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_sku = models.CharField(max_length=50, unique=True, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    initial_quantity = models.PositiveIntegerField()
    current_quantity = models.PositiveIntegerField()
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='batches')
    buying_price = models.DecimalField(max_digits=10, decimal_places=2)
    manufacture_date = models.DateField(null=True, blank=True)
    stock_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.product.name} - {self.batch_sku or 'No SKU'}"

    class Meta:
        ordering = ['-stock_date']

class Stock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    initial_stock = models.IntegerField()
    new_stock = models.IntegerField()
    total_stock = models.IntegerField()
    stock_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.product.name} - {self.total_stock}"

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')]
    )
    address = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Order(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    quantity = models.PositiveIntegerField()
    batch_sku = models.ForeignKey(ProductBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    units = models.CharField(max_length=10, default='pcs')
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00) 
    final_total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    order_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def save(self, *args, **kwargs):
        """Calculate price_per_unit, total_price, and final_total before saving."""
        if not self.price_per_unit:
            self.price_per_unit = self.product.selling_price

        # total_price = self.quantity * self.price_per_unit
        # self.final_total = total_price * (1 - self.discount / 100)
        self.total_price = float((self.quantity * self.price_per_unit ) - ((self.quantity * self.price_per_unit) * ( self.discount/ 100.00)))
        self.final_total = 0  # Initialize final_total to 0
        self.final_total = + float(self.total_price)  

        # Validate stock availability
        if self.quantity > self.product.quantity_in_stock:
            raise ValueError("Order quantity exceeds available stock.")

        super().save(*args, **kwargs)

        # Update product stock
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=self.product.pk)
            product.quantity_in_stock -= self.quantity
            product.save()

    def __str__(self):
        return f"Order {self.id} by {self.customer.name}"

    class Meta:
        ordering = ['-order_date']


class StockAdjustment(models.Model):
    ADJUSTMENT_TYPES = (
        ('add', 'Addition'),
        ('subtract', 'Subtraction'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='adjustments')
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    quantity = models.IntegerField()
    reason = models.TextField()
    batch = models.ForeignKey('ProductBatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='adjustments')
    created_at = models.DateTimeField(default=timezone.now)
    def apply_adjustment(self):
        """Update product stock based on adjustment type."""
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=self.product.pk)
            if self.adjustment_type == 'add':
                product.quantity_in_stock += self.quantity
            elif self.adjustment_type == 'subtract':
                if product.quantity_in_stock < self.quantity:
                    raise ValueError("Insufficient stock to subtract")
                product.quantity_in_stock -= self.quantity
            product.save()

    def __str__(self):
        return f"{self.adjustment_type} {self.quantity} of {self.product.name}"

    class Meta:
        ordering = ['-created_at']
