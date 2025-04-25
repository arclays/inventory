from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import datetime, date
from django.views.generic import View
from django.urls import reverse
from .models import Customer, Product, Order,User, Category, Supplier
from django.http import HttpResponse
from django.utils import timezone
from .models import Order, Stock, StockAdjustment, ProductBatch
from decimal import Decimal
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Sum, F,   Q, When, Value, Case,  FloatField,Count , ExpressionWrapper
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, FloatField, FloatField, Subquery, OuterRef, Q
from django.db.models.functions import  TruncMonth
import json
import csv
import logging



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
    stocks = Stock.objects.all()

    category_id = request.GET.get('category', '')
    search_query = request.GET.get('search', '').strip()

    products = Product.objects.all().order_by('-product_id')
    if category_id:
        products = products.filter(category_id=category_id)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(product_id__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        try:
            category_id = request.POST.get('category_id')
            name = request.POST.get('name', '').strip()
            quantity_in_stock = request.POST.get('quantity_in_stock', 0)
            units = request.POST.get('units')
            selling_price = request.POST.get('selling_price', 0)
            reorder_quantity = request.POST.get('reorder_quantity', 0)
            reorder_level = request.POST.get('reorder_level', 0)

            if not category_id:
                messages.error(request, "Category is required!")
                return redirect('product_list')
            
            if not name:
                messages.error(request, "Product name is required!")
                return redirect('product_list')

            if Product.objects.filter(name__iexact=name).exists():
                messages.error(request, f"Product '{name}' already exists!")
                return redirect('product_list')

            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                messages.error(request, "Invalid category selected!")
                return redirect('product_list')

            Product.objects.create(
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

    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = [
            {
                'product_id': product.product_id,
                'name': product.name,
                'category': product.category.name,
                'quantity_in_stock': product.quantity_in_stock,
                'units': product.units,
                'selling_price': product.selling_price,
                'reorder_quantity': product.reorder_quantity,
                'reorder_level': product.reorder_level
            }
            for product in page_obj
        ]
        return JsonResponse({
            'results': data,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page_number': page_obj.number,
            'total_pages': paginator.num_pages
        })

    context = {
        'page_obj': page_obj,
        'stocks': stocks,
        'categories': categories,
        'category_id': category_id,
        'search_query': search_query,
    }
    return render(request, 'InvApp/product_list.html', context)

def product_history(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    combined_activity = []
    
    for batch in product.productbatch_set.all():

        combined_activity.append({
            'date': batch.stock_date,
            'event_type': 'batch',
            'description': f"Batch {batch.batch_sku} added with {batch.initial_quantity} {product.units}",
            'quantity': batch.initial_quantity
        })
    
        orders = product.order_set.all().order_by('-order_date')

    for order in orders:
        combined_activity.append({
            'date': order.order_date,
            'event_type': 'order',
            'user': order.customer,
            'quantity': order.quantity
        })
    
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
    
    paginator = Paginator(combined_activity, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    today = datetime.now()
    sales_labels = []
    sales_data = []
    
    for i in range(11, -1, -1):
        month = today - timedelta(days=30*i)
        sales_labels.append(month.strftime("%b %Y"))
        sales_data.append(0)  
    
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
        'total_cust': total_cust,
    }
    return render(request, 'Invapp/customer_list.html', context)

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
    product = get_object_or_404(Product, product_id=product_id)
    if request.method == 'POST':
        fields = ['name', 'buying_price', 'quantity_in_stock', 'supplier', 'units', 
                  'category', 'selling_price', 'manufacture_date', 'reorder_quantity', 'reorder_level']

        update_data = {field: request.POST.get(field) for field in fields if request.POST.get(field) is not None}

        Product.objects.filter(product_id=product_id).update(**update_data)

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


def get_selling_price(request, product_id):
    try:
        product = Product.objects.get(product_id=product_id)
        return JsonResponse({"selling_price": product.selling_price})
    except Product.DoesNotExist:
        return JsonResponse({"selling_price": 0}, status=404)


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
    
    total_stock_in = 0
    total_stock_out = 0
    total_adjustments_in = 0
    total_adjustments_out = 0
    total_cash_made = 0
    total_quantity_sold = 0
    stock_adjustments= StockAdjustment.objects.count()

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

    total_opening_stock = sum(t['opening_stock'] for t in stock_transactions)
    total_closing_stock = sum(t['closing_stock'] for t in stock_transactions)
    calculated_total_closing = (
        total_opening_stock + 
        total_stock_in + 
        total_adjustments_in - 
        total_stock_out - 
        total_adjustments_out
    )

    orders = Order.objects.filter(order_date=selected_date)
    total_customers = orders.values('customer').distinct().count()
    total_orders = orders.count()
    
    total_cash_made = Order.objects.filter(
        order_date=selected_date
    ).aggregate(total=Sum('final_total'))['total'] or 0
    
    total_quantity_sold = Order.objects.filter(
        order_date=selected_date
    ).aggregate(total=Sum('quantity'))['total'] or 0

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
        'total_opening_stock': total_opening_stock,
        'total_stock_in': total_stock_in,
        'total_stock_out': total_stock_out,
        'total_adjustments_in': total_adjustments_in,
        'total_adjustments_out': total_adjustments_out,
        'total_closing_stock': total_closing_stock,
        'calculated_total_closing': calculated_total_closing,
        'total_customers': total_customers,
        'total_orders': total_orders,
        'stock_adjustments':stock_adjustments,
        'total_cash_made': total_cash_made,
        'total_quantity_sold': total_quantity_sold,
        'all_zeros': all_zeros,
    }

    return render(request, 'InvApp/report.html', context)


@login_required
def home_view(request):
    selected_date = request.GET.get('orderDate', str(date.today()))
    selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()

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
        product_batches =ProductBatch.objects.all()
        stock_adjustments_qs = StockAdjustment.objects.all().select_related('product')

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
            'product_batches':product_batches,
            'start_date': start_date,
            'end_date': end_date,
        }

        return render(request, 'InvApp/adjust.html', context)


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



logger = logging.getLogger(__name__)

def report_analysis(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    twelve_months_ago = today - timedelta(days=365)

    latest_batch = ProductBatch.objects.filter(product=OuterRef('product')).order_by('-stock_date')[:1]
    buying_price_subquery = Subquery(latest_batch.values('buying_price')[:1], output_field=FloatField())

    batch_values = ProductBatch.objects.values(
        'product__name', 'product__product_id', 'product__category__name', 'buying_price'
    ).annotate(
        quantity=Sum('initial_quantity'),
        total_value=Sum(
            ExpressionWrapper(
                F('initial_quantity') * F('buying_price'),
                output_field=FloatField()
            )
        ),
    ).order_by('-total_value')

    total_inventory_value = sum(item['total_value'] for item in batch_values if item['total_value']) or 0.0

    inventory_data = [
        {
            'name': item['product__name'],
            'sku': item['product__product_id'],
            'quantity_in_stock': item['quantity'],
            'unit_cost': item['buying_price'],
            'total_value': item['total_value'],
            'percentage': round((item['total_value'] / total_inventory_value) * 100, 2) if total_inventory_value else 0,
            'category__name': item['product__category__name']
        }
        for item in batch_values
    ]

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
            Sum('reorder_quantity'),
            output_field=FloatField()
        )
    )['avg_reorder'] or 0.0

    
    category_data = Category.objects.annotate(
        product_count=Count('product'),
        batch_count=Count('product__productbatch'),
        total_quantity=Sum('product__productbatch__initial_quantity'),
        total_value=Sum(
            ExpressionWrapper(
                F('product__productbatch__initial_quantity') * F('product__productbatch__buying_price'),
                output_field=FloatField()
            )
        ),
        percentage=ExpressionWrapper(
            Sum(
                ExpressionWrapper(
                    F('product__productbatch__initial_quantity') * F('product__productbatch__buying_price'),
                    output_field=FloatField()
                )
            ) * 100.0 / (total_inventory_value if total_inventory_value else 1),
            output_field=FloatField()
        )
    ).values(
        'id', 'name', 'product_count', 'batch_count',
        'total_quantity', 'total_value', 'percentage'
    ).order_by('-total_value')

    category_data = [
        {
            'id': item['id'],
            'name': item['name'],
            'product_count': item['product_count'],
            'batch_count': item['batch_count'],
            'total_quantity': item['total_quantity'] or 0,
            'total_value': item['total_value'] or 0.0,
            'percentage': item['percentage'] or 0.0
        }
        for item in category_data
    ]

    inventory_trend = ProductBatch.objects.filter(
        stock_date__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('stock_date')
    ).values('month').annotate(
        total_value=Sum(
            ExpressionWrapper(
                F('initial_quantity') * F('buying_price'),
                output_field=FloatField()
            )
        )
    ).order_by('month')

    inventory_trend_labels = []
    inventory_trend_values = []
    current_month = twelve_months_ago.replace(day=1)
    while current_month <= today:
        month_data = next(
            (item for item in inventory_trend if item['month'] and item['month'].month == current_month.month and item['month'].year == current_month.year),
            {'total_value': 0.0}
        )
        inventory_trend_labels.append(current_month.strftime('%b %Y'))
        inventory_trend_values.append(float(month_data['total_value'] or 0.0))
        current_month = (current_month + timedelta(days=32)).replace(day=1)

    
    orders = Order.objects.filter(
        order_date__gte=thirty_days_ago,
        payment_method__in=["cash", "credit_card", "mobile_money", "bank_transfer"]
    )

    total_revenue = orders.aggregate(
        total=Sum('total_price', output_field=FloatField())
    )['total'] or 0.0

    
    previous_period_start = thirty_days_ago - timedelta(days=30)
    previous_period_orders = Order.objects.filter(
        order_date__gte=previous_period_start,
        order_date__lt=thirty_days_ago,
        payment_method__in=["cash", "credit_card", "mobile_money", "bank_transfer"]
    )
    previous_revenue = previous_period_orders.aggregate(
        total=Sum('total_price', output_field=FloatField())
    )['total'] or 0.0
    revenue_growth = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue else 0.0

   
    total_cogs = orders.annotate(
        buying_price=buying_price_subquery
    ).aggregate(
        total_cost=Sum(
            ExpressionWrapper(
                F('quantity') * F('buying_price'),
                output_field=FloatField()
            )
        )
    )['total_cost'] or 0.0
    gross_profit = total_revenue - total_cogs
    gross_margin = (gross_profit / total_revenue * 100) if total_revenue else 0.0

    # Average Order  and Total Orders
    total_orders = orders.count()
    avg_order_value = (total_revenue / total_orders) if total_orders else 0.0

    # Return Rate and Total Returns 
    total_returns = 0.0
    return_rate = 0.0

    # Top-selling products
    try:
        top_selling = orders.annotate(
            buying_price=buying_price_subquery
        ).values(
            'product__name', 'product__category__name'
        ).annotate(
            qty=Sum('quantity'),
            revenue=Sum('total_price', output_field=FloatField()),
            cost=Sum(
                ExpressionWrapper(
                    F('quantity') * F('buying_price'),
                    output_field=FloatField()
                )
            )
        ).annotate(
            profit=ExpressionWrapper(
                F('revenue') - F('cost'),
                output_field=FloatField()
            ),
            margin=ExpressionWrapper(
                (F('revenue') - F('cost')) / F('revenue') * 100,
                output_field=FloatField()
            )
        ).order_by('-revenue')[:10]

        logger.debug("Top Selling Raw: %s", list(top_selling))

        top_selling_processed = [
            {
                'product__name': item['product__name'],
                'product__category__name': item['product__category__name'],
                'qty': item['qty'] or 0,
                'revenue': item['revenue'] or 0.0,
                'cost': item['cost'] or 0.0,
                'profit': item['profit'] or 0.0,
                'margin': item['margin'] or 0.0 if item['revenue'] else 0.0
            }
            for item in top_selling
        ]

        logger.debug("Top Selling Processed: %s", top_selling_processed)
    except Exception as e:
        logger.error("Error in top_selling query: %s", str(e))
        top_selling_processed = []
        top_product_names = []
        top_product_values = []
        top5_revenue = 0.0
        top5_percentage = 0.0
        other_percentage = 0.0
    else:
        # Sales Distribution
        top5_revenue = sum(item['revenue'] for item in top_selling_processed[:5] if item['revenue'] is not None) or 0.0
        top5_percentage = (top5_revenue / total_revenue * 100) if total_revenue else 0.0
        other_percentage = 100.0 - top5_percentage if total_revenue else 0.0

        top_product_names = [item['product__name'] for item in top_selling_processed]
        top_product_values = [item['revenue'] for item in top_selling_processed]

    # Monthly Sales Trend
    monthly_sales = Order.objects.filter(
        order_date__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('order_date'),
        buying_price=buying_price_subquery
    ).values('month').annotate(
        total_sales=Sum('total_price', output_field=FloatField()),
        order_count=Count('id'),
        cogs=Sum(
            ExpressionWrapper(
                F('quantity') * F('buying_price'),
                output_field=FloatField()
            )
        )
    ).annotate(
        net_sales=F('total_sales'),
        gross_profit=ExpressionWrapper(
            F('total_sales') - F('cogs'),
            output_field=FloatField()
        ),
        margin=ExpressionWrapper(
            (F('total_sales') - F('cogs')) / F('total_sales') * 100,
            output_field=FloatField()
        )
    ).order_by('month')

    # Post-process monthly_sales to handle null values
    monthly_sales_processed = [
        {
            'month': item['month'],
            'total_sales': item['total_sales'] or 0.0,
            'order_count': item['order_count'],
            'cogs': item['cogs'] or 0.0,
            'net_sales': item['net_sales'] or 0.0,
            'gross_profit': item['gross_profit'] or 0.0,
            'margin': item['margin'] or 0.0 if item['total_sales'] else 0.0
        }
        for item in monthly_sales
    ]

    monthly_labels = []
    monthly_sales_data = []
    monthly_profit_data = []
    current_month = twelve_months_ago.replace(day=1)
    while current_month <= today:
        month_data = next(
            (item for item in monthly_sales_processed if item['month'] and item['month'].month == current_month.month and item['month'].year == current_month.year),
            {
                'total_sales': 0.0,
                'gross_profit': 0.0,
                'order_count': 0,
                'net_sales': 0.0,
                'cogs': 0.0,
                'margin': 0.0
            }
        )
        monthly_labels.append(current_month.strftime('%b %Y'))
        monthly_sales_data.append(float(month_data['total_sales']))
        monthly_profit_data.append(float(month_data['gross_profit']))
        current_month = (current_month + timedelta(days=32)).replace(day=1)

    # Sales Trend Comparison
    current_period_sales = total_revenue
    previous_period_sales = previous_revenue
    sales_change = revenue_growth
    current_period_units = orders.aggregate(total=Sum('quantity'))['total'] or 0
    previous_period_units = previous_period_orders.aggregate(total=Sum('quantity'))['total'] or 0
    units_change = ((current_period_units - previous_period_units) / previous_period_units * 100) if previous_period_units else 0.0
    current_avg_order = avg_order_value
    previous_avg_order = (previous_revenue / previous_period_orders.count()) if previous_period_orders.count() else 0.0
    aov_change = ((current_avg_order - previous_avg_order) / previous_avg_order * 100) if previous_avg_order else 0.0

    # Daily Transaction Report
    daily_sales = orders.annotate(
        buying_price=buying_price_subquery
    ).values(
        'order_date', 'id', 'product__name', 'quantity', 'total_price'
    ).annotate(
        date=F('order_date'),
        order_id=F('id'),
        product=F('product__name'),
        unit_price=ExpressionWrapper(
            F('total_price') / F('quantity'),
            output_field=FloatField()
        ),
        cost=ExpressionWrapper(
            F('quantity') * F('buying_price'),
            output_field=FloatField()
        ),
        revenue=F('total_price'),
        profit=ExpressionWrapper(
            F('total_price') - F('cost'),
            output_field=FloatField()
        )
    ).order_by('-order_date')

    total_units = orders.aggregate(total=Sum('quantity'))['total'] or 0
    total_cost = total_cogs
    total_profit = gross_profit

    # Profitability Analysis
    profitability_matrix = orders.annotate(
        buying_price=buying_price_subquery
    ).values(
        'product__name'
    ).annotate(
        revenue=Sum('total_price', output_field=FloatField()),
        cogs=Sum(
            ExpressionWrapper(
                F('quantity') * F('buying_price'),
                output_field=FloatField()
            )
        ),
        volume=Sum('quantity')
    ).annotate(
        profit=ExpressionWrapper(
            F('revenue') - F('cogs'),
            output_field=FloatField()
        ),
        margin=ExpressionWrapper(
            (F('revenue') - F('cogs')) / F('revenue') * 100,
            output_field=FloatField()
        ),
        contribution=ExpressionWrapper(
            (F('revenue') - F('cogs')) * 100 /
            Case(
                When(cogs=0, then=Value(1)),
                default=F('cogs'),
                output_field=FloatField()
            ),
            output_field=FloatField()
        )
    ).order_by('-profit')

    # Category Profitability
    category_profit = orders.annotate(
        buying_price=buying_price_subquery
    ).values(
        'product__category__name'
    ).annotate(
        revenue=Sum('total_price', output_field=FloatField()),
        cogs=Sum(
            ExpressionWrapper(
                F('quantity') * F('buying_price'),
                output_field=FloatField()
            )
        )
    ).annotate(
        profit=ExpressionWrapper(
            F('revenue') - F('cogs'),
            output_field=FloatField()
        ),
        margin=ExpressionWrapper(
            (F('revenue') - F('cogs')) / F('revenue') * 100,
            output_field=FloatField()
        )
    ).order_by('-profit')

    # Post-process category_profit to handle null values
    category_profit = [
        {
            'product__category__name': item['product__category__name'],
            'revenue': item['revenue'] or 0.0,
            'cogs': item['cogs'] or 0.0,
            'profit': item['profit'] or 0.0,
            'margin': item['margin'] or 0.0 if item['revenue'] else 0.0
        }
        for item in category_profit
    ]

    # Expiry check
    near_expiry = ProductBatch.objects.filter(
        expiry_date__range=[today, today + timedelta(days=365)]
    ).select_related('product').values(
        'product__name', 'expiry_date', 'initial_quantity'
    ).order_by('expiry_date')

    context = {
        # Summary Cards
        'total_revenue': total_revenue,
        'revenue_growth': round(revenue_growth, 2),
        'gross_profit': gross_profit,
        'gross_margin': round(gross_margin, 2),
        'avg_order_value': avg_order_value,
        'total_orders': total_orders,
        'return_rate': round(return_rate, 2),
        'total_returns': total_returns,

        # Inventory Data
        'default_start_date': thirty_days_ago,
        'default_end_date': today,
        'total_inventory_value': total_inventory_value,
        'total_sales': total_revenue,
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

        # Top Selling
        'top_selling': top_selling_processed,
        'top_product_names': json.dumps(top_product_names),
        'top_product_values': top_product_values,
        'top5_percentage': round(top5_percentage, 2),
        'other_percentage': round(other_percentage, 2),

        # Monthly Sales Trend
        'monthly_sales': monthly_sales_processed,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_sales_data': monthly_sales_data,
        'monthly_profit_data': monthly_profit_data,
        'current_period_sales': total_revenue,
        'previous_period_sales': previous_revenue,
        'sales_change': round(sales_change, 2),
        'current_period_units': current_period_units,
        'previous_period_units': previous_period_units,
        'units_change': round(units_change, 2),
        'current_avg_order': current_avg_order,
        'previous_avg_order': previous_avg_order,
        'aov_change': round(aov_change, 2),

        # Daily Sales
        'daily_sales': daily_sales,
        'total_units': total_units,
        'total_cost': total_cost,
        'total_revenue': total_revenue,
        'total_profit': total_profit,

        # Profitability
        'profitability_matrix': profitability_matrix,
        'category_profit': category_profit,

        # Expiry
        'near_expiry': near_expiry,
        'current_date': today.strftime("%Y-%m-%d"),
        'report_range': f"{thirty_days_ago.strftime('%b %d')} - {today.strftime('%b %d')}"
    }

    return render(request, 'InvApp/report_analysis.html', context)




logger = logging.getLogger(__name__)

def order_page(request):
    today = timezone.now().date()
    selected_date = request.GET.get('orderDate', today.strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        selected_date = today

    # Filters
    customer_id = request.GET.get('customer')
    status = request.GET.get('status')
    payment_method = request.GET.get('payment_method')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', '-order_date')  # Default: newest first
    page_size = int(request.GET.get('page_size', 10))  # Default: 10 per page

    # Base queryset
    orders = Order.objects.select_related('customer', 'product', 'batch_sku')

    # Apply date filter
    orders = orders.filter(order_date=selected_date)

    # Apply customer filter
    if customer_id:
        orders = orders.filter(customer_id=customer_id)

    # Apply status filter
    if status:
        orders = orders.filter(status=status)

    # Apply payment method filter
    if payment_method:
        orders = orders.filter(payment_method=payment_method)

    # Apply search
    if search_query:
        orders = orders.filter(
            Q(customer__name__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    # Apply sorting
    orders = orders.order_by(sort_by)

    # Summary metrics
    total_customers = orders.values('customer').distinct().count()
    total_orders = orders.count()
    total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0
    total_cash_made = orders.aggregate(total=Sum('final_total'))['total'] or 0.0

    # Pagination
    paginator = Paginator(orders, page_size)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'orders': page_obj,
        'page_obj': page_obj,
        'selected_date': selected_date.strftime('%Y-%m-%d'),
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_quantity': total_quantity,
        'total_cash_made': total_cash_made,
        'customers': Customer.objects.all(),
        'products': Product.objects.all(),
        'product_batches': ProductBatch.objects.all(),
        'status_choices': ['pending', 'completed', 'cancelled'],
        'payment_methods': ['cash', 'credit_card', 'mobile_money', 'bank_transfer'],
        'page_sizes': [10, 25, 50, 100],
        'current_page_size': page_size,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    return render(request, 'InvApp/order_page.html', context)

def place_order(request):
    if request.method == 'POST':
        try:
            customer_id = request.POST.get('orderCustomer')
            order_date = request.POST.get('orderDate')
            payment_method = request.POST.get('paymentMethod')
            products = request.POST.getlist('products[]')
            quantities = request.POST.getlist('orderQuantity[]')
            units = request.POST.getlist('units[]')
            price_per_units = request.POST.getlist('price_per_unit[]')
            discounts = request.POST.getlist('productDiscount[]')
            batch_skus = request.POST.getlist('batch_sku[]')

            customer = Customer.objects.get(id=customer_id)
            order_date = datetime.strptime(order_date, '%Y-%m-%d').date()

            for i in range(len(products)):
                product = Product.objects.get(product_id=products[i])
                quantity = int(quantities[i])
                discount = float(discounts[i]) if discounts[i] else 0.0
                price_per_unit = float(price_per_units[i])
                total_price = quantity * price_per_unit
                final_total = total_price * (1 - discount / 100)

                # Update inventory
                if product.quantity_in_stock < quantity:
                    messages.error(request, f"Insufficient stock for {product.name}")
                    return redirect('order_page')
                product.quantity_in_stock -= quantity
                product.save()

                # Handle batch
                batch_sku = None
                if batch_skus[i]:
                    batch_sku = ProductBatch.objects.get(id=batch_skus[i])
                    if batch_sku.initial_quantity < quantity:
                        messages.error(request, f"Insufficient batch quantity for {batch_sku.batch_sku}")
                        return redirect('order_page')
                    batch_sku.initial_quantity -= quantity
                    batch_sku.save()

                # Create order
                Order.objects.create(
                    customer=customer,
                    product=product,
                    batch_sku=batch_sku,
                    quantity=quantity,
                    units=units[i],
                    price_per_unit=price_per_unit,
                    total_price=total_price,
                    payment_method=payment_method,
                    discount=discount,
                    final_total=final_total,
                    order_date=order_date,
                    status='completed'
                )

            messages.success(request, "Order placed successfully!")
            return redirect('order_page')
        except Exception as e:
            logger.error("Error placing order: %s", str(e))
            messages.error(request, f"Error placing order: {str(e)}")
            return redirect('order_page')
    return redirect('order_page')





class BulkUpdateOrdersView(View):
    def post(self, request):
        order_ids = request.POST.getlist('order_ids')
        action = request.POST.get('action')
        
        if not order_ids:
            messages.error(request, 'No orders selected.')
            return redirect('orders_list')
        
        if action == 'update_status':
            new_status = request.POST.get('new_status')
            if not new_status:
                messages.error(request, 'No status selected.')
                return redirect('orders_list')
            
            # Update orders status
            updated_count = Order.objects.filter(id__in=order_ids).update(status=new_status)
            messages.success(request, f'Updated status for {updated_count} order(s) to {dict(Order.STATUS_CHOICES).get(new_status, new_status)}.')
        
        elif action == 'delete':
            # Delete orders
            deleted_count, _ = Order.objects.filter(id__in=order_ids).delete()
            messages.success(request, f'Successfully deleted {deleted_count} order(s).')
        
        else:
            messages.error(request, 'Invalid action selected.')
        
        return redirect('orders_list')

def export_orders_csv(request):
    selected_date = request.GET.get('orderDate', timezone.now().date().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()

    orders = Order.objects.filter(order_date=selected_date).select_related('customer', 'product', 'batch_sku')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="orders_{selected_date}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Order ID', 'Customer', 'Product', 'Batch SKU', 'Quantity', 'Units',
        'Price per Unit', 'Total Price', 'Payment Method', 'Discount (%)',
        'Final Total', 'Order Date', 'Status'
    ])

    for order in orders:
        writer.writerow([
            order.id,
            order.customer.name,
            order.product.name,
            order.batch_sku.batch_sku if order.batch_sku else 'N/A',
            order.quantity,
            order.units,
            order.price_per_unit,
            order.total_price,
            order.payment_method,
            order.discount,
            order.final_total,
            order.order_date,
            order.status
        ])

    return response



def home_view(request):
    today = timezone.now().date()
    default_start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    default_end_date = today.strftime('%Y-%m-%d')

    # Filters
    start_date = request.GET.get('start_date', default_start_date)
    end_date = request.GET.get('end_date', default_end_date)
    category_id = request.GET.get('category')
    customer_id = request.GET.get('customer')
    search_query = request.GET.get('search', '')
    page_size = int(request.GET.get('page_size', 5))  # Default: 5 per table

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = today - timedelta(days=30)
        end_date = today

    # Subquery for buying_price
    latest_batch = ProductBatch.objects.filter(product=OuterRef('product')).order_by('-stock_date')[:1]
    buying_price_subquery = Subquery(latest_batch.values('buying_price')[:1], output_field=FloatField())
    stock_adjustments= StockAdjustment.objects.count()

    # Summary Metrics
    orders = Order.objects.filter(order_date__range=[start_date, end_date])
    if category_id:
        orders = orders.filter(product__category_id=category_id)
    if customer_id:
        orders = orders.filter(customer_id=customer_id)
    if search_query:
        orders = orders.filter(
            Q(customer__name__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(id__icontains=search_query)
        )

    total_orders = orders.count()
    total_customers = orders.values('customer').distinct().count()
    total_cash_made = orders.aggregate(total=Sum('final_total'))['total'] or 0.0

    # Stock Metrics
    total_stock_in = ProductBatch.objects.filter(
        stock_date__range=[start_date, end_date]
    ).aggregate(total=Sum('initial_quantity'))['total'] or 0
    total_products = Product.objects.count()
    categories = Category.objects.count()
    
    # Low Stock Items
    critical_threshold = 0.2
    low_stock_items = Product.objects.annotate(
        critical_level=F('reorder_level') * critical_threshold
    ).filter(quantity_in_stock__lt=F('reorder_level'))
    if search_query:
        low_stock_items = low_stock_items.filter(name__icontains=search_query)
    if category_id:
        low_stock_items = low_stock_items.filter(category_id=category_id)
    low_stock_count = low_stock_items.count()

    # Adjustments
    average_adjustments = ProductBatch.objects.filter(
        stock_date__range=[start_date, end_date]
    ).aggregate(avg=Sum('initial_quantity'))['avg'] or 0

    # Recent Orders
    recent_orders = orders.select_related('batch_sku').order_by('-order_date')[:10]
    
    # Paginate Tables
    low_stock_paginator = Paginator(low_stock_items, page_size)
    orders_paginator = Paginator(recent_orders, page_size)
    low_stock_page = request.GET.get('low_stock_page')
    orders_page = request.GET.get('orders_page')
    low_stock_page_obj = low_stock_paginator.get_page(low_stock_page)
    orders_page_obj = orders_paginator.get_page(orders_page)

    # Sales Chart Data
    monthly_sales = orders.annotate(
        month=TruncMonth('order_date'),
        buying_price=buying_price_subquery
    ).values('month').annotate(
        total_sales=Sum('final_total', output_field=FloatField()),
        total_profit=Sum(
            ExpressionWrapper(
                F('final_total') - (F('quantity') * F('buying_price')),
                output_field=FloatField()
            )
        )
    ).order_by('month')

    sales_labels = []
    sales_data = []
    profit_data = []
    current_month = (start_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    while current_month <= end_date:
        month_data = next(
            (item for item in monthly_sales if item['month'] and item['month'].month == current_month.month and item['month'].year == current_month.year),
            {'total_sales': 0.0, 'total_profit': 0.0}
        )
        sales_labels.append(current_month.strftime('%b %Y'))
        sales_data.append(float(month_data['total_sales']))
        profit_data.append(float(month_data['total_profit']))
        current_month = (current_month + timedelta(days=32)).replace(day=1)

    # Stock Chart Data
    stock_trend = ProductBatch.objects.filter(
        stock_date__range=[start_date, end_date]
    ).annotate(
        month=TruncMonth('stock_date')
    ).values('month').annotate(
        total_stock=Sum('initial_quantity'),
        total_value=Sum(
            ExpressionWrapper(
                F('initial_quantity') * F('buying_price'),
                output_field=FloatField()
            )
        )
    ).order_by('month')

    stock_labels = []
    stock_data = []
    stock_value_data = []
    current_month = (start_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    while current_month <= end_date:
        month_data = next(
            (item for item in stock_trend if item['month'] and item['month'].month == current_month.month and item['month'].year == current_month.year),
            {'total_stock': 0, 'total_value': 0.0}
        )
        stock_labels.append(current_month.strftime('%b %Y'))
        stock_data.append(int(month_data['total_stock']))
        stock_value_data.append(float(month_data['total_value']))
        current_month = (current_month + timedelta(days=32)).replace(day=1)

    context = {
        'total_orders': total_orders,
        'total_customers': total_customers,
        'total_stock_in': total_stock_in,
        'low_stock_count': low_stock_count,
        'total_products': total_products,
        'stock_adjustments':stock_adjustments,
        'categories': categories,
        'average_adjustments': round(average_adjustments),
        'total_cash_made': total_cash_made,
        'recent_orders': orders_page_obj,
        'low_stock_items': low_stock_page_obj,
        'orders_page_obj': orders_page_obj,
        'low_stock_page_obj': low_stock_page_obj,
        'sales_labels': json.dumps(sales_labels),
        'sales_data': json.dumps(sales_data),
        'profit_data': json.dumps(profit_data),
        'stock_labels': json.dumps(stock_labels),
        'stock_data': json.dumps(stock_data),
        'stock_value_data': json.dumps(stock_value_data),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'categories_list': Category.objects.all(),
        'customers': Customer.objects.all(),
        'search_query': search_query,
        'category_id': category_id,
        'customer_id': customer_id,
        'page_size': page_size,
        'page_sizes': [5, 10, 20],
    }
    return render(request, 'InvApp/home.html', context)


def export_dashboard_csv(request, table_type):
    start_date = request.GET.get('start_date', (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', timezone.now().date().strftime('%Y-%m-%d'))
    category_id = request.GET.get('category')
    customer_id = request.GET.get('customer')
    search_query = request.GET.get('search', '')

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = timezone.now().date() - timedelta(days=30)
        end_date = timezone.now().date()

    response = HttpResponse(content_type='text/csv')
    if table_type == 'orders':
        response['Content-Disposition'] = f'attachment; filename="recent_orders_{start_date}_to_{end_date}.csv"'
        orders = Order.objects.filter(order_date__range=[start_date, end_date]).select_related('customer', 'product', 'batch_sku')
        
        # Apply filters
        if category_id:
            orders = orders.filter(product__category_id=category_id)
        if customer_id:
            orders = orders.filter(customer_id=customer_id)
        if search_query:
            orders = orders.filter(
                Q(customer__name__icontains=search_query) |
                Q(product__name__icontains=search_query) |
                Q(id__icontains=search_query)
            )

        # Check if orders exist
        if not orders.exists():
            messages.warning(request, "No orders found for the selected filters.")
            return HttpResponse(status=204)  # No content

        writer = csv.writer(response)
        writer.writerow([
            'Order ID', 'Customer', 'Product', 'Batch SKU', 'Quantity', 'Units',
            'Price per Unit', 'Total Price', 'Payment Method', 'Discount (%)',
            'Final Total', 'Order Date', 'Status'
        ])
        for order in orders:
            writer.writerow([
                order.id,
                order.customer.name,
                order.product.name,
                order.batch_sku.batch_sku if order.batch_sku else 'N/A',
                order.quantity,
                order.units,
                order.price_per_unit,
                order.total_price,
                order.payment_method,
                order.discount,
                order.final_total,
                order.order_date,
                order.status
            ])
        messages.success(request, "Orders exported successfully.")
    elif table_type == 'low_stock':
        # Existing low stock export logic (unchanged for brevity)
        response['Content-Disposition'] = f'attachment; filename="low_stock_items_{start_date}_to_{end_date}.csv"'
        low_stock_items = Product.objects.annotate(
            critical_level=F('reorder_level') * 0.2
        ).filter(quantity_in_stock__lt=F('reorder_level'))
        if category_id:
            low_stock_items = low_stock_items.filter(category_id=category_id)
        if search_query:
            low_stock_items = low_stock_items.filter(name__icontains=search_query)
        
        if not low_stock_items.exists():
            messages.warning(request, "No low stock items found for the selected filters.")
            return HttpResponse(status=204)

        writer = csv.writer(response)
        writer.writerow(['Product', 'Category', 'Current Stock', 'Reorder Level'])
        for item in low_stock_items:
            writer.writerow([
                item.name,
                item.category.name,
                item.quantity_in_stock,
                item.reorder_level
            ])
        messages.success(request, "Low stock items exported successfully.")
    else:
        messages.error(request, "Invalid export type.")
        return HttpResponse(status=400)

    return response
   

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
                product.quantity_in_stock - quantity
                product.save()

                if batch :
                    batch.initial_quantity - quantity
                    batch.save()
                else:
                    batch.initial_quantity < quantity
                    print(f"Product with  {batch} has low stock.")


            except Product.DoesNotExist:
                print(f"Product with ID {product_id} does not exist.")
                continue
            except ProductBatch.DoesNotExist:
                print(f"Batch with ID {batch_id} does not exist.")
                continue

        return redirect('order_page')
