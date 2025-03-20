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
from django.db.models import F, Avg
from django.shortcuts import get_object_or_404

# CRUD
# Home_view
# @login_required
def home_view(request):
    orders = Order.objects.all()
    products = Product.objects.all()
    orders = Order.objects.all()
    stocks = Stock.objects.all()
    low_stock_items = Product.objects.filter(quantity_in_stock__lt=F('reorder_level')).values(
        'name', 'quantity_in_stock','reorder_level','reorder_quantity'
    )
    return render(request, 'Invapp/home.html', {'orders': orders, 'products': products,'stocks': stocks, 'low_stock_items': low_stock_items})


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
    customer = get_object_or_404(Customer, id=customer_id) 
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
    customer = get_object_or_404(Customer, id=customer_id)
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

    paginator = Paginator(orders, 8) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj, 
        'page_obj': page_obj,  
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
        customer_id = request.POST.get('orderCustomer') 
        quantity = request.POST.get('orderQuantity')

        products = request.POST.getlist('products[]')
        order_quantities = request.POST.getlist('orderQuantity[]')
        units = request.POST.getlist('units[]')
        unit_prices = request.POST.getlist('unitPrice[]')
        total_prices = request.POST.getlist('totalPrice[]')


        product_list = []
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

        payment_method = request.POST.get('paymentMethod', 'cash')  
        discount = request.POST.get('discount', '0.00') 
        # Convert discount to float 
        try:
            discount = float(discount)
        except ValueError:
            discount = 0.0 



        # store items
        for item in product_list:
            product_id =item['product_id']
            unit_id = item['unit']
            unit_price = item['unit_price']
            total_price = item['total_price']
            quantity = item['quantity']
            

            product = Product.objects.get(product_id=product_id)
            quantity = int(quantity)
            if quantity <= 0 or quantity > product.quantity_in_stock:
                pass
            else:
                # Create Order 
               Order.objects.create(
                   customer=customer,
                   product=product,
                   quantity=quantity,
                   price_per_unit=unit_price,
                   total_price=total_price,
                   units=unit_id,
                   payment_method=payment_method, 
                   discount=discount,  
)

                # Deduct  stock
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


        product = get_object_or_404(Product, product_id=product_id)  

        initial_stock = product.quantity_in_stock  
        total_stock = int(initial_stock) + int(new_stock ) 

        product.quantity_in_stock = total_stock
        product.save()

        stock = Stock.objects.filter(product=product).first()
        if stock:
            stock.total_stock = total_stock
            stock.save()

        Stock.objects.create(
            product=product,
            initial_stock=initial_stock,
            new_stock=new_stock,
            total_stock=total_stock,  
            stock_date=timezone.now().date(),
            expiry_date=expiry_date,
        )
        return redirect('stock')
    
    total_new_stock = Stock.objects.aggregate(total=Sum('new_stock'))['total'] or 0

    products = Product.objects.all()
    return render(request, 'InvApp/stock.html', {'products': products, 'total_new_stock': total_new_stock})
   

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
            return redirect('report')

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Quantity must be a positive number.")
            return redirect('stock')

        if adjustment_type not in ["add", "subtract"]:
            messages.error(request, "Invalid adjustment type.")
            return redirect('report')

        product = get_object_or_404(Product, product_id=product_id) 

        if adjustment_type == "subtract" and product.quantity_in_stock < quantity:
            messages.error(request, "Not enough stock to subtract.")
            return redirect('stock')

        if adjustment_date:
            try:
                adjustment_date = datetime.strptime(adjustment_date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid date format.")
                return redirect('report')
        else:
            adjustment_date = datetime.today().date()

        adjustment = StockAdjustment.objects.create(
            product=product,
            adjustment_type=adjustment_type,
            quantity=quantity,
            reason=reason,
            adjustment_date=adjustment_date
        )

        # Apply changes
        adjustment.apply_adjustment()
        return redirect('report')

  
    products = Product.objects.all()
    return render(request, 'InvApp/adjust_stock.html', {'products': products})



def report_page(request):
    selected_date = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))

    orders = Order.objects.filter(order_date=selected_date)
    
    # Order 
    total_customers = orders.values('customer').distinct().count()
    total_orders = orders.count()
    total_cash_made = sum(order.final_total for order in orders)
    total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0


    stock_entries = Stock.objects.filter(stock_date=selected_date)
    stock_adjustments = StockAdjustment.objects.filter(adjustment_date=selected_date)
    
    low_stock_items = Product.objects.filter(quantity_in_stock__lt=F('reorder_level')).values(
        'name', 'quantity_in_stock', 'reorder_level', 'reorder_quantity'
    )

    stock_transactions = []
    products = Product.objects.all()

    for product in products:

        stock_in = stock_entries.filter(product=product).aggregate(Sum('new_stock'))['new_stock__sum'] or 0
        stock_out = orders.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
        adjustments = stock_adjustments.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
        opening_stock= stock_entries.filter(product=product).aggregate(Sum('initial_stock'))['initial_stock__sum'] or 0
        closing_stock = product.quantity_in_stock

        total_new_stock = Stock.objects.aggregate(total=Sum('new_stock'))['total'] or 0
        total_adjustments = StockAdjustment.objects.filter(adjustment_type='add').aggregate(total=Sum('quantity'))['total'] or 0
        total_stock_in = total_new_stock + total_adjustments 
        tol_adjustments = StockAdjustment.objects.filter(adjustment_type='subtract').aggregate(total=Sum('quantity'))['total'] or 0
        stock_out = total_quantity + tol_adjustments

        total_quantity_in_stock = Product.objects.aggregate(total_stock=Sum('quantity_in_stock'))['total_stock']

        
        stock_transactions.append({
            'product_name': product.name,
            'stock_in': stock_in,
            'stock_out': stock_out,
            'opening_stock': opening_stock,
            'adjustments': adjustments,
            'closing_stock': closing_stock,
        })

    context = {
        'selected_date': selected_date,
        'orders': orders,
        'stock_entries': stock_entries,
        'stock_out': stock_out,
        'products': products, 
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_cash_made': total_cash_made,
        'total_quantity': total_quantity,
        'stock_adjustments': stock_adjustments,
        'low_stock_items': low_stock_items,
        'stock_transactions': stock_transactions,
        'total_new_stock': total_new_stock,
        'total_quantity_in_stock': total_quantity_in_stock,
        'total_adjustments': total_adjustments,
        'total_stock_in': total_stock_in,
    }


    return render(request, 'InvApp/report.html', context) 

def reorder_alerts(request):

    low_stock_items = Product.objects.filter(quantity_in_stock__lt=F('reorder_level')).values(
        'name', 'quantity_in_stock', 'reorder_level', 'reorder_quantity'
    )
    
    total_products = Product.objects.count()  
    low_stock_count = low_stock_items.count()  
    average_reorder_quantity = Product.objects.aggregate(Avg('reorder_quantity'))['reorder_quantity__avg'] or 0  # Average reorder quantity

  
    return render(request, 'InvApp/reorder.html', {
        'low_stock_items': low_stock_items,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'average_reorder_quantity': average_reorder_quantity,
    })


def stock_adjustments(request):
    stock_adjustments_qs = StockAdjustment.objects.all().select_related('product')
    orders = Order.objects.all().select_related('product')

    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            stock_adjustments_qs = stock_adjustments_qs.filter(adjustment_date__range=(start_date, end_date))
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
            return redirect('stock_adjustments')

    total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0

    stock_entries = Stock.objects.filter(stock_date__range=(start_date, end_date)) if start_date and end_date else Stock.objects.all()
    
    products = Product.objects.all()
    stock_adjustments_list = []

    for product in products:
        stock_in = stock_entries.filter(product=product).aggregate(Sum('new_stock'))['new_stock__sum'] or 0
        stock_out = stock_adjustments_qs.filter(product=product, adjustment_type='subtract').aggregate(Sum('quantity'))['quantity__sum'] or 0
        adjustments = stock_adjustments_qs.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
         
        total_new_stock = Stock.objects.aggregate(total=Sum('new_stock'))['total'] or 0
        total_adjustments = StockAdjustment.objects.filter(adjustment_type='add').aggregate(total=Sum('quantity'))['total'] or 0
        total_stock_in = total_new_stock + total_adjustments 
        tol_adjustments = StockAdjustment.objects.filter(adjustment_type='subtract').aggregate(total=Sum('quantity'))['total'] or 0
        stock_out = total_quantity + tol_adjustments

        stock_adjustments_list.append({
            'product_name': product.name,
            'stock_in': stock_in,
            'stock_out': stock_out,
            'adjustments': adjustments,
        })

    context = {
        'stock_adjustments': stock_adjustments_list,
        'products': products,
        'start_date': start_date,
        'end_date': end_date,
        'total_quantity': total_quantity,
        'total_new_stock': total_new_stock,
        'total_adjustments': total_adjustments,
        'total_stock_in': total_stock_in,
        'tol_adjustments': tol_adjustments,
    }

    return render(request, 'InvApp/adjust.html', context)