import csv
from django.http import HttpResponse
from django.http import JsonResponse
from .forms import ExportCSVForm
from django.utils import timezone
from django.core.exceptions import ValidationError
import logging
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from django.db.models import Sum
from .models import Order, Stock, StockAdjustment, ProductBatch


logger = logging.getLogger(__name__)

def export_csv(request, model, queryset, field_mappings, filename_prefix):
    form = ExportCSVForm(request.GET)
    if form.is_valid():
        try:
            selected_date = form.cleaned_data['order_date']

            # Filter the queryset based on the selected date if applicable
            if 'order_date' in field_mappings:
                queryset = queryset.filter(**{field_mappings['order_date']: selected_date})

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{selected_date.strftime("%Y-%m-%d")}.csv"'

            writer = csv.writer(response)
            headers = [header for header, _ in field_mappings.items()]
            writer.writerow(headers)

            for obj in queryset:
                row = []
                for _, field in field_mappings.items():
                    if callable(field):
                        row.append(field(obj))
                    else:
                        value = getattr(obj, field, 'N/A')
                        if isinstance(value, timezone.datetime):
                            value = value.strftime("%Y-%m-%d")
                        row.append(value)
                writer.writerow(row)

            return response

        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return JsonResponse({'error': f'Error exporting CSV: {str(e)}'}, status=500)
    else:
        logger.error(f"Form validation errors: {form.errors}")
        return JsonResponse({'errors': form.errors}, status=400)
    


logger = logging.getLogger(__name__)

def get_sales_data(product, time_period='monthly'):
    today = timezone.now().date()
    sales_labels = []
    sales_data = []

    if time_period == 'daily':
        # Last 30 days
        for i in range(29, -1, -1):  # range(0, 30)
            day = today - timedelta(days=i)
            sales_labels.append(day.strftime("%Y-%m-%d"))
            daily_sales = Order.objects.filter(
                product=product,
                order_date=day
            ).aggregate(total=Sum('quantity'))['total'] or 0
            sales_data.append(daily_sales)
    
    elif time_period == 'weekly':
        # Last 52 weeks
        for i in range(51, -1, -1):  # range(0, 52)
            week_start = today - timedelta(weeks=i, days=today.weekday())
            week_end = week_start + timedelta(days=6)
            sales_labels.append(f"Week {week_start.strftime('%Y-%m-%d')} - {week_end.strftime('%Y-%m-%d')}")
            weekly_sales = Order.objects.filter(
                product=product,
                order_date__gte=week_start,
                order_date__lte=week_end
            ).aggregate(total=Sum('quantity'))['total'] or 0
            sales_data.append(weekly_sales)
    
    elif time_period == 'quarterly':
        # Last 4 quarters
        for i in range(3, -1, -1):  # range(0, 4)
            quarter_start = today - relativedelta(months=(i+1)*3, day=1)
            quarter_end = quarter_start + relativedelta(months=3) - timedelta(days=1)
            sales_labels.append(f"Q{((quarter_start.month - 1) // 3) + 1} {quarter_start.year}")
            quarterly_sales = Order.objects.filter(
                product=product,
                order_date__gte=quarter_start,
                order_date__lte=quarter_end
            ).aggregate(total=Sum('quantity'))['total'] or 0
            sales_data.append(quarterly_sales)
    
    elif time_period == 'yearly':
        # Last 10 years
        for i in range(9, -1, -1):  # range(0, 10)
            year_start = today.replace(year=today.year - i, month=1, day=1)
            year_end = year_start.replace(year=year_start.year + 1, month=1, day=1) - timedelta(days=1)
            sales_labels.append(str(year_start.year))
            yearly_sales = Order.objects.filter(
                product=product,
                order_date__gte=year_start,
                order_date__lte=year_end
            ).aggregate(total=Sum('quantity'))['total'] or 0
            sales_data.append(yearly_sales)
    
    else:
        # Default to monthly
        for i in range(11, -1, -1):  # range(0, 12)
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


def get_product_batches(product):
    return ProductBatch.objects.filter(product=product).select_related('product', 'supplier').order_by('-stock_date')

def get_orders(product):
    return Order.objects.filter(product=product).select_related('batch_sku', 'customer').order_by('-order_date')

def get_adjustments(product):
    return StockAdjustment.objects.filter(product=product).select_related('batch').order_by('-created_at')


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

    # combined_activity.sort(key=lambda x: x['date'], reverse=True)
    return combined_activity

