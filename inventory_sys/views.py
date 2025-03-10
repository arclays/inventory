from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductForm, CustomerForm
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm
from django.core.paginator import Paginator
from django.contrib import messages
from .forms import CustomerForm
from datetime import datetime, date
from django.urls import reverse
from .models import Customer, Product, Order,User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Order, Stock, StockAdjustment
from django.db.models import Sum
from django.db.models import F
from django.shortcuts import get_object_or_404

# CRUD
# Home_view
# @login_required
def home_view(request):
    orders = Order.objects.all()
    return render(request, 'Invapp/home.html', {'orders': orders})


def register_view(request):
    if request.method == 'POST': 
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'Invapp/register.html', {'form': form}) 

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or reverse('home')
            return redirect(next_url)
        else:
            return render(request, 'Invapp/login.html', {'error': 'Invalid credentials'})

    next_url = request.GET.get('next', '')
    return render(request, 'Invapp/login.html', {'next': next_url})


def logout_view(request):
    logout(request)
    return redirect('login') 

class ProtectedView(LoginRequiredMixin, View):
    login_url = '/Invapp/login/'  # Ensure this matches your login route
    redirect_field_name = 'next'

    def get(self, request):
        return render(request, 'Invapp/products.html')      


# Create_view

def product_list(request):
    products = Product.objects.all()
    paginator = Paginator(products, 7) 

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product added successfully!')
            return redirect('product_list')
    else:
        form = ProductForm()

    return render(request, 'Invapp/product_list.html', {'page_obj': page_obj, 'form': form})

def customer_list(request):
    customers = Customer.objects.all()  
    paginator = Paginator(customers, 7) 

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer added successfully!')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    return render(request, 'Invapp/customer_list.html', {'form': form, 'page_obj': page_obj})


def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, customer_id=customer_id) 
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer) 
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer edited successfully!')
            return redirect('customer_list')  
    else:
        form = CustomerForm(instance=customer)  
    return render(request, 'Invapp/customer_edit.html', {'form': form})

def customer_confirm_delete(request, customer_id):
    customer = get_object_or_404(Customer, customer_id=customer_id)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully!')
        return redirect('customer_list')
    return render(request, 'Invapp/customer_confirm_delete.html', {'customer': customer})


def product_update(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'Invapp/product_update.html', {'form': form})

def product_confirm_delete(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('product_list')
    return render(request, 'Invapp/product_confirm_delete.html', {'product': product})


def order_page(request):
    units = "pcs"
    selected_date = request.GET.get('orderDate', str(date.today()))

    orders = Order.objects.filter(order_date=selected_date)

    total_customers = orders.values('customer').distinct().count()
    total_orders = orders.count()
    total_cash_made = sum(order.final_total for order in orders)
    total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0

    customers = Customer.objects.all()
    products = Product.objects.all()

    paginator = Paginator(orders, 8)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,  # Use paginated orders instead of full list
        'page_obj': page_obj,  # Pass pagination object
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_cash_made': total_cash_made,
        'selected_date': selected_date,
        'total_quantity': total_quantity,
        'customers': customers,
        'units': units,
        'products': products,
    }

    return render(request, 'InvApp/order_page.html', context)

def place_order(request):
    if request.method == 'POST':
        # print(request.POST)
        customer_id = request.POST.get('orderCustomer')
        # product_id = request.POST.get('orderProduct') 
        quantity = request.POST.get('orderQuantity')

        products = request.POST.getlist('products[]')
        order_quantities = request.POST.getlist('orderQuantity[]')
        units = request.POST.getlist('units[]')
        unit_prices = request.POST.getlist('unitPrice[]')
        total_prices = request.POST.getlist('totalPrice[]')


        product_list = []
        # total_amount=0
        for i in range(len(products)):
            order = {
                'product_id': products[i],
                'quantity': int(order_quantities[i]),
                'unit': units[i],
                'unit_price': float(unit_prices[i]),
                'total_price': float(total_prices[i])
            }
            product_list.append(order)
            # total_amount=total_amount+float(total_prices[i])
        # print(product_list)



        customer = Customer.objects.get(id=customer_id)

        # Retrieve payment method and discount from the form
        payment_method = request.POST.get('paymentMethod', 'cash')  # Default to 'cash' if not provided
        discount = request.POST.get('discount', '0.00')  # Default to '0' if not provided

        # Convert discount to float (handles potential string input errors)
        try:
            discount = float(discount)
        except ValueError:
            discount = 0.0  # Fallback to 0.0 if conversion fails



        # store items
        for item in product_list:
            product_id =item['product_id']
            unit_id = item['unit']
            unit_price = item['unit_price']
            total_price = item['total_price']
            quantity = item['quantity']
            

            # Check if product has enough stock
            product = Product.objects.get(product_id=product_id)
            quantity = int(quantity)
            if quantity <= 0 or quantity > product.quantity_in_stock:
                pass
            else:
                # Create Order Item
               Order.objects.create(
                   customer=customer,
                   product=product,
                   quantity=quantity,
                   price_per_unit=unit_price,
                   total_price=total_price,
                   units=unit_id,
                   payment_method=payment_method,  # Ensure this is provided
                   discount=discount,  # Ensure this is provided
)

                # Deduct from product stock
        product.quantity_in_stock -= quantity
        product.save()


        return redirect('order_page')

    return render(request, 'Invapp/order_page.html')

def stock_view(request):
  
    selected_date = request.GET.get('orderDate', str(date.today()))
    selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    stocks = Stock.objects.filter(stock_date=selected_date)
    
    products = Product.objects.all()

    paginator = Paginator(stocks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)                                                                                                                                        

   
    return render(request, 'Invapp/stock.html', {
        'stocks': page_obj,  
        'products': products,
        'selected_date': selected_date,
        'page_obj': page_obj  
    })
def add_stock(request):
     

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        new_stock = request.POST.get('newStock')
        expiry_date = request.POST.get('expiryDate')

        

    # Ensure we use the correct field name
        product = get_object_or_404(Product, product_id=product_id)  

        initial_stock = product.quantity_in_stock  
        total_stock = int(initial_stock) + int(new_stock ) 

        product.quantity_in_stock = total_stock
        product.save()

        stock = Stock.objects.filter(product=product).first()
        if stock:
            stock.total_stock = total_stock
            stock.save()

        # Save to Stock table
        Stock.objects.create(
            product=product,
            initial_stock=initial_stock,
            new_stock=new_stock,
            total_stock=total_stock,  
            stock_date=timezone.now().date(),
            expiry_date=expiry_date,
        )

        return redirect('stock')

    # Fetch all products for dropdown
    products = Product.objects.all()
    return render(request, 'InvApp/stock.html', {'products': products})

def apply_adjustment(self):
        """Updates the stock levels based on the adjustment."""
        if self.adjustment_type == 'add':
            self.product.quantity_in_stock += self.quantity
        elif self.adjustment_type == 'subtract':
            self.product.quantity_in_stock -= self.quantity
            if self.product.quantity_in_stock < 0:
                self.product.quantity_in_stock = 0  # Prevent negative stock
        self.product.save()

def adjust_stock(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        adjustment_type = request.POST.get('adjustment_type')
        quantity = request.POST.get('quantity')
        reason = request.POST.get('reason')
        adjustment_date = request.POST.get('adjustmentDate')

        # Check if product_id is empty
        if not product_id:
            messages.error(request, "Please select a valid product.")
            return redirect('stock')

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Quantity must be a positive number.")
            return redirect('stock')

        if adjustment_type not in ["add", "subtract"]:
            messages.error(request, "Invalid adjustment type.")
            return redirect('stock')

        product = get_object_or_404(Product, id=product_id)

        # Ensure sufficient stock before subtracting
        if adjustment_type == "subtract" and product.quantity_in_stock < quantity:
            messages.error(request, "Not enough stock to subtract.")
            return redirect('stock')

        # Convert adjustment_date to DateTime object if provided
        if adjustment_date:
            try:
                adjustment_date = datetime.strptime(adjustment_date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid date format.")
                return redirect('stock')
        else:
            adjustment_date = datetime.today().date()

        adjustment = StockAdjustment.objects.create(
            product=product,
            adjustment_type=adjustment_type,
            quantity=quantity,
            reason=reason,
            adjustment_date=adjustment_date
        )

        # Apply the stock change
        adjustment.apply_adjustment()

        messages.success(request, "Stock adjustment applied successfully.")
        return redirect('stock')

  
    products = Product.objects.all()
    return render(request, 'InvApp/adjust_stock.html', {'products': products})

def report_page(request):
    selected_date = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))

    # Fetch orders and stock entries for the selected date
    orders = Order.objects.filter(order_date=selected_date)
    stock_entries = Stock.objects.filter(stock_date=selected_date)

    # Fetch all products
    products = Product.objects.all()

    # Fetch products where current stock is below the reorder level
    low_stock_items = Product.objects.filter(quantity_in_stock__lt=F('reorder_level')).values(
        'name', 'quantity_in_stock', 'reorder_level', 'reorder_quantity'
    )

    context = {
        'selected_date': selected_date,
        'orders': orders,
        'stock_entries': stock_entries,
        'products': products, 
        'low_stock_items': low_stock_items
    }

    return render(request, 'InvApp/report.html', context)