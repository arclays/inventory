
# from django.contrib.auth.models import User
from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from django.contrib.auth.models import User
from.models import Customer, Product, Order, Stock

# admin.site.register(User, UserAdmin)
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(Stock)