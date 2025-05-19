from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.decorators import login_required
from django.db.models.functions import ExtractDay
from django.db import models
from django.db.models.functions import TruncMonth, TruncYear
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.core.exceptions import EmptyResultSet
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import transaction
from datetime import datetime, date
from django.views.generic import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import DecimalField
from .forms import CustomerForm, ProductForm,AddStockForm ,PlaceOrderForm
from .utils import export_csv
from django.urls import reverse
from .models import Customer, Product, Order, Category, Supplier
from django.http import HttpResponse
from django.utils import timezone
from .models import Order, Stock, StockAdjustment, ProductBatch
from .forms import StockAdjustmentForm, DateRangeForm, OrderFilterForm, BulkUpdateOrdersForm
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from django.http import JsonResponse
from django.db.models import Sum, F,   Q, When, Value, Case,  FloatField,Count , ExpressionWrapper, CharField, IntegerField
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.contrib.auth.models import User
from .forms import UserProfileForm
from datetime import timedelta
from django.db.models import Sum, Count, FloatField, FloatField, Subquery, OuterRef, Q
from django.db.models.functions import  TruncMonth
import json,logging,csv
from django.http import HttpRequest, HttpResponse


def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not all([email, username, password, confirm_password]):
            messages.error(request, "All fields are required.")
            return redirect('register')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            return render(request, 'InvApp/register.html', {'error': 'Username already taken'})
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('home')
    return render(request, 'InvApp/register.html')


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

def edit_profile(request):
    try:
        if request.method == 'POST':
            form = UserProfileForm(
                data=request.POST,
                files=request.FILES if request.FILES else None,
                instance=request.user
            )
            if form.is_valid():
                user = form.save(commit=False)
                password = form.cleaned_data.get('password')
                if password:
                    user.set_password(password) 
                user.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('home')  
            else:
                messages.error(request, 'Please correct the errors below.')
                logger.warning(f"Form validation failed: {form.errors}")
        else:
            form = UserProfileForm(instance=request.user)
        
        return render(request, 'InvApp/layout.html', {'form': form, 'user': request.user})
    except Exception as e:
        logger.error(f"Error in edit_profile: {str(e)}")
        messages.error(request, 'An unexpected error occurred. Please try again.')
        return render(request, 'InvApp/layout.html', {'form': UserProfileForm(instance=request.user), 'user': request.user})   


def logout_view(request):
    return render(request, 'Invapp/logout.html')   


def confirm_logout(request):
    logout(request)
    return redirect('login')


class DashboardBaseMixin:
    """Base mixin for dashboard-related functionality"""
    def get_date_range(self):
        """Get default date range (last 30 days)"""
        today = timezone.now().date()
        return {
            'default_start': today - timezone.timedelta(days=30),
            'default_end': today
        }

    def parse_date(self, date_str, default):
        """Parse date string or return default"""
        try:
            return timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return default

class HomeDashboardView(LoginRequiredMixin, DashboardBaseMixin, TemplateView):
    template_name = 'InvApp/home.html'
    paginate_by = 5
    critical_threshold = 0.2

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.setup_dates()
        self.setup_filters()
        
        context.update({
            **self.get_core_metrics(),
            **self.get_stock_metrics(),
            **self.get_sales_data(),
            **self.get_stock_trends(),
            **self.get_paginated_items(),
        })
        return context

    def setup_dates(self):
        """Initialize date-related attributes"""
        date_range = self.get_date_range()
        self.today = timezone.now().date()
        self.start_date = self.parse_date(
            self.request.GET.get('start_date'),
            date_range['default_start']
        )
        self.end_date = self.parse_date(
            self.request.GET.get('end_date'),
            date_range['default_end']
        )

    def setup_filters(self):
        """Initialize filtering parameters"""
        self.page_size = int(self.request.GET.get('page_size', self.paginate_by))

    def get_orders_queryset(self):
        """Return filtered orders queryset"""
        queryset = Order.objects.filter(
            order_date__range=[self.start_date, self.end_date]
        ).select_related('customer', 'product', 'batch_sku')
        return queryset

    def get_core_metrics(self):
        """Calculate and return core business metrics"""
        orders = self.get_orders_queryset()
        
        return {
            'total_orders': orders.count(),
            'total_customers': orders.values('customer').distinct().count(),
            'total_cash_made': orders.aggregate(
                total=Sum('final_total')
            )['total'] or 0.0,
            'stock_adjustments': StockAdjustment.objects.filter(
                created_at__date__range=[self.start_date, self.end_date]
            ).count(),
        }

    def get_stock_metrics(self):
        """Calculate and return stock-related metrics"""
        total_stock_in = ProductBatch.objects.filter(
            stock_date__range=[self.start_date, self.end_date]
        ).aggregate(total=Sum('current_quantity'))['total'] or 0
        
        return {
            'total_stock_in': total_stock_in,
            'total_products': Product.objects.count(),
            'low_stock_count': self.get_low_stock_queryset().count(),
        }

    def get_low_stock_queryset(self):
        """Return low stock items queryset"""

        queryset = Product.objects.annotate(
            critical_level=F('reorder_level') * self.critical_threshold
        ).filter(
            quantity_in_stock__lt=F('reorder_level'),
            batches__stock_date__range=[self.start_date, self.end_date]
        ).distinct()    
        return queryset

    def get_sales_data(self):
        """Generate monthly sales and profit data for charts"""
        buying_price_subquery = Subquery(
            ProductBatch.objects.filter(
                product=OuterRef('product')
            ).order_by('-stock_date').values('buying_price')[:1],
            output_field=DecimalField()
        )

        monthly_sales = self.get_orders_queryset().annotate(
            month=TruncMonth('order_date'),
            buying_price=buying_price_subquery
        ).values('month').annotate(
            total_sales=Sum('final_total'),
            total_profit=Sum(F('final_total') - (F('quantity') * F('buying_price')))
        ).order_by('month')

        return self.generate_time_series_data(
            monthly_sales,
            ['total_sales', 'total_profit'],
            'month'
        )

    def get_stock_trends(self):
        """Generate stock trend data for charts"""
        stock_trend = ProductBatch.objects.filter(
            stock_date__range=[self.start_date, self.end_date]
        ).annotate(
            month=TruncMonth('stock_date')
        ).values('month').annotate(
            total_stock=Sum('initial_quantity'),
            total_value=Sum(F('initial_quantity') * F('buying_price'))
        ).order_by('month')

        return self.generate_time_series_data(
            stock_trend,
            ['total_stock', 'total_value'],
            'month',
            is_float=False
        )

    def generate_time_series_data(self, queryset, fields, date_field, is_float=True):
        """Helper method to generate time series data for charts"""
        labels = []
        data = {field: [] for field in fields}
        
        current_month = (self.start_date.replace(day=1) - timezone.timedelta(days=1)).replace(day=1)
        while current_month <= self.end_date:
            labels.append(current_month.strftime('%b %Y'))
            
            # Find matching month data
            month_data = next(
                (item for item in queryset if 
                 item[date_field].month == current_month.month and
                 item[date_field].year == current_month.year),
                None
            )
            
            # Populate data
            for field in fields:
                value = month_data[field] if month_data else 0
                data[field].append(float(value) if is_float else int(value))
            
            current_month = (current_month + timezone.timedelta(days=32)).replace(day=1)
        
        return {
            'labels': json.dumps(labels),
            **{f'{field}_data': json.dumps(data[field]) for field in fields}
        }

    def get_paginated_items(self):
        """Return paginated low stock items and recent orders"""
        low_stock_paginator = Paginator(
            self.get_low_stock_queryset(),
            self.page_size
        )
        orders_paginator = Paginator(
            self.get_orders_queryset().order_by('-order_date')[:10],
            self.page_size
        )
        
        return {
            'low_stock_page_obj': low_stock_paginator.get_page(
                self.request.GET.get('low_stock_page')
            ),
            'orders_page_obj': orders_paginator.get_page(
                self.request.GET.get('orders_page')
            ),
        }
    
def get_categories_and_product_batches():
    categories = Category.objects.all()
    product_batches = ProductBatch.objects.all()
    return categories, product_batches

def handle_ajax_request(page_obj, paginator):
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


def product_list(request):
    categories, product_batches = get_categories_and_product_batches()

    category_id = request.GET.get('category', '')
    # search_query = request.GET.get('search', '').strip()

    products = Product.objects.all().order_by('-product_id')
    if category_id:
        products = products.filter(category_id=category_id)

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{form.cleaned_data['name']}' created successfully!")
            return redirect('product_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            return redirect('product_list')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return handle_ajax_request(page_obj, paginator)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'category_id': category_id,
        'product_batches': product_batches,
    }
    return render(request, 'InvApp/product_list.html', context) 

def get_product_batches(product):
    return ProductBatch.objects.filter(product=product).select_related('product', 'supplier').order_by('-stock_date')

def get_orders(product):
    return Order.objects.filter(product=product).select_related('batch_sku', 'customer').order_by('-order_date')

def get_adjustments(product):
    return StockAdjustment.objects.filter(product=product).select_related('batch').order_by('-created_at')

def get_sales_data(product, today):
    sales_labels = []
    sales_data = []
    for i in range(11, -1, -1): # range(0, 12)
        month_start = (today - relativedelta(months=i)).replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
        sales_labels.append(month_start.strftime("%b %Y"))
        monthly_sales = Order.objects.filter(
            product=product,
            order_date__gte=month_start,
            order_date__lte=month_end
        ).aggregate(total=Sum('quantity'))['total'] or 0
        sales_data.append(monthly_sales)
    return sales_labels, sales_data

def get_batch_data(product_batches):
    batch_labels = [f"Batch {batch.batch_sku}" for batch in product_batches]
    batch_quantities = [batch.current_quantity for batch in product_batches]
    return batch_labels, batch_quantities

def get_total_sold_last_30_days(product, today):
    thirty_days_ago = today - timedelta(days=30)
    return Order.objects.filter(
        product=product, order_date__gte=thirty_days_ago
    ).aggregate(total=Sum('quantity'))['total'] or 0

def get_yearly_sales_and_avg_monthly_sales(product, today):
    yearly_sales = Order.objects.filter(
        product=product, order_date__gte=today - timedelta(days=365)
    ).aggregate(total=Sum('quantity'))['total'] or 0
    avg_monthly_sales = yearly_sales / 12 if yearly_sales else 0
    return yearly_sales, avg_monthly_sales

def get_suggested_reorder_quantity(product):
    return product.reorder_level * 2 if product.reorder_level else 0

def get_expiring_batches_count(product_batches, today):
    return product_batches.filter(
        expiry_date__lte=today + timedelta(days=30),
        expiry_date__gte=today
    ).count()

def get_combined_activity(product_batches, product, request):
    combined_activity = []

    for batch in product_batches:
        combined_activity.append({
            'date': batch.stock_date,
            'event_type': 'batch',
            'description': f"Batch {batch.batch_sku} added with {batch.initial_quantity} {product.units}",
            'quantity': batch.initial_quantity,
            'user': {'name': request.user}
        })

        orders = Order.objects.filter(batch_sku__batch_sku=batch.batch_sku).select_related('customer')
        for order in orders:
            combined_activity.append({
                'date': order.order_date,
                'event_type': 'order',
                'description': f"Order #{order.id} placed for {order.quantity} {product.units}" + (f" from batch_sku {order.batch_sku.batch_sku}" if order.batch_sku else ""),
                'quantity': -order.quantity,
                'customer': order.customer,
            })

        adjustments = StockAdjustment.objects.filter(batch=batch)
        for adj in adjustments:
            combined_activity.append({
                'date': adj.created_at,
                'event_type': 'adjustment',
                'description': f"Stock {adj.adjustment_type} of {adj.quantity} {product.units} ({adj.reason})" + (f" for batch {adj.batch.batch_sku}" if adj.batch else ""),
                'quantity': adj.quantity if adj.adjustment_type == 'add' else -adj.quantity,
                'user': {'name': request.user}
            })

    combined_activity.sort(key=lambda x: x['date'], reverse=True)
    return combined_activity

def product_history(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product_batches = get_product_batches(product)
    orders = get_orders(product)
    adjustments = get_adjustments(product)
    today = datetime.now().date()

    combined_activity = get_combined_activity(product_batches, product, request)

    sales_labels, sales_data = get_sales_data(product, today)
    batch_labels, batch_quantities = get_batch_data(product_batches)
    total_sold_last_30_days = get_total_sold_last_30_days(product, today)
    yearly_sales, avg_monthly_sales = get_yearly_sales_and_avg_monthly_sales(product, today)
    suggested_reorder_quantity = get_suggested_reorder_quantity(product)
    expiring_batches_count = get_expiring_batches_count(product_batches, today)

    combined_activity_paginator = Paginator(combined_activity, 10)
    combined_activity_page = request.GET.get('page', 1)
    combined_activity = combined_activity_paginator.get_page(combined_activity_page)

    orders_paginator = Paginator(orders, 10)
    orders_page = request.GET.get('page', 1)
    orders = orders_paginator.get_page(orders_page)

    adjustments_paginator = Paginator(adjustments, 10)
    adjustments_page = request.GET.get('page', 1)
    adjustments = adjustments_paginator.get_page(adjustments_page)

    context = {
        'product': product,
        'product_batches': product_batches,
        'combined_activity': combined_activity,
        'orders': orders,
        'adjustments': adjustments,
        'total_sold_last_30_days': total_sold_last_30_days,
        'avg_monthly_sales': avg_monthly_sales,
        'yearly_sales':yearly_sales,
        'suggested_reorder_quantity': suggested_reorder_quantity,
        'expiring_batches_count': expiring_batches_count,
        'sales_labels': sales_labels,
        'sales_data': sales_data,
        'batch_labels': batch_labels,
        'batch_quantities': batch_quantities,
        'active_tab': request.GET.get('tab', 'activity'),
    }

    return render(request, 'InvApp/product_history.html', context)   


def customer_list(request):
    customers = Customer.objects.all()
    paginator = Paginator(customers, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    total_cust = Customer.objects.count()

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer added successfully!')
            return redirect('customer_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.upper()}: {error}")
            return redirect('customer_list')

    context = {
        'page_obj': page_obj,
        'total_cust': total_cust,
    }
    return render(request, 'Invapp/customer_list.html', context)

def customer_edit(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Customer edited successfully!')
            return redirect('customer_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            return render(request, 'Invapp/customer_edit.html', {'customer': customer, 'form': form})

    form = CustomerForm(instance=customer)
    return render(request, 'Invapp/customer_edit.html', {'customer': customer, 'form': form})

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
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
            return render(request, 'Invapp/product_update.html', {'product': product, 'form': form})

    form = ProductForm(instance=product)
    return render(request, 'Invapp/product_update.html', {'product': product, 'form': form})

def product_confirm_delete(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('product_list')
    return render(request, 'Invapp/product_confirm_delete.html', {'product': product})

def get_selling_price(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    return JsonResponse({"selling_price": product.selling_price})


logger = logging.getLogger(__name__)
@cache_page(60 * 15)
@require_http_methods(["GET"])
def get_sales_data(request):
    """
    Returns sales data aggregated by month or year in JSON format.
    """
    try:
        interval = request.GET.get('interval', 'month').lower()
        if interval == 'year':
            trunc_kind = TruncYear('order_date')
            date_format = '%Y'
        else:
            # Default to monthly if interval is not 'year' or invalid
            trunc_kind = TruncMonth('order_date')
            date_format = '%b %Y'

        sales_data = (
            Order.objects
            .annotate(interval_group=trunc_kind)
            .values('interval_group')
            .annotate(total_quantity=models.Sum('quantity'))
            .order_by('interval_group')
            .values_list('interval_group', 'total_quantity')
        )

        if not sales_data:
            logger.info("No sales data found")
            return JsonResponse({'labels': [], 'data': []})

        interval_dates, quantities = zip(*sales_data)
        labels = [date.strftime(date_format) for date in interval_dates]
        data = list(quantities)

        return JsonResponse({
            'labels': labels,
            'data': data,
            'meta': {
                'min_date': min(interval_dates).isoformat(),
                'max_date': max(interval_dates).isoformat(),
                'total_sales': sum(quantities),
                'interval': interval
            }
        })

    except EmptyResultSet:
        return JsonResponse({'labels': [], 'data': []}, status=200)
    
    except models.DatabaseError as e:
        logger.error(f"Database error fetching sales data: {str(e)}")
        return JsonResponse({'error': 'Unable to retrieve sales data'}, status=503)
    
    except Exception as e:
        logger.critical(f"Unexpected error in get_sales_data: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)   

def get_stock_data(request):
    products = Product.objects.all().only('name', 'quantity_in_stock')
    labels = [product.name for product in products]
    data = [product.quantity_in_stock for product in products]

    return JsonResponse({'labels': labels, 'data': data})

def parse_selected_date(request: HttpRequest) -> datetime.date:
    """Parse the selected date from request GET parameters, default to today if not provided."""
    selected_date_str = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = datetime.today().date()
        selected_date_str = selected_date.strftime('%Y-%m-%d')
    return selected_date, selected_date_str

def calculate_stock_transactions(products, selected_date, prev_date):
    """Calculate stock transactions for each product."""
    stock_transactions = []
    total_stock_in = 0
    total_stock_out = 0
    total_adjustments = 0

    for product in products:
        # Stock In: new_stock + positive adjustments
        stock_in = (
            Stock.objects.filter(product=product, stock_date=selected_date)
            .aggregate(total=Sum('new_stock'))['total'] or 0
        )
        positive_adjustments = (
            StockAdjustment.objects.filter(
                product=product, created_at__date=selected_date, adjustment_type='add'
            )
            .aggregate(total=Sum('quantity'))['total'] or 0
        )
        stock_in_total = stock_in + positive_adjustments

        # Stock Out: orders + negative adjustments
        stock_out = (
            Order.objects.filter(product=product, order_date=selected_date)
            .aggregate(total=Sum('quantity'))['total'] or 0
        )
        negative_adjustments = (
            StockAdjustment.objects.filter(
                product=product, created_at__date=selected_date, adjustment_type='subtract'
            )
            .aggregate(total=Sum('quantity'))['total'] or 0
        )
        stock_out_total = stock_out + negative_adjustments

        net_adjustments = positive_adjustments - negative_adjustments

        # Calculate previous stock details
        prev_new_stock = (
            Stock.objects.filter(product=product, stock_date__lte=prev_date)
            .aggregate(total=Sum('new_stock'))['total'] or 0
        )
        prev_positive_adjustments = (
            StockAdjustment.objects.filter(
                product=product, created_at__date__lte=prev_date, adjustment_type='add'
            )
            .aggregate(total=Sum('quantity'))['total'] or 0
        )
        prev_negative_adjustments = (
            StockAdjustment.objects.filter(
                product=product, created_at__date__lte=prev_date, adjustment_type='subtract'
            )
            .aggregate(total=Sum('quantity'))['total'] or 0
        )
        prev_orders = (
            Order.objects.filter(product=product, order_date__lte=prev_date)
            .aggregate(total=Sum('quantity'))['total'] or 0
        )
        opening_stock = (
            prev_new_stock + prev_positive_adjustments - prev_orders - prev_negative_adjustments
        )

        total_stock_in += stock_in_total
        total_stock_out += stock_out_total
        total_adjustments += net_adjustments

        stock_transactions.append({
            'product_name': product.name,
            'negative_adjustments': negative_adjustments,
            'positive_adjustments': positive_adjustments,
            'opening_stock': opening_stock,
            'stock_in': stock_in_total,
            'stock_out': stock_out_total,
            'net_adjustments': net_adjustments,
            'stock_available': ProductBatch.objects.aggregate(total=Sum('current_quantity'))['total'] or 0,
            'category_name': product.category.name if product.category else 'N/A',
        })

    total_opening_stock = sum(t['opening_stock'] for t in stock_transactions)
    return stock_transactions, total_stock_in, total_stock_out, total_adjustments, total_opening_stock

def report_page(request: HttpRequest) -> HttpResponse:
    """Generate a report page with stock transactions and other metrics."""
    selected_date, selected_date_str = parse_selected_date(request)
    prev_date = selected_date - timedelta(days=1)

    
    stock_adjustments_count = StockAdjustment.objects.filter(created_at__date=selected_date).count()

    # Fetch products and product batches
    selected_category_id = request.GET.get('category', None)
    products = Product.objects.select_related('category').all()
    product_batches = ProductBatch.objects.all()

    # Filter products by category if a category is selected
    if selected_category_id:
        products = products.filter(category_id=selected_category_id)

    # Calculate stock transactions
    stock_transactions, total_stock_in, total_stock_out, total_adjustments, total_opening_stock = calculate_stock_transactions(products, selected_date, prev_date)

    orders = Order.objects.filter(order_date=selected_date)
    total_customers = orders.values('customer').distinct().count()
    total_orders = orders.count()

    total_cash_made = orders.aggregate(total=Sum('final_total'))['total'] or 0
    total_quantity_sold = orders.aggregate(total=Sum('quantity'))['total'] or 0

    all_zeros = all([
        total_opening_stock == 0,
        total_stock_in == 0,
        total_stock_out == 0,
        total_adjustments == 0,
        total_cash_made == 0,
        total_quantity_sold == 0,
    ])

    context = {
        'selected_date': selected_date_str,
        'selected_category': selected_category_id,
        'orders': orders,
        'products': products,
        'product_batches': product_batches,
        'stock_transactions': stock_transactions,
        'total_opening_stock': total_opening_stock,
        'total_stock_in': total_stock_in,
        'total_stock_out': total_stock_out,
        'total_adjustments': total_adjustments,
        'total_customers': total_customers,
        'total_orders': total_orders,
        'stock_adjustments': stock_adjustments_count,
        'total_cash_made': total_cash_made,
        'total_quantity_sold': total_quantity_sold,
        'all_zeros': all_zeros,
    }
    return render(request, 'InvApp/report.html', context)

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

def get_product_and_batch(product_id: int, batch_id: int = None):
    """
    Fetch product and batch objects based on provided IDs.
    """
    try:
        product = Product.objects.get(product_id=product_id)
    except Product.DoesNotExist:
        raise Exception("Product not found.")

    batch = None
    if batch_id:
        try:
            batch = ProductBatch.objects.get(id=batch_id, product=product)
        except ProductBatch.DoesNotExist:
            raise Exception("Invalid Batch ID.")
    
    return product, batch

def process_stock_adjustment(request: HttpRequest, form: StockAdjustmentForm):
    """
    Process the stock adjustment form and update the database.
    """
    product = form.cleaned_data['product_id']
    adjustment_type = form.cleaned_data['adjustment_type']
    quantity = form.cleaned_data['quantity']
    reason = form.cleaned_data['reason']
    batch = form.cleaned_data.get('batch_sku')

    if adjustment_type == 'add':
        if batch:
            batch.current_quantity = F('current_quantity') + quantity
            batch.save()
        product.quantity_in_stock = F('quantity_in_stock') + quantity
        product.save()
    elif adjustment_type == 'subtract':
        if batch:
            batch.current_quantity = F('current_quantity') - quantity
            batch.save()
        product.quantity_in_stock = F('quantity_in_stock') - quantity
        product.save()

    StockAdjustment.objects.create(
        product=product,
        adjustment_type=adjustment_type,
        quantity=quantity,
        reason=reason,
        batch=batch,
        created_at=timezone.now()
    )
    messages.success(request, "Stock adjusted successfully!")

def parse_date_range(request: HttpRequest) -> tuple:
    """
    Parse the date range from request GET parameters using DateRangeForm.
    """
    form = DateRangeForm(request.GET)
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
    else:
        start_date = date.today()
        end_date = date.today()
    return start_date, end_date    

def stock_adjustments(request: HttpRequest) -> HttpResponse:
    """
    View to display stock adjustments and handle form submissions to add new stock adjustments.
    """
    start_date, end_date = parse_date_range(request)

    if request.method == 'POST':
        stock_adjustment_form = StockAdjustmentForm(request.POST)
        if stock_adjustment_form.is_valid():
            try:
                process_stock_adjustment(request, stock_adjustment_form)
                return redirect('stock_adjustments')
            except Exception as e:
                messages.error(request, str(e))
    else:
        stock_adjustment_form = StockAdjustmentForm()

    products = Product.objects.all()
    product_batches = ProductBatch.objects.all()
    stock_adjustments_qs = StockAdjustment.objects.all().select_related('product').filter(
        created_at__date__range=(start_date, end_date)
    )

    context = {
        'stock_adjustments_list': stock_adjustments_qs,
        'start_date': start_date,
        'end_date': end_date,
        'products': products,
        'product_batches': product_batches,
        'stock_adjustment_form': stock_adjustment_form,
    }
    return render(request, 'InvApp/adjust.html', context)

def get_stock_alerts() -> list:
    """
    Get stock alerts for critical and low stock levels.
    """
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

def annotate_batch_status(queryset):
    """
    Annotate product batches with expiry status and days until expiry.
    """
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

def stock_view(request: HttpRequest) -> HttpResponse:
    """
    View to display stock information with filters and alerts.
    """
    start_date, end_date = parse_date_range(request)

    stocks = Stock.objects.filter(
        stock_date__range=[start_date, end_date]
    ).select_related('product', 'product__category').order_by('-stock_date')
    
    products = Product.objects.all().select_related('category')
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    paginator = Paginator(stocks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    stock_alerts = get_stock_alerts()

    # top_products = Stock.objects.values(
    #     'product__name'
    # ).annotate(
    #     total=Sum('total_stock')
    # ).order_by('-total')[:10]
    
    # category_dist = Stock.objects.values(
    #     'product__category__name'
    # ).annotate(
    #     count=Count('id'),
    #     total_stock=Sum('total_stock')
    # ).order_by('-count')

    product_batches = annotate_batch_status(ProductBatch.objects.all().select_related('product', 'supplier'))
    total_products = Product.objects.count()
    low_stock_items = len([a for a in stock_alerts if a['status'] == 'low'])
    critical_stock_items = len([a for a in stock_alerts if a['status'] == 'critical'])
    
    # total_stock_value = sum(
    #     stock.total_stock * stock.product.selling_price 
    #     for stock in Stock.objects.select_related('product')
    # )

    context = {
        'stocks': page_obj,
        'products': products,
        'categories': categories,
        'suppliers': suppliers,
        'start_date': start_date,
        'end_date': end_date,
        'product_batches': product_batches,
        'stock_alerts': stock_alerts,
        'total_products': total_products,
        'low_stock_items': low_stock_items,
        'critical_stock_items': critical_stock_items,
        # 'total_stock_value': total_stock_value,
        # 'product_names': [p['product__name'] for p in top_products],
        # 'stock_levels': [p['total'] for p in top_products],
        # 'category_names': [c['product__category__name'] for c in category_dist],
        # 'category_counts': [c['count'] for c in category_dist],
        # 'category_stock': [c['total_stock'] for c in category_dist],
    }
    return render(request, 'InvApp/stock.html', context)

logger = logging.getLogger(__name__)
def add_stock(request):
    if request.method == 'POST':
        form = AddStockForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    product_id = form.cleaned_data['product_id']
                    product = get_object_or_404(Product, product_id=product_id)
                    supplier_id = form.cleaned_data['supplier_id']
                    supplier = get_object_or_404(Supplier, id=supplier_id)
                    new_stock = form.cleaned_data['new_stock']
                    batch_sku = form.cleaned_data['batch_sku']
                    buying_price = form.cleaned_data['buying_price']
                    manufacture_date = form.cleaned_data['manufacture_date']
                    expiry_date = form.cleaned_data['expiry_date']
                    stock_date = form.cleaned_data.get('stock_date', timezone.now().date())

                   
                    product.quantity_in_stock = F('quantity_in_stock') + new_stock
                    product.save()

                    ProductBatch.objects.create(
                        product=product,
                        supplier=supplier,
                        batch_sku=batch_sku,
                        buying_price=buying_price,
                        initial_quantity=new_stock,
                        current_quantity=new_stock,
                        expiry_date=expiry_date,
                        manufacture_date=manufacture_date,
                        stock_date=stock_date,
                    )

                    Stock.objects.create(
                        product=product,
                        initial_stock=F('product__quantity_in_stock') - new_stock,
                        new_stock=new_stock,
                        total_stock=F('product__quantity_in_stock'),
                        stock_date=stock_date,
                    )

                    return redirect('stock')

            except Exception as e:
                logger.error(f"Error processing request: {e}")
                return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=500)
        else:
            logger.error(f"Form validation errors: {form.errors}")
            return JsonResponse({'errors': form.errors}, status=400)

    form = AddStockForm()
    products = Product.objects.all()
    # total_new_stock = Stock.objects.aggregate(total=Sum('new_stock'))['total'] or 0
    context = {
        'form': form,
        # 'products': products,
        # 'total_new_stock': total_new_stock
    }
    return render(request, 'InvApp/stock.html', context)

logger = logging.getLogger(__name__)
def order_page(request: HttpRequest) -> HttpResponse:
    """
    View to display stock information with filters and alerts.
    """
    form = OrderFilterForm(request.GET)
    if form.is_valid():
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        customer = form.cleaned_data['customer']
        status = form.cleaned_data['status']
        payment_method = form.cleaned_data['payment_method']
        # search_query = form.cleaned_data['search']
        sort_by = form.cleaned_data['sort_by']
        page_size = form.cleaned_data['page_size']

        orders = Order.objects.select_related('customer', 'product', 'batch_sku').filter(
            order_date__range=[start_date, end_date]
        )

        if customer:
            orders = orders.filter(customer=customer)

        if status:
            orders = orders.filter(status=status)

        if payment_method:
            orders = orders.filter(payment_method=payment_method)

        # if search_query:
        #     orders = orders.filter(
        #         Q(customer__name__icontains=search_query) |
        #         Q(product__name__icontains=search_query) |
        #         Q(id__icontains=search_query)
        #     )

        orders = orders.order_by(sort_by)

        total_customers = orders.values('customer').distinct().count()
        total_orders = orders.count()
        total_quantity = orders.aggregate(total=Sum('quantity'))['total'] or 0
        total_cash_made = orders.aggregate(total=Sum('final_total'))['total'] or 0.0

        paginator = Paginator(orders, page_size)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context = {
            'orders': page_obj,
            'page_obj': page_obj,
            'start_date': start_date,
            'end_date': end_date,
            'total_customers': total_customers,
            'total_orders': total_orders,
            'total_quantity': total_quantity,
            'total_cash_made': total_cash_made,
            'customers': Customer.objects.all(),
            'products': Product.objects.all(),
            'product_batches': ProductBatch.objects.all(),
            'status_choices': form.fields['status'].choices,
            'payment_methods': form.fields['payment_method'].choices,
            # 'page_sizes': form.fields['page_size'].choices,
            # 'current_page_size': page_size,
            'sort_by': sort_by,
            'form': form
        }
        return render(request, 'InvApp/order_page.html', context)
    else:
        logger.error(f"Form validation errors: {form.errors}")
        context = {
            'form': form,
            'status_choices': form.fields['status'].choices,
            'payment_methods': form.fields['payment_method'].choices,
            'page_sizes': form.fields['page_size'].choices,
        }
        return render(request, 'InvApp/order_page.html', context)

logger = logging.getLogger(__name__)
def place_order(request: HttpRequest):
    """
    View to handle placing a new order.
    """
    if request.method == 'POST':
        form = PlaceOrderForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    customer = form.cleaned_data['order_customer']
                    products = form.cleaned_data['products']
                    order_quantities = form.cleaned_data['order_quantities']
                    units = form.cleaned_data['units']
                    price_per_units = form.cleaned_data['price_per_units']
                    total_prices = form.cleaned_data['total_prices']
                    batch_skus = form.cleaned_data['batch_skus']
                    discounts = form.cleaned_data['product_discounts']
                    order_date = form.cleaned_data['order_date']
                    final_total = form.cleaned_data['final_total']
                    payment_method = form.cleaned_data['payment_method']

                    errors = []

                    for i in range(len(products)):
                        product = products[i]
                        quantity = order_quantities[i]
                        unit = units[i]
                        price_per_unit = price_per_units[i]
                        total_price = total_prices[i]
                        batch_sku = batch_skus[i]
                        discount = discounts[i]

                        try:
                            batch = ProductBatch.objects.get(id=batch_sku) if batch_sku else None
                        except ProductBatch.DoesNotExist:
                            errors.append(f"Batch with ID {batch_sku} does not exist.")
                            continue

                        if quantity <= 0:
                            errors.append(f"Invalid quantity for product {product.name}.")
                            continue

                        if product.quantity_in_stock < quantity:
                            errors.append(f"Insufficient stock for product {product.name}. Available: {product.quantity_in_stock}, Requested: {quantity}")
                            continue

                        if batch and batch.current_quantity < quantity:
                            errors.append(f"Insufficient quantity in batch {batch.batch_sku}. Available: {batch.current_quantity}, Requested: {quantity}")
                            continue

                        # Create Order
                        Order.objects.create(
                            customer=customer,
                            product=product,
                            batch_sku=batch,
                            quantity=quantity,
                            price_per_unit=price_per_unit,
                            total_price=total_price,
                            units=unit,
                            payment_method=payment_method,
                            discount=discount,
                            order_date=order_date,
                            final_total=final_total,
                        )

                        # Update stock
                        product.quantity_in_stock -= quantity
                        product.save()

                        if batch:
                            batch.current_quantity -= quantity
                            batch.save()

                    if errors:
                        for error in errors:
                            messages.error(request, error)
                        return redirect('order_page')

                    messages.success(request, "Order placed successfully!")
                    return redirect('order_page')

            except Exception as e:
                logger.error(f"Error placing order: {e}")
                messages.error(request, f"Error placing order: {str(e)}")
                return redirect('order_page')
        else:
            logger.error(f"Form validation errors: {form.errors}")
            for error in form.errors.values():
                messages.error(request, error)
            return redirect('order_page')

    return redirect('order_page')

logger = logging.getLogger(__name__)
class BulkUpdateOrdersView(View):
    def post(self, request):
        form = BulkUpdateOrdersForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    order_ids = form.cleaned_data['order_ids']
                    action = form.cleaned_data['action']
                    new_status = form.cleaned_data.get('new_status')

                    if action == 'update_status':
                        updated_count = Order.objects.filter(id__in=order_ids).update(status=new_status)
                        messages.success(request, f'Updated status for {updated_count} order(s) to {dict(Order.STATUS_CHOICES).get(new_status, new_status)}.')

                    elif action == 'delete':
                        orders_to_delete = Order.objects.filter(id__in=order_ids).select_related('product')
                        
                        for order in orders_to_delete:
                            product = order.product
                            product.quantity_in_stock = F('quantity_in_stock') + order.quantity
                            product.save()
                        
                        deleted_count, _ = orders_to_delete.delete()
                        messages.success(request, f'Successfully deleted {deleted_count} order(s).')
                    
                    else:
                        messages.error(request, 'Invalid action selected.')
                
                return redirect('order_page')

            except Exception as e:
                logger.error(f"Error processing bulk update: {e}")
                messages.error(request, f'Error processing bulk update: {str(e)}')
                return redirect('order_page')
        else:
            logger.error(f"Form validation errors: {form.errors}")
            for error in form.errors.values():
                messages.error(request, error)
            return redirect('order_page')

logger = logging.getLogger(__name__)
def export_orders_csv(request):
    field_mappings = {
        'Order ID': 'id',
        'Customer': lambda obj: obj.customer.name,
        'Product': lambda obj: obj.product.name,
        'Batch SKU': lambda obj: obj.batch_sku.batch_sku if obj.batch_sku else 'N/A',
        'Quantity': 'quantity',
        'Units': 'units',
        'Price per Unit': 'price_per_unit',
        'Total Price': 'total_price',
        'Payment Method': 'payment_method',
        'Discount (%)': 'discount',
        'Final Total': 'final_total',
        'Order Date': 'order_date',
        'Status': 'status'
    }
    queryset = Order.objects.select_related('customer', 'product', 'batch_sku')
    return export_csv(request, Order, queryset, field_mappings, 'orders')

# def export_products_csv(request):
#     field_mappings = {
#         'Product ID': 'id',
#         'Name': 'name',
#         'Category': 'category',
#         'Price': 'price',
#         'Stock Quantity': 'quantity_in_stock',
#         'Description': 'description'
#     }
#     queryset = Product.objects.all()
#     return export_csv(request, Product, queryset, field_mappings, 'products')

# def export_customers_csv(request):
#     field_mappings = {
#         'Customer ID': 'id',
#         'Name': 'name',
#         'Email': 'email',
#         'Phone': 'phone',
#         'Address': 'address'
#     }
#     queryset = Customer.objects.all()
#     return export_csv(request, Customer, queryset, field_mappings, 'customers')


logger = logging.getLogger(__name__)

def get_latest_buying_price_subquery():
    latest_batch = ProductBatch.objects.filter(product=OuterRef('product')).order_by('-stock_date')[:1]
    return Subquery(latest_batch.values('buying_price')[:1], output_field=FloatField())

def calculate_batch_values():
    return ProductBatch.objects.values(
        'product__name', 'product__product_id', 'product__category__name'
    ).annotate(
        buying_price=Sum(F('buying_price')),
        quantity=Sum('initial_quantity'),
        total_value=Sum(
            ExpressionWrapper(
                F('initial_quantity') * F('buying_price'),
                output_field=FloatField()
            )
        ),
    ).order_by('-total_value')

def calculate_total_inventory_value(batch_values):
    return sum(item['total_value'] for item in batch_values if item['total_value']) or 0.0

def process_inventory_data(batch_values, total_inventory_value):
    return [
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

def get_low_stock_items():
    critical_threshold = 0.2
    return Product.objects.annotate(
        critical_level=F('reorder_level') * critical_threshold
    ).filter(quantity_in_stock__lt=F('reorder_level')).values(
        'product_id', 'name', 'quantity_in_stock',
        'reorder_level', 'reorder_quantity', 'critical_level'
    )

def calculate_critical_stock_count(low_stock_items):
    return low_stock_items.filter(
        quantity_in_stock__lt=F('critical_level')
    ).count()

def calculate_total_products():
    return Product.objects.count()

def calculate_average_reorder_quantity():
    return Product.objects.aggregate(
        avg_reorder=ExpressionWrapper(
            Sum('reorder_quantity'),
            output_field=FloatField()
        )
    )['avg_reorder'] or 0.0

def calculate_category_data(total_inventory_value):
    return Category.objects.annotate(
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

def process_category_data(category_data):
    return [
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

def calculate_inventory_trend(today, twelve_months_ago):
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

    labels, values = [], []
    current_month = twelve_months_ago.replace(day=1)
    while current_month <= today:
        month_data = next(
            (item for item in inventory_trend if item['month'] and item['month'].month == current_month.month and item['month'].year == current_month.year),
            {'total_value': 0.0}
        )
        labels.append(current_month.strftime('%b %Y'))
        values.append(float(month_data['total_value'] or 0.0))
        current_month = (current_month + timezone.timedelta(days=32)).replace(day=1)
    return labels, values

def get_recent_orders(thirty_days_ago):
    return Order.objects.filter(
        order_date__gte=thirty_days_ago,
        payment_method__in=["cash", "credit_card", "mobile_money", "bank_transfer"]
    )

def calculate_total_revenue(orders):
    return orders.aggregate(
        total=Sum('total_price', output_field=FloatField())
    )['total'] or 0.0

def get_previous_period_orders(thirty_days_ago):
    previous_period_start = thirty_days_ago - timezone.timedelta(days=30)
    return Order.objects.filter(
        order_date__gte=previous_period_start,
        order_date__lt=thirty_days_ago,
        payment_method__in=["cash", "credit_card", "mobile_money", "bank_transfer"]
    )

def calculate_previous_revenue(previous_period_orders):
    return previous_period_orders.aggregate(
        total=Sum('total_price', output_field=FloatField())
    )['total'] or 0.0

def calculate_revenue_growth(total_revenue, previous_revenue):
    return ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue else 0.0

def calculate_cogs_and_gross_profit( total_revenue, orders, buying_price_subquery):
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
    return total_cogs, gross_profit, gross_margin

def calculate_total_orders(orders):
    return orders.count()

def calculate_avg_order_value(total_revenue, total_orders):
    return (total_revenue / total_orders) if total_orders else 0.0

def get_top_selling_products(orders, buying_price_subquery):
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

        processed_top_selling = [
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

        logger.debug("Top Selling Processed: %s", processed_top_selling)
        return processed_top_selling
    except Exception as e:
        logger.error("Error in top_selling query: %s", str(e))
        return []

def calculate_top_selling_metrics(processed_top_selling, total_revenue):
    top5_revenue = sum(item['revenue'] for item in processed_top_selling[:5] if item['revenue'] is not None) or 0.0
    top5_percentage = (top5_revenue / total_revenue * 100) if total_revenue else 0.0
    other_percentage = 100.0 - top5_percentage if total_revenue else 0.0
    top_product_names = [item['product__name'] for item in processed_top_selling]
    top_product_values = [item['revenue'] for item in processed_top_selling]
    return top5_revenue, top5_percentage, other_percentage, top_product_names, top_product_values

def calculate_monthly_sales(today, twelve_months_ago, orders, buying_price_subquery):
    monthly_sales = orders.annotate(
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

    processed_monthly_sales = [
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

    labels, sales_data, profit_data = [], [], []
    current_month = twelve_months_ago.replace(day=1)
    while current_month <= today:
        month_data = next(
            (item for item in processed_monthly_sales if item['month'] and item['month'].month == current_month.month and item['month'].year == current_month.year),
            {
                'total_sales': 0.0,
                'gross_profit': 0.0,
                'order_count': 0,
                'net_sales': 0.0,
                'cogs': 0.0,
                'margin': 0.0
            }
        )
        labels.append(current_month.strftime('%b %Y'))
        sales_data.append(float(month_data['total_sales']))
        profit_data.append(float(month_data['gross_profit']))
        current_month = (current_month + timezone.timedelta(days=32)).replace(day=1)
    return labels, sales_data, profit_data

def calculate_sales_trend(total_revenue, previous_revenue, total_cogs, total_orders, previous_period_orders):
    current_period_sales = total_revenue
    previous_period_sales = previous_revenue
    sales_change = calculate_revenue_growth(total_revenue, previous_revenue)
    current_period_units = total_orders
    previous_period_units = previous_period_orders.aggregate(total=Sum('quantity'))['total'] or 0
    units_change = ((current_period_units - previous_period_units) / previous_period_units * 100) if previous_period_units else 0.0
    current_avg_order = calculate_avg_order_value(total_revenue, total_orders)
    previous_avg_order = (previous_revenue / previous_period_orders.count()) if previous_period_orders.count() else 0.0
    aov_change = ((current_avg_order - previous_avg_order) / previous_avg_order * 100) if previous_avg_order else 0.0
    return current_period_sales, previous_period_sales, sales_change, current_period_units, previous_period_units, units_change, current_avg_order, previous_avg_order, aov_change

def calculate_daily_sales(orders, buying_price_subquery):
    return orders.annotate(
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

def calculate_total_units(orders):
    return orders.aggregate(total=Sum('quantity'))['total'] or 0

def calculate_profitability_matrix(orders, buying_price_subquery):
    return orders.annotate(
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

def calculate_category_profit(orders, buying_price_subquery):
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

    return [
        {
            'product__category__name': item['product__category__name'],
            'revenue': item['revenue'] or 0.0,
            'cogs': item['cogs'] or 0.0,
            'profit': item['profit'] or 0.0,
            'margin': item['margin'] or 0.0 if item['revenue'] else 0.0
        }
        for item in category_profit
    ]

def get_near_expiry_products(today):
    return ProductBatch.objects.filter(
        expiry_date__range=[today, today + timezone.timedelta(days=365)]
    ).select_related('product').values(
        'product__name', 'expiry_date', 'initial_quantity'
    ).order_by('expiry_date')


def report_analysis(request):
    today = timezone.now().date()
    thirty_days_ago = today - timezone.timedelta(days=30)
    twelve_months_ago = today - timezone.timedelta(days=365)

    buying_price_subquery = get_latest_buying_price_subquery()
    batch_values = calculate_batch_values()
    total_inventory_value = calculate_total_inventory_value(batch_values)
    inventory_data = process_inventory_data(batch_values, total_inventory_value)

    low_stock_items = get_low_stock_items()
    critical_stock_count = calculate_critical_stock_count(low_stock_items)
    total_products = calculate_total_products()
    low_stock_count = low_stock_items.count()
    average_reorder_quantity = calculate_average_reorder_quantity()
    category_data = process_category_data(calculate_category_data(total_inventory_value))

    inventory_trend_labels, inventory_trend_values = calculate_inventory_trend(today, twelve_months_ago)

    orders = get_recent_orders(thirty_days_ago)
    total_revenue = calculate_total_revenue(orders)
    previous_period_orders = get_previous_period_orders(thirty_days_ago)
    previous_revenue = calculate_previous_revenue(previous_period_orders)
    revenue_growth = calculate_revenue_growth(total_revenue, previous_revenue)

    total_cogs, gross_profit, gross_margin = calculate_cogs_and_gross_profit(orders, buying_price_subquery)
    total_orders = calculate_total_orders(orders)
    avg_order_value = calculate_avg_order_value(total_revenue, total_orders)

    top_selling_processed = get_top_selling_products(orders, buying_price_subquery)
    top5_revenue, top5_percentage, other_percentage, top_product_names, top_product_values = calculate_top_selling_metrics(top_selling_processed, total_revenue)

    monthly_labels, monthly_sales_data, monthly_profit_data = calculate_monthly_sales(today, twelve_months_ago, orders, buying_price_subquery)

    current_period_sales, previous_period_sales, sales_change, current_period_units, previous_period_units, units_change, current_avg_order, previous_avg_order, aov_change = calculate_sales_trend(total_revenue, previous_revenue, total_cogs, total_orders, previous_period_orders)

    daily_sales = calculate_daily_sales(orders, buying_price_subquery)
    total_units = calculate_total_units(orders)
    total_cost = total_cogs
    total_profit = gross_profit

    profitability_matrix = calculate_profitability_matrix(orders, buying_price_subquery)
    category_profit = calculate_category_profit(orders, buying_price_subquery)
    near_expiry = get_near_expiry_products(today)

    context = {
        'total_revenue': total_revenue,
        'revenue_growth': round(revenue_growth, 2),
        'gross_profit': gross_profit,
        'gross_margin': round(gross_margin, 2),
        'avg_order_value': avg_order_value,
        'total_orders': total_orders,
        'return_rate': 0.0, 
        'total_returns': 0.0,
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
        'top_selling': top_selling_processed,
        'top_product_names': json.dumps(top_product_names),
        'top_product_values': top_product_values,
        'top5_percentage': round(top5_percentage, 2),
        'other_percentage': round(other_percentage, 2),
        'monthly_sales': monthly_sales_data,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_profit_data': monthly_profit_data,
        'current_period_sales': current_period_sales,
        'previous_period_sales': previous_period_sales,
        'sales_change': round(sales_change, 2),
        'current_period_units': current_period_units,
        'previous_period_units': previous_period_units,
        'units_change': round(units_change, 2),
        'current_avg_order': current_avg_order,
        'previous_avg_order': previous_avg_order,
        'aov_change': round(aov_change, 2),
        'daily_sales': daily_sales,
        'total_units': total_units,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'profitability_matrix': profitability_matrix,
        'category_profit': category_profit,
        'near_expiry': near_expiry,
        'current_date': today.strftime("%Y-%m-%d"),
        'report_range': f"{thirty_days_ago.strftime('%b %d')} - {today.strftime('%b %d')}"
    }

    return render(request, 'InvApp/report_analysis.html', context)
