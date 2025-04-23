from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import datetime, date
from django.urls import reverse
from .models import Customer, Product, Order,User, Category, Supplier
from django.http import HttpResponse
from django.utils import timezone
from .models import Order, Stock, StockAdjustment, ProductBatch
from decimal import Decimal
from django.db.models import F, Avg
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Sum, F,  Value, Q, When, FloatField,Count , ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth, Coalesce
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, F, Avg, FloatField, Case, When, Value
from django.db.models.functions import Coalesce, TruncMonth
import json





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
    # GET request handling
    categories = Category.objects.all()
    products = Product.objects.all().order_by('-product_id')
    stocks = Stock.objects.all()
    
    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # POST request handling
    if request.method == 'POST':
        try:
            # Get form data
            category_id = request.POST.get('category_id')
            name = request.POST.get('name', '').strip()
            quantity_in_stock = request.POST.get('quantity_in_stock', 0)
            units = request.POST.get('units')
            selling_price = request.POST.get('selling_price', 0)
            reorder_quantity = request.POST.get('reorder_quantity', 0)
            reorder_level = request.POST.get('reorder_level', 0)

            # Validate required fields
            if not category_id:
                messages.error(request, "Category is required!")
                return redirect('product_list')
            
            if not name:
                messages.error(request, "Product name is required!")
                return redirect('product_list')

            # Check for existing product
            if Product.objects.filter(name__iexact=name).exists():
                messages.error(request, f"Product '{name}' already exists!")
                return redirect('product_list')

            # Get category
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                messages.error(request, "Invalid category selected!")
                return redirect('product_list')

            # Create product
            product = Product.objects.create(
                name=name,
                quantity_in_stock=int(quantity_in_stock),
                units=units,
                category=category,
                selling_price=float(selling_price),
                reorder_quantity=int(reorder_quantity),
                reorder_level=int(reorder_level)
            )

            messages.success(request, f"Product '{name}' created successfully!")
            return redirect('product_list')

        except ValueError as e:
            messages.error(request, f"Invalid numeric value: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error creating product: {str(e)}")
        
        return redirect('product_list')

    context = {
        'page_obj': page_obj,
        'stocks': stocks,
        'categories': categories,
    }
    return render(request, 'InvApp/product_list.html', context)


def product_history(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    # Combine all activity
    combined_activity = []
    
    # Add batches
    
    for batch in product.productbatch_set.all():

        combined_activity.append({
            'date': batch.stock_date,
            'event_type': 'batch',
            'description': f"Batch {batch.batch_sku} added with {batch.initial_quantity} {product.units}",
            'quantity': batch.initial_quantity
        })
    
    # Add orders
    orders = product.order_set.all().order_by('-order_date')

    for order in orders:
        combined_activity.append({
            'date': order.order_date,
            'event_type': 'order',
            'user': order.customer,
            'quantity': order.quantity
        })
    
    # Add adjustments
    adjustments = product.stockadjustment_set.all().order_by('-created_at')

    for adj in adjustments:
        combined_activity.append({
            'date': adj.created_at,
            'event_type': 'adjustment',
            'description': f"Stock adjustment: {adj.quantity} {product.units} ({adj.reason})",
            'quantity': adj.quantity
        })
    
    # # Sort by date descending
    # combined_activity.sort(key=lambda x: x['date'], reverse=True)
    
    # Pagination
    paginator = Paginator(combined_activity, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Sales data for chart (last 12 months)
    today = datetime.now()
    sales_labels = []
    sales_data = []
    
    for i in range(11, -1, -1):
        month = today - timedelta(days=30*i)
        sales_labels.append(month.strftime("%b %Y"))
        # You'll need to implement actual sales aggregation here
        sales_data.append(0)  # Replace with actual data
    
    # Batch data for doughnut chart
    batch_labels = [f"Batch {batch.batch_sku}" for batch in product.productbatch_set.all()]
    batch_quantities = [batch.current_quantity for batch in product.productbatch_set.all()]
    
    context = {
        'product': product,
        'combined_activity': page_obj,
        'orders': orders,
        'adjustments': adjustments,
        'sales_labels': sales_labels,
        'sales_data': sales_data,
        'batch_labels': batch_labels,
        'batch_quantities': batch_quantities,
    }
    
    return render(request, 'InvApp/product_history.html', context)


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
    context = {
        'page_obj': page_obj,
        'total_cust' : total_cust,
    }

    return render(request, 'Invapp/customer_list.html', {'context':context })

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

    total_customers = orders.values('customer').distinct().count()
    total_orders = orders.count()
    total_cash_made = orders.aggregate(total=Sum('final_total'))['total'] or 0
    total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0

    customers = Customer.objects.all()
    products = Product.objects.all()
    product_batches = ProductBatch.objects.all()

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
                batch_id = batch_ids[i]

                product = Product.objects.get(product_id=product_id)
                batch = ProductBatch.objects.get(id=batch_id) 
                if not batch:
                    batch = None

              
                # Create Order
                Order.objects.create(
                    customer=customer,
                    product=product,
                    batch_sku = batch,
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

                if batch :
                    batch.current_quantity -= quantity
                    batch.save()
                else:
                    batch.current_quantity < quantity
                    print(f"Product with  {batch} has low stock.")


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
    labels = [product.name for product in products] 
    
    data = [product.quantity_in_stock for product in products] 

    return JsonResponse({'labels': labels, 'data': data})


def report_page(request):
    
    selected_date_str = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    today = date.today()
    
    # Initialize totals
    total_stock_in = 0
    total_stock_out = 0
    total_adjustments_in = 0
    total_adjustments_out = 0
    total_cash_made = 0
    total_quantity_sold = 0

    products = Product.objects.all()
    stock_transactions = []

    for product in products:
        stock_in = Stock.objects.filter(product=product, stock_date=selected_date ).aggregate(total=Sum('new_stock'))['total'] or 0
        stock_out = Order.objects.filter( product=product,order_date=selected_date).aggregate(total=Sum('quantity'))['total'] or 0

        positive_adjustments = StockAdjustment.objects.filter(product=product,created_at__date=selected_date,adjustment_type='add').aggregate(total=Sum('quantity'))['total'] or 0
        negative_adjustments = StockAdjustment.objects.filter(product=product,created_at__date=selected_date,adjustment_type='subtract' ).aggregate(total=Sum('quantity'))['total'] or 0

        net_adjustments = positive_adjustments - negative_adjustments

        opening_stock = product.quantity_in_stock - stock_in - net_adjustments + stock_out
        closing_stock = opening_stock + stock_in + positive_adjustments - stock_out - negative_adjustments

        total_stock_in += stock_in
        total_stock_out += stock_out
        total_adjustments_in += positive_adjustments
        total_adjustments_out += negative_adjustments

        # Add to transactions list
        stock_transactions.append({
            'product_name': product.name,
            'opening_stock': opening_stock,
            'stock_in': stock_in,
            'stock_out': stock_out,
            'positive_adjustments': positive_adjustments,
            'negative_adjustments': negative_adjustments,
            'closing_stock': closing_stock,
            'net_adjustments': net_adjustments
        })

    # Calculate overall totals
    total_opening_stock = sum(t['opening_stock'] for t in stock_transactions)
    total_closing_stock = sum(t['closing_stock'] for t in stock_transactions)
    calculated_total_closing = (
        total_opening_stock + 
        total_stock_in + 
        total_adjustments_in - 
        total_stock_out - 
        total_adjustments_out
    )

    # Additional metrics
    orders = Order.objects.filter(order_date=selected_date)
    total_customers = orders.values('customer').distinct().count()
    total_orders = orders.count()
    
    # Calculate total cash made from sales only
    total_cash_made = Order.objects.filter(
        order_date=selected_date
    ).aggregate(total=Sum('final_total'))['total'] or 0
    
    total_quantity_sold = Order.objects.filter(
        order_date=selected_date
    ).aggregate(total=Sum('quantity'))['total'] or 0

    # Check if all values are zero (for empty report indication)
    all_zeros = all([
        total_opening_stock == 0,
        total_stock_in == 0,
        total_stock_out == 0,
        total_adjustments_in == 0,
        total_adjustments_out == 0,
        total_closing_stock == 0,
        total_cash_made == 0,
        total_quantity_sold == 0
    ])

    context = {
        'selected_date': selected_date_str,
        'orders': orders,
        'products': products,
        'stock_transactions': stock_transactions,
        
        # Stock metrics
        'total_opening_stock': total_opening_stock,
        'total_stock_in': total_stock_in,
        'total_stock_out': total_stock_out,
        'total_adjustments_in': total_adjustments_in,
        'total_adjustments_out': total_adjustments_out,
        'total_closing_stock': total_closing_stock,
        'calculated_total_closing': calculated_total_closing,
        
        # Order metrics
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_cash_made': total_cash_made,
        'total_quantity_sold': total_quantity_sold,
        
        # Flags
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
        batch_id = request.POST.getlist('batch_sku')

        product = Product.objects.get(product_id=product_id)

        if not quantity or not quantity.isdigit():
            messages.error(request, "Invalid quantity.")
            return redirect('stock_adjustments')

        quantity = int(quantity)

        batch = ProductBatch.objects.get(id=batch_id) 
        if not batch:
            batch = None

        
        adjustment = StockAdjustment.objects.create(
            product=product,
            adjustment_type=adjustment_type,
            quantity=quantity,
            reason=reason
        )
        if batch is 'add':
                    batch.current_quantity + quantity
                    batch.save()
        if batch is 'substract':
                    batch.current_quantity - quantity
                    batch.save()
        else:
            print(f"Product with  {batch} has low stock.")

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


def report_analysis(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    twelve_months_ago = today - timedelta(days=365)

    # Total inventory value using batch prices
    batch_values = ProductBatch.objects.values(
    'product__name', 'product__product_id', 'product__category__name'
).annotate(
    quantity=Sum('initial_quantity'),
        total_value=Sum(
            ExpressionWrapper(
                F('initial_quantity ') * F('buying_price'),
                output_field=FloatField()
            )
        ),
    ).order_by('-total_value')

    total_inventory_value = sum(item['total_value'] for item in batch_values if item['total_value'])

    # Add percentage per item
    inventory_data = [
        {
            'name': item['product__name'],
            'sku': item['product__product_id'],
            'quantity_in_stock': item['quantity'],
            'total_value': item['total_value'],
            'percentage': round((item['total_value'] / total_inventory_value) * 100, 2) if total_inventory_value else 0,
            'category__name': item['product__category__name']
        }
        for item in batch_values
    ]

    # Low stock items
    critical_threshold = 0.2
    low_stock_items = Product.objects.annotate(
        critical_level=F('reorder_level') * critical_threshold
    ).filter(quantity_in_stock__lt=F('reorder_level')).values(
        'product_id', 'name', 'quantity_in_stock',
        'reorder_level', 'reorder_quantity', 'critical_level'
    )

    critical_stock_count = low_stock_items.filter(
        quantity_in_stock__lt=F('critical_level')
    ).count()

    total_products = Product.objects.count()
    low_stock_count = low_stock_items.count()
    average_reorder_quantity = Product.objects.aggregate(
    avg_reorder=ExpressionWrapper(
        Coalesce(Sum('reorder_quantity'), 0.0),
        output_field=FloatField()
    )
)['avg_reorder']

    # Category Analysis
    category_data = Category.objects.annotate(
        product_count=Count('product'),
        batch_count=Count('product__productbatch'),
        total_quantity=Coalesce(Sum('product__productbatch__initial_quantity '), 0),
        total_value=Coalesce(
            Sum(
                ExpressionWrapper(
                    F('product__productbatch__initial_quantity ') * F('product__productbatch__buying_price'),
                    output_field=FloatField()
                )
            ),
            0.0
        ),
        percentage=ExpressionWrapper(
            Coalesce(
                Sum(
                    ExpressionWrapper(
                        F('product__productbatch__initial_quantity ') * F('product__productbatch__buying_price'),
                        output_field=FloatField()
                    )
                ), 0.0
            ) * 100.0 / (total_inventory_value if total_inventory_value else 1),
            output_field=FloatField()
        )
    ).values(
        'id', 'name', 'product_count', 'batch_count',
        'total_quantity', 'total_value', 'percentage'
    ).order_by('-total_value')

    # Top-selling products
    top_selling = Order.objects.filter(
        order_date__gte=thirty_days_ago,
        payment_method__in=["cash", "credit_card", "mobile_money", "bank_transfer"]
    ).values('product__name').annotate(
        qty=Sum('quantity'),
        revenue=Sum('total_price')
    ).order_by('-revenue')[:10]

    # Inventory trend
    inventory_trend = Stock.objects.filter(
        stock_date__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('stock_date')
    ).values('month').annotate(
        total_value=Sum(
            ExpressionWrapper(
                F('product__productbatch__initial_quantity ') * F('product__productbatch__buying_price'),
                output_field=FloatField()
            )
        ),
    ).order_by('month')

    inventory_trend_labels = []
    inventory_trend_values = []

    current_month = twelve_months_ago.replace(day=1)
    while current_month <= today:
        month_data = next(
            (item for item in inventory_trend if item['month'].month == current_month.month and item['month'].year == current_month.year),
            {'total_value': 0}
        )
        inventory_trend_labels.append(current_month.strftime('%b %Y'))
        inventory_trend_values.append(float(month_data['total_value'] or 0))
        current_month = (current_month + timedelta(days=32)).replace(day=1)

    # Expiry check
    near_expiry = ProductBatch.objects.filter(
        expiry_date__range=[today, today + timedelta(days=60)]
    ).select_related('product').values(
        'product__name', 'expiry_date', 'initial_quantity '
    ).order_by('expiry_date')

    context = {
        'default_start_date': thirty_days_ago,
        'default_end_date': today,
        'total_inventory_value': total_inventory_value,
        'total_sales': sum(item['revenue'] for item in top_selling if item['revenue']),
        'low_stock_count': low_stock_count,
        'critical_stock_count': critical_stock_count,
        'expiring_soon_count': near_expiry.count(),

        'inventory': inventory_data,
        'inventory_trend_labels': json.dumps(inventory_trend_labels),
        'inventory_trend_values': inventory_trend_values,

        'low_stock_items': low_stock_items,
        'total_products': total_products,
        'average_reorder_quantity': round(average_reorder_quantity),

        'category': category_data,
        'category_names': json.dumps([cat['name'] for cat in category_data]),
        'category_values': [cat['total_value'] for cat in category_data],

        'top_selling': top_selling,
        'near_expiry': near_expiry,

        'current_date': today.strftime("%Y-%m-%d"),
        'report_range': f"{thirty_days_ago.strftime('%b %d')} - {today.strftime('%b %d')}"
    }

    return render(request, 'InvApp/report_analysis.html', context)

def stock_view(request):
    selected_date = request.GET.get('orderDate', str(date.today()))
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()

    stocks = Stock.objects.filter(stock_date=selected_date).select_related(
        'product', 'product__category').order_by('-stock_date')
    
    products = Product.objects.all().select_related('category')
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    paginator = Paginator(stocks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    def get_stock_alerts():
        alerts = []
        critical_stocks = Stock.objects.filter(
            total_stock__lte=F('product__reorder_level') * Decimal('0.2')
        ).select_related('product')
        
        low_stocks = Stock.objects.filter(
            total_stock__lte=F('product__reorder_level'),
            total_stock__gt=F('product__reorder_level') * Decimal('0.2')
        ).select_related('product')
        
        for stock in critical_stocks:
            alerts.append({
                'product': stock.product,
                'current_stock': stock.total_stock,
                'status': 'critical'
            })
            
        for stock in low_stocks:
            alerts.append({
                'product': stock.product,
                'current_stock': stock.total_stock,
                'status': 'low'
            })
            
        return alerts

    stock_alerts = get_stock_alerts()

    # Chart data
    top_products = Stock.objects.values(
        'product__name'
    ).annotate(
        total=Sum('total_stock')
    ).order_by('-total')[:10]
    
    category_dist = Stock.objects.values(
        'product__category__name'
    ).annotate(
        count=Count('id'),
        total_stock=Sum('total_stock')
    ).order_by('-count')

    # Batch processing
    def annotate_batch_status(queryset):
        today = date.today()
        for batch in queryset:
            if batch.expiry_date:
                days_left = (batch.expiry_date - today).days
                if days_left < 0:
                    batch.expiry_status = 'expired'
                elif days_left <= 30:
                    batch.expiry_status = 'expiring-soon'
                else:
                    batch.expiry_status = 'good'
                batch.days_until_expiry = days_left
            else:
                batch.expiry_status = None
                batch.days_until_expiry = None
        return queryset

    product_batches = annotate_batch_status(ProductBatch.objects.all().select_related('product', 'supplier'))

    total_products = Product.objects.count()
    low_stock_items = len([a for a in stock_alerts if a['status'] == 'low'])
    critical_stock_items = len([a for a in stock_alerts if a['status'] == 'critical'])
    
    total_stock_value = sum(
        stock.total_stock * stock.product.selling_price 
        for stock in Stock.objects.select_related('product')
    )

    context = {
        'stocks': page_obj,
        'products': products,
        'categories': categories,
        'suppliers': suppliers,
        'selected_date': selected_date,
        'page_obj': page_obj,
        'product_batches': product_batches,
        'stock_alerts': stock_alerts,
        'total_products': total_products,
        'low_stock_items': low_stock_items,
        'critical_stock_items': critical_stock_items,
        'total_stock_value': total_stock_value,
        'product_names': [p['product__name'] for p in top_products],
        'stock_levels': [p['total'] for p in top_products],
        'category_names': [c['product__category__name'] for c in category_dist],
        'category_counts': [c['count'] for c in category_dist],
        'category_stock': [c['total_stock'] for c in category_dist],
    }
    
    return render(request, 'InvApp/stock.html', context)


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
            initial_quantity = int(request.POST.get('initial_quantity', 0))
            current_quantity = int(request.POST.get('current_quantity ', 0))
        except ValueError:
            initial_quantity = 0

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
        initial_quantity  = new_stock
        current_quantity = new_stock
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
            initial_quantity=initial_quantity,
            current_quantity=current_quantity,
            expiry_date=expiry_date,
            manufacture_date=manufacture_date,
            stock_date=stock_date,
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

