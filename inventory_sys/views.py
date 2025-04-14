from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import datetime, date
from django.urls import reverse
from .models import Customer, Product, Order,User, Category, Supplier
from django.http import HttpResponse
from django.utils import timezone
from .models import Order, Stock, StockAdjustment, ProductBatch
from django.db.models import F, Avg
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Sum, F,  Value, Case, When, FloatField
from django.db.models.functions import TruncMonth, Coalesce
from django.utils import timezone
from datetime import timedelta
from django.db import transaction




def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            messages.success(request, "Registration successful. You can now log in.")
            return redirect('login')
        except Exception as e:
            messages.error(request, str(e))
            print(f"Redirecting to register due to error: {e}")
            return redirect('register')

    return render(request, 'Invapp/register.html')


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
    return render(request, 'Invapp/logout.html')   


def confirm_logout(request):
    logout(request)
    return redirect('login')


def product_list(request):

    categories = Category.objects.all()
    products = Product.objects.all()
    paginator = Paginator(products, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        print(request.POST)
        product_name = request.POST.get('name')
        quantity_in_stock = request.POST.get('quantity_in_stock')
        units = request.POST.get('units')
        selling_price = request.POST.get('selling_price')
        reorder_quantity = request.POST.get('reorder_quantity')
        reorder_level = request.POST.get('reorder_level')


        if  category_id is None:
            return HttpResponse("Error: Category is required!", status=400)

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return HttpResponse("Error: Category not found!", status=400)
        

        # Create Product
        Product.objects.create(
            name=product_name,
            quantity_in_stock=quantity_in_stock if quantity_in_stock else 0,
            units=units,
            category=category,  # Assign category object
            selling_price=selling_price,
            reorder_quantity=reorder_quantity,
            reorder_level=reorder_level
        )

        messages.success(request, f"Product '{product_name}' added successfully.")
        return redirect('product_list')

    # GET Request
    products = Product.objects.all().order_by('-product_id')
    categories = Category.objects.all()
    product_batches = ProductBatch.objects.all()

    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Map each product to its batches

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'product_batches': product_batches,
    }
    return render(request, 'InvApp/product_list.html', context)


def customer_list(request):
    customers = Customer.objects.all()
    paginator = Paginator(customers, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    total_cust = Customer.objects.count()

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        Customer.objects.create(name=name, email=email, phone=phone, address=address)
        messages.success(request, 'Customer added successfully!')
        return redirect('customer_list')

    return render(request, 'Invapp/customer_list.html', {'page_obj': page_obj, 'total_cust' : total_cust})

def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.email = request.POST.get('email')
        customer.phone = request.POST.get('phone')
        customer.address = request.POST.get('address')
        customer.save()
        messages.success(request, 'Customer edited successfully!')
        return redirect('customer_list')
    return render(request, 'Invapp/customer_edit.html', {'customer': customer})

def customer_confirm_delete(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Customer deleted successfully!')
        return redirect('customer_list')
    return render(request, 'Invapp/customer_confirm_delete.html', {'customer': customer})

def product_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        fields = ['name', 'buying_price', 'quantity_in_stock', 'supplier', 'units', 
                  'category', 'selling_price', 'manufacture_date', 'reorder_quantity', 'reorder_level']

        update_data = {field: request.POST.get(field) for field in fields if request.POST.get(field) is not None}

        Product.objects.filter(id=product_id).update(**update_data)

        messages.success(request, 'Product updated successfully!')
        return redirect('product_list')

    return render(request, 'Invapp/product_update.html', {'product': product})

def product_confirm_delete(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('product_list')
    return render(request, 'Invapp/product_confirm_delete.html', {'product': product})


def order_page(request):
    units = "pcs"
    selected_date = request.GET.get('orderDate', date.today().strftime('%Y-%m-%d'))
    orders = Order.objects.filter(order_date=selected_date).order_by('-order_date')

    # Summary calculations
    total_customers = orders.values('customer').distinct().count()
    total_orders = orders.count()
    total_cash_made = orders.aggregate(total=Sum('final_total'))['total'] or 0
    total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0

    # Get related data
    customers = Customer.objects.all()
    products = Product.objects.all()
    product_batches = ProductBatch.objects.all()

    # Pagination
    paginator = Paginator(orders, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'page_obj': page_obj,
        'product_batches': product_batches,
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




# def place_order(request):
#     if request.method == 'POST':
#         customer_id = request.POST.get('orderCustomer') 
#         products = request.POST.getlist('products[]')
#         order_quantities = request.POST.getlist('orderQuantity[]')
#         units = request.POST.getlist('units[]')
#         price_per_units = request.POST.getlist('price_per_unit[]')
#         total_prices = request.POST.getlist('totalPrice[]')
#         batch_ids = request.POST.getlist('batch_sku[]')
#         discounts = request.POST.getlist('productDiscount[]')
#         order_date = request.POST.get('orderDate', date.today())
#         final_total = request.POST.get('finalTotal', 0)

#         try:
#             customer = Customer.objects.get(id=customer_id)
#         except Customer.DoesNotExist:
#             return redirect('order_page')

#         payment_method = request.POST.get('paymentMethod', 'cash')

#         try:
#             with transaction.atomic():  # <== WRAP ALL WRITES HERE
#                 for i in range(len(products)):
#                     try:
#                         product_id = products[i]
#                         unit_id = units[i]
#                         unit_price = float(price_per_units[i])
#                         total_price = float(total_prices[i])
#                         quantity = int(order_quantities[i])
#                         discount = float(discounts[i])
#                         batch_id = batch_ids[i] if i < len(batch_ids) and batch_ids[i] else None

#                         product = Product.objects.get(product_id=product_id)
#                         batch_instance = ProductBatch.objects.get(id=batch_id) if batch_id else None

#                         # Check stock
#                         if batch_instance and quantity > batch_instance.qty:
#                             print(f"Not enough quantity in batch {batch_instance.batch_sku}")
#                             continue

#                         if quantity > product.quantity_in_stock:
#                             print(f"Not enough stock for product {product.name}")
#                             continue

#                         # Create Order
#                         Order.objects.create(
#                             customer=customer,
#                             product=product,
#                             batch=batch_instance,
#                             quantity=quantity,
#                             price_per_unit=unit_price,
#                             total_price=total_price,
#                             units=unit_id,
#                             payment_method=payment_method,
#                             discount=discount,
#                             order_date=order_date,
#                             final_total=final_total,
#                         )

#                         # Update stock
#                         product.quantity_in_stock -= quantity
#                         product.save()

#                         if batch_instance:
#                             batch_instance.qty -= quantity
#                             batch_instance.save()

#                     except Product.DoesNotExist:
#                         print(f"Product with ID {product_id} does not exist.")
#                         continue
#                     except ProductBatch.DoesNotExist:
#                         print(f"Batch with ID {batch_id} does not exist.")
#                         continue

#         except Exception as e:
#             print(f"Error during order placement: {e}")

#         return redirect('order_page')

    # GET request
    # product_batches = ProductBatch.objects.select_related('product').all().order_by('expiry_date')
    # products = Product.objects.all()
    # customers = Customer.objects.all()

    # return render(request, 'Invapp/order_page.html', {
    #     'product_batches': product_batches,
    #     'products': products,
    #     'customers': customers
    # })



def get_selling_price(request, product_id):
    try:
        product = Product.objects.get(product_id=product_id)
        return JsonResponse({"selling_price": product.selling_price})
    except Product.DoesNotExist:
        return JsonResponse({"selling_price": 0}, status=404)
    

def place_order(request):
    if request.method == 'POST':
        customer_id = request.POST.get('orderCustomer') 
        products = request.POST.getlist('products[]')
        order_quantities = request.POST.getlist('orderQuantity[]')
        units = request.POST.getlist('units[]')
        price_per_units = request.POST.getlist('price_per_unit[]')
        total_prices = request.POST.getlist('totalPrice[]')
        batch_ids = request.POST.getlist('batch_sku[]')
        discounts = request.POST.getlist('productDiscount[]')
        order_date = request.POST.get('orderDate', date.today())
        final_total = request.POST.get('finalTotal', 0)

        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return redirect('order_page')

        payment_method = request.POST.get('paymentMethod', 'cash')  

    

        for i in range(len(products)):
            try:
                product_id = products[i]
                unit_id = units[i]
                unit_price = float(price_per_units[i])
                total_price = float(total_prices[i])
                quantity = int(order_quantities[i])
                discount = float(discounts[i])
                batch_id = batch_ids[i] if i < len(batch_ids) and batch_ids[i] else None

                product = Product.objects.get(product_id=product_id)
                batch_instance = ProductBatch.objects.get(id=batch_id) if batch_id else None

                # Check if there's enough stock
                if batch_instance and quantity > batch_instance.qty:
                    print(f"Not enough quantity in batch {batch_instance.batch_sku}")
                    continue

                if quantity > product.quantity_in_stock:
                    print(f"Not enough stock for product {product.name}")
                    continue

                # Create Order
                Order.objects.create(
                    customer=customer,
                    product=product,
                    batch=batch_instance,
                    quantity=quantity,
                    price_per_unit=unit_price,
                    total_price=total_price,
                    units=unit_id,
                    payment_method=payment_method, 
                    discount=discount, 
                    order_date=order_date,
                    final_total=final_total, 
                )

                # Update stock
                product.quantity_in_stock -= quantity
                product.save()

                if batch_instance:
                    batch_instance.qty -= quantity
                    batch_instance.save()

            except Product.DoesNotExist:
                print(f"Product with ID {product_id} does not exist.")
                continue
            except ProductBatch.DoesNotExist:
                print(f"Batch with ID {batch_id} does not exist.")
                continue

        return redirect('order_page')

    # GET request
    product_batches = ProductBatch.objects.select_related('product').all().order_by('expiry_date')
    products = Product.objects.all()
    customers = Customer.objects.all()

    return render(request, 'Invapp/order_page.html', {
        'product_batches': product_batches,
        'products': products,
        'customers': customers
    })


def get_sales_data(request):
    orders = Order.objects.values('order_date').annotate(total_quantity=Sum('quantity')).order_by('order_date')

    labels = [order['order_date'].strftime('%b') for order in orders]
    data = [order['total_quantity'] for order in orders]

    return JsonResponse({'labels': labels, 'data': data})

def get_stock_data(request):
    products = Product.objects.all()
    labels = [product.product_name for product in products] 
    
    data = [product.quantity_in_stock for product in products] 

    return JsonResponse({'labels': labels, 'data': data})

def stock_view(request):
  
    selected_date = request.GET.get('orderDate', str(date.today()))
    selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    stocks = Stock.objects.filter(stock_date=selected_date)
    
    products = Product.objects.all()
    Suppliers= Supplier.objects.all()
    product_batches = ProductBatch.objects.all()
    product_batches = ProductBatch.objects.select_related('product', 'supplier').all()


    paginator = Paginator(stocks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)                                                                                                                                        

   
    return render(request, 'Invapp/stock.html', {
        'stocks': page_obj,  
        'products': products,
        'suppliers': Suppliers,
        'product_batches': product_batches,
        'selected_date': selected_date,
        'page_obj': page_obj  
    })

def add_stock(request): 
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
       
        product = get_object_or_404(Product, product_id=product_id)

        supplier_id = request.POST.get('supplier_id')

        try:
            new_stock = int(request.POST.get('newStock', 0))
            
        except ValueError:
            new_stock = 0

        batch_sku = request.POST.get('batch_sku')
        try:
            qty = int(request.POST.get('qty', 0))
        except ValueError:
            qty = 0

        try:
            buying_price = float(request.POST.get('buying_price', 0))
        except ValueError:
            buying_price = 0.0
            
        if  supplier_id is None:
            return HttpResponse("Error: Supplier is required!", status=400)
        try:
            supplier = Supplier.objects.get(id=supplier_id)
        except Supplier.DoesNotExist:
            return HttpResponse("Error: Supplier's data Doesn't exist", status=400) 
        

        manufacture_date = request.POST.get('manufacture_date')
        expiry_date = request.POST.get('expiryDate')
        stock_date = request.POST.get('stock_date') or timezone.now().date()

        # Update product stock
        qty = new_stock
        initial_stock = product.quantity_in_stock
        total_stock = product.quantity_in_stock + new_stock
        product.quantity_in_stock = total_stock
        product.save()



        # Create the batch record
        ProductBatch.objects.create(
            product=product,
            supplier=supplier,
            batch_sku=batch_sku,
            buying_price=buying_price,
            qty=qty,
            expiry_date=expiry_date,
            manufacture_date=manufacture_date,
        )

        # Create the stock record
        Stock.objects.create(
            product=product,
            initial_stock=initial_stock,
            new_stock=new_stock,
            total_stock=total_stock,
            stock_date=stock_date,
        )

        return redirect('stock')

    # GET request
    total_new_stock = Stock.objects.aggregate(total=Sum('new_stock'))['total'] or 0
    products = Product.objects.all()
    return render(request, 'InvApp/stock.html', {
        'products': products,
        'total_new_stock': total_new_stock
    })


def report_page(request):
    selected_date = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))
    today = datetime.today().date()
    orders = Order.objects.filter(order_date=selected_date)
    
    # Order 
    stock_adjustments = StockAdjustment.objects.all()
    orders = Order.objects.all()
    total_customers = orders.values('customer').distinct().count()
    total_orders = orders.count()
    total_cash_made = sum(order.final_total for order in orders)
    total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0
    stock_entries = Stock.objects.filter(stock_date=selected_date)
    stock_adjustments = StockAdjustment.objects.filter(created_at=selected_date)
    
    

    stock_transactions = []
    products = Product.objects.all()

    all_zeros = True  # Flag to check if all values are 0

    for product in products:

        stock_in = stock_entries.filter(product=product).aggregate(Sum('new_stock'))['new_stock__sum'] or 0
        stock_out = orders.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
        adjustments = stock_adjustments.filter(product=product).aggregate(Sum('quantity'))['quantity__sum'] or 0
        opening_stock= stock_entries.filter(product=product).aggregate(Sum('initial_stock'))['initial_stock__sum'] or 0
        closing_stock = product.quantity_in_stock

        total_new_stock = Stock.objects.aggregate(total=Sum('new_stock'))['total'] or 0
        total_adjustments = StockAdjustment.objects.filter(adjustment_type='add').aggregate(total=Sum('quantity'))['total'] or 0

        total_quantity_in_stock = Product.objects.aggregate(total_stock=Sum('quantity_in_stock'))['total_stock']
        tol_adjustments = StockAdjustment.objects.filter(adjustment_type='subtract',  created_at__date=today).aggregate(total=Sum('quantity'))['total'] or 0      
        adjust_total  = total_adjustments + tol_adjustments
        total_stock_in = total_new_stock + total_quantity_in_stock 
        average_adjustments =+adjust_total
        stock_out = total_quantity + tol_adjustments
        closing_stock = total_stock_in + stock_out

        if stock_in != 0 or stock_out != 0 or adjustments != 0:
         all_zeros = False

        stock_transactions.append({
            'product_name': product.name,
            'stock_in': stock_in,
            'stock_out': stock_out,
            'opening_stock': opening_stock,
            'adjustments': adjustments,
            'closing_stock': closing_stock,
            'total_quantity': total_quantity,
            'stock_adjustments': stock_adjustments
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
        'stock_transactions': stock_transactions,
        'total_new_stock': total_new_stock,
        'total_quantity_in_stock': total_quantity_in_stock,
        'total_stock_in': total_stock_in,
        'average_adjustments': average_adjustments,
        'tol_adjustments': tol_adjustments,
        'closing_stock': closing_stock,
        'total_quantity_in_stock': total_quantity_in_stock,
        'total_stock_in': total_stock_in,
        'all_zeros': all_zeros, 
    }


    return render(request, 'InvApp/report.html', context) 



@login_required
def home_view(request):
    selected_date = request.GET.get('orderDate', str(date.today()))
    selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()

    # Filter only daily data
    stocks = Stock.objects.filter(stock_date=selected_date)
    orders = Order.objects.filter(order_date=selected_date)
    stock_adjustments = StockAdjustment.objects.filter(created_at__date=selected_date)

    low_stock_items = Product.objects.filter(quantity_in_stock__lt=F('reorder_level')).values(
        'name', 'quantity_in_stock', 'reorder_level', 'reorder_quantity'
    )

    total_orders = orders.count()
    total_customers = orders.values('customer').distinct().count()
    total_cash_made = orders.aggregate(Sum('final_total'))['final_total__sum'] or 0
    total_quantity = orders.aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_products = Product.objects.count()
    low_stock_count = low_stock_items.count()
    categories = Category.objects.count()
    suppliers = Supplier.objects.count()
    batch_sku = ProductBatch.objects.all()

    # Stock Data
    total_new_stock = stocks.aggregate(Sum('new_stock'))['new_stock__sum'] or 0
    total_adjustments = stock_adjustments.filter(adjustment_type='add').aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_stock_in = total_new_stock + total_adjustments

    tol_adjustments = stock_adjustments.filter(adjustment_type='subtract').aggregate(Sum('quantity'))['quantity__sum'] or 0
    stock_out = total_quantity + tol_adjustments
    adjust_total = total_adjustments + tol_adjustments
    average_adjustments = adjust_total

    total_quantity_in_stock = Product.objects.aggregate(Sum('quantity_in_stock'))['quantity_in_stock__sum'] or 0

    recent_orders = orders.order_by('-order_date')[:5].select_related('customer')

    context = {
        'stock_out': stock_out,
        'total_orders': total_orders,
        'categories': categories,
        'batch_sku': batch_sku,
        'suppliers': suppliers,
        'total_customers': total_customers,
        'total_cash_made': total_cash_made,
        'total_quantity': total_quantity,
        'total_products': total_products,
        'total_stock_in': total_stock_in,
        'total_stock_out': tol_adjustments,
        'total_quantity_in_stock': total_quantity_in_stock,
        'low_stock_items': low_stock_items,
        'recent_orders': recent_orders,
        'low_stock_count': low_stock_count,
        'adjust_total': adjust_total,
        'total_new_stock': total_new_stock,
        'total_adjustments': total_adjustments,
        'tol_adjustments': tol_adjustments,
        'average_adjustments': average_adjustments,
        'selected_date': selected_date,
    }

    return render(request, 'InvApp/home.html', context)



def catalog(request):
    if request.method == 'POST':
        if 'add_category' in request.POST:
            name = request.POST.get('category_name')
            description = request.POST.get('category_description')
            category_type = request.POST.get('category_type')

            if name and category_type:
                Category.objects.create(name=name, description=description, category_type=category_type)
                return redirect('catalog')

        elif 'add_supplier' in request.POST:
            name = request.POST.get('supplier_name')
            contact_person = request.POST.get('supplier_contact')
            phone = request.POST.get('supplier_phone')
            email = request.POST.get('supplier_email')

            if name and phone:
                Supplier.objects.create(name=name, contact_person=contact_person, phone=phone, email=email)
                return redirect('catalog')


    categories_list = Category.objects.all().order_by('-id')
    suppliers_list = Supplier.objects.all().order_by('-id')

    category_paginator = Paginator(categories_list, 8)  
    supplier_paginator = Paginator(suppliers_list, 8)

    category_page_number = request.GET.get('category_page')
    supplier_page_number = request.GET.get('supplier_page')

    categories = category_paginator.get_page(category_page_number)
    suppliers = supplier_paginator.get_page(supplier_page_number)

    context = {
        'categories': categories,
        'suppliers': suppliers,
    }

    return render(request, 'InvApp/catalog.html', context)
def stock_adjustments(request):
    selected_date = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        adjustment_type = request.POST.get('adjustment_type')
        quantity = request.POST.get('quantity')
        reason = request.POST.get('reason')

        product = Product.objects.get(product_id=product_id)

        if not quantity or not quantity.isdigit():
            messages.error(request, "Invalid quantity.")
            return redirect('stock_adjustments')

        quantity = int(quantity)

        
        adjustment = StockAdjustment.objects.create(
            product=product,
            adjustment_type=adjustment_type,
            quantity=quantity,
            reason=reason
        )

        if hasattr(adjustment, 'apply_adjustment'):
            adjustment.apply_adjustment()
        else:
            messages.error(request, "Stock adjustment method not found.")
            return redirect('stock_adjustments')

        messages.success(request, "Stock adjusted successfully!")
        return redirect('stock_adjustments')

    else:
        products = Product.objects.all()
        stock_adjustments_qs = StockAdjustment.objects.all().select_related('product')

        # Handle date range filtering using created_at field
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if start_date and end_date:
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                stock_adjustments_qs = stock_adjustments_qs.filter(
                    created_at__date__range=(start_date, end_date)
                )
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
                return redirect('stock_adjustments')
        else:
            today = datetime.today().date()
            stock_adjustments_qs = stock_adjustments_qs.filter(created_at__date=today)
            start_date = end_date = today

        context = {
            'stock_adjustments_list': stock_adjustments_qs,
            'selected_date': selected_date,
            'products': products,
            'start_date': start_date,
            'end_date': end_date,
        }

        return render(request, 'InvApp/adjust.html', context)

def report_anaylsis(request):
    
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    inventory_data = Product.objects.annotate(
        total_value=F('quantity_in_stock') * F('buying_price')
    ).values('name', 'quantity_in_stock', 'buying_price', 'total_value')  
    
    total_inventory_value = sum(item['total_value'] for item in inventory_data)
    
    low_stock_items = Product.objects.filter(quantity_in_stock__lt=F('reorder_level')).values(
        'name', 'quantity_in_stock', 'reorder_level', 'reorder_quantity'
    )
    
    total_products = Product.objects.count()  
    low_stock_count = low_stock_items.count()  
    average_reorder_quantity = Product.objects.aggregate(Avg('reorder_quantity'))['reorder_quantity__avg'] or 0  # Average reorder quantity

    
    category_overview = Category.objects.annotate(
        total_quantity=Coalesce(
            Sum('product__quantity_in_stock'),
            Value(0, output_field=FloatField())
        )
    ).values('name', 'total_quantity')

    top_selling = Order.objects.filter(
        order_date__gte=thirty_days_ago
    ).values('product__name').annotate(
        qty=Sum('quantity'),
        revenue=Sum('total_price')
    ).order_by('-qty')[:10]

    # Monthly Sales & Returns
    # monthly_sales = Order.objects.filter(
    #     order_date__year=today.year
    # ).annotate(
    #     month=TruncMonth('order_date')
    # ).values('month').annotate(
    #     total_sales=Sum(
    #         Case(
    #             When(transaction_type='sale', then='total_price'),
    #             default=Value(0),
    #             output_field=FloatField()
    #         )
    #     ),
    #     total_returns=Sum(
    #         Case(
    #             When(transaction_type='return', then='total_price'),
    #             default=Value(0),
    #             output_field=FloatField()
    #         )
    #     )
    # ).order_by('month')

    daily_sales = Order.objects.filter(
        order_date=today
    ).values('product__name').annotate(
        total=Sum('quantity'),
        revenue=Sum('total_price'),
        gross=Sum(F('total_price') - (F('product__buying_price') * F('quantity')))
    ).order_by('-revenue')

    near_expiry = Stock.objects.filter(
        expiry_date__range=[today, today + timedelta(days=60)]
    ).select_related('product').annotate(
        product_name=F('product__name'),
        quantity=F('total_stock')
    ).values('product_name', 'expiry_date', 'quantity')

    context = {
        # Inventory Section
        'inventory': inventory_data,
        'total_inventory_value': total_inventory_value,
         'low_stock_items': low_stock_items,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'average_reorder_quantity': average_reorder_quantity,
        'categories': category_overview,
        'top_selling': top_selling,
        # 'monthly_sales': monthly_sales,
        'daily_sales': daily_sales,
        'near_expiry': near_expiry,
        'current_date': today.strftime("%Y-%m-%d"),
        'report_range': f"{thirty_days_ago.strftime('%b %d')} - {today.strftime('%b %d')}"
    }
    
    return render(request, 'InvApp/report_anaylsis.html', context)
