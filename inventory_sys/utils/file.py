

logger = logging.getLogger(__name__)

def get_latest_buying_price_subquery():
    """Returns a subquery for the latest buying price of a product."""
    latest_batch = ProductBatch.objects.filter(
        product=OuterRef('product')
    ).order_by('-stock_date').values('buying_price')[:1]
    return Subquery(latest_batch, output_field=FloatField())

def calculate_batch_values(buying_price_subquery):
    """Calculates product-level inventory metrics using the latest buying price."""
    return ProductBatch.objects.values(
        'product__name', 'product__product_id', 'product__category__name'
    ).annotate(
        buying_price=buying_price_subquery,
        quantity=Sum('initial_quantity'),
        total_value=Sum(
            ExpressionWrapper(
                F('initial_quantity') * buying_price_subquery,
                output_field=FloatField()
            )
        )
    ).order_by('-total_value')

def calculate_total_inventory_value(batch_values):
    """Sums total inventory value from batch values."""
    return sum(item['total_value'] for item in batch_values) or 0.0

def process_inventory_data(batch_values, total_inventory_value):
    """Formats inventory data for template rendering."""
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
    """Fetches low stock items and critical stock count."""
    critical_threshold = 0.2  
    low_stock = Product.objects.annotate(
        critical_level=F('reorder_level') * critical_threshold
    ).filter(quantity_in_stock__lt=F('reorder_level')).values(
        'product_id', 'name', 'quantity_in_stock',
        'reorder_level', 'reorder_quantity', 'critical_level'
    )
    critical_count = low_stock.filter(quantity_in_stock__lt=F('critical_level')).count()
    return low_stock, critical_count

def calculate_total_products():
    """Counts total products."""
    return Product.objects.count()

def calculate_average_reorder_quantity():
    """Calculates average reorder quantity."""
    return Product.objects.aggregate(avg_reorder=Avg('reorder_quantity'))['avg_reorder'] or 0.0

def calculate_category_data(total_inventory_value):
    """Aggregates category-level inventory metrics."""
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
            ) * 100.0 / (total_inventory_value or 1),
            output_field=FloatField()
        )
    ).values(
        'id', 'name', 'product_count', 'batch_count',
        'total_quantity', 'total_value', 'percentage'
    ).order_by('-total_value')

def process_category_data(category_data):
    """Formats category data for template rendering."""
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
    """Generates monthly inventory value trends."""
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
        current_month += relativedelta(months=1)
    return labels, values

def get_recent_orders(thirty_days_ago):
    """Fetches orders from the last 30 days."""
    return Order.objects.filter(order_date__gte=thirty_days_ago)

def calculate_total_revenue(orders):
    """Calculates total revenue from orders."""
    return orders.aggregate(total=Sum('total_price', output_field=FloatField()))['total'] or 0.0

def get_previous_period_orders(thirty_days_ago):
    """Fetches orders from the previous 30-day period."""
    previous_period_start = thirty_days_ago - timezone.timedelta(days=30)
    return Order.objects.filter(
        order_date__gte=previous_period_start,
        order_date__lt=thirty_days_ago
    )

def calculate_revenue_growth(total_revenue, previous_revenue):
    """Calculates revenue growth percentage."""
    return ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue else 0.0

def calculate_cogs_and_gross_profit(orders,total_revenue, buying_price_subquery):
    """Calculates COGS, gross profit, and gross margin."""
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
    """Counts total orders."""
    return orders.count()

def calculate_avg_order_value(total_revenue, total_orders):
    """Calculates average order value."""
    return (total_revenue / total_orders) if total_orders else 0.0

def get_top_selling_products(orders, buying_price_subquery):
    """Fetches top 10 selling products by revenue."""
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
        ),
        profit=ExpressionWrapper(
            F('revenue') - F('cost'),
            output_field=FloatField()
        ),
        margin=ExpressionWrapper(
            (F('revenue') - F('cost')) / F('revenue') * 100,
            output_field=FloatField()
        )
    ).order_by('-revenue')[:10]

    return [
        {
            'product__name': item['product__name'],
            'product__category__name': item['product__category__name'],
            'qty': item['qty'] or 0,
            'revenue': item['revenue'] or 0.0,
            'cost': item['cost'] or 0.0,
            'profit': item['profit'] or 0.0,
            'margin': item['margin'] or 0.0
        }
        for item in top_selling
    ]

def calculate_top_selling_metrics(processed_top_selling, total_revenue):
    """Calculates metrics for top 5 selling products."""
    top5_revenue = sum(item['revenue'] for item in processed_top_selling[:5]) or 0.0
    top5_percentage = (top5_revenue / total_revenue * 100) if total_revenue else 0.0
    other_percentage = 100.0 - top5_percentage if total_revenue else 0.0
    top_product_names = [item['product__name'] for item in processed_top_selling]
    top_product_values = [item['revenue'] for item in processed_top_selling]
    return top5_revenue, top5_percentage, other_percentage, top_product_names, top_product_values

def calculate_monthly_sales(today, twelve_months_ago, orders, buying_price_subquery):
    """Generates monthly sales and profit trends."""
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
        ),
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
            'gross_profit': item['gross_profit'] or 0.0,
            'margin': item['margin'] or 0.0
        }
        for item in monthly_sales
    ]

    labels, sales_data, profit_data = [], [], []
    current_month = twelve_months_ago.replace(day=1)
    while current_month <= today:
        month_data = next(
            (item for item in processed_monthly_sales if item['month'] and item['month'].month == current_month.month and item['month'].year == current_month.year),
            {'total_sales': 0.0, 'gross_profit': 0.0, 'order_count': 0, 'cogs': 0.0, 'margin': 0.0}
        )
        labels.append(current_month.strftime('%b %Y'))
        sales_data.append(float(month_data['total_sales']))
        profit_data.append(float(month_data['gross_profit']))
        current_month += relativedelta(months=1)
    return labels, sales_data, profit_data

def calculate_sales_trend(total_revenue, previous_revenue, total_orders, previous_period_orders):
    """Calculates sales trend metrics."""
    sales_change = calculate_revenue_growth(total_revenue, previous_revenue)
    current_period_units = total_orders
    previous_period_units = previous_period_orders.aggregate(total=Sum('quantity'))['total'] or 0
    units_change = ((current_period_units - previous_period_units) / previous_period_units * 100) if previous_period_units else 0.0
    current_avg_order = calculate_avg_order_value(total_revenue, total_orders)
    previous_avg_order = (previous_revenue / previous_period_orders.count()) if previous_period_orders.count() else 0.0
    aov_change = ((current_avg_order - previous_avg_order) / previous_avg_order * 100) if previous_avg_order else 0.0
    return total_revenue, previous_revenue, sales_change, current_period_units, previous_period_units, units_change, current_avg_order, previous_avg_order, aov_change

def calculate_daily_sales(orders, buying_price_subquery):
    """Generates daily sales data."""
    return orders.annotate(
        buying_price=buying_price_subquery
    ).values(
        'order_date', 'id', 'product__name', 'quantity', 'total_price'
    ).annotate(
        unit_price=ExpressionWrapper(
            F('total_price') / F('quantity'),
            output_field=FloatField()
        ),
        cost=ExpressionWrapper(
            F('quantity') * F('buying_price'),
            output_field=FloatField()
        ),
        profit=ExpressionWrapper(
            F('total_price') - F('cost'),
            output_field=FloatField()
        )
    ).order_by('-order_date')

def calculate_total_units(orders):
    """Sums total units sold."""
    return orders.aggregate(total=Sum('quantity'))['total'] or 0

def calculate_profitability_matrix(orders, buying_price_subquery):
    """Calculates product-level profitability metrics."""
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
        volume=Sum('quantity'),
        profit=ExpressionWrapper(
            F('revenue') - F('cogs'),
            output_field=FloatField()
        ),
        margin=ExpressionWrapper(
            (F('revenue') - F('cogs')) / F('revenue') * 100,
            output_field=FloatField()
        )
    ).order_by('-profit')

def calculate_category_profit(orders, buying_price_subquery):
    """Calculates category-level profitability metrics."""
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
        ),
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
            'margin': item['margin'] or 0.0
        }
        for item in category_profit
    ]

def get_near_expiry_products(today):
    """Fetches products expiring within the next year."""
    return ProductBatch.objects.filter(
        expiry_date__range=[today, today + timezone.timedelta(days=365)]
    ).select_related('product').values(
        'product__name', 'expiry_date', 'initial_quantity'
    ).order_by('expiry_date')
def report_analysis(request):
    """Generates a comprehensive inventory and sales report."""
    try:
        # Initialize dates
        today = timezone.now().date()
        thirty_days_ago = today - timezone.timedelta(days=30)
        twelve_months_ago = today - timezone.timedelta(days=365)

        # Inventory calculations
        logger.info("Getting latest buying price subquery...")
        buying_price_subquery = get_latest_buying_price_subquery()
        logger.info("Calculating batch values...")
        batch_values = calculate_batch_values(buying_price_subquery)
        logger.info("Calculating total inventory value...")
        total_inventory_value = calculate_total_inventory_value(batch_values)
        logger.info("Processing inventory data...")
        inventory_data = process_inventory_data(batch_values, total_inventory_value)
        logger.info("Getting low stock items...")
        low_stock_items, critical_stock_count = get_low_stock_items()
        logger.info("Calculating total products...")
        total_products = calculate_total_products()
        logger.info("Calculating average reorder quantity...")
        average_reorder_quantity = calculate_average_reorder_quantity()
        logger.info("Calculating category data...")
        category_data = process_category_data(calculate_category_data(total_inventory_value))
        logger.info("Calculating inventory trend...")
        inventory_trend_labels, inventory_trend_values = calculate_inventory_trend(today, twelve_months_ago)

        # Sales calculations
        logger.info("Getting recent orders...")
        orders = get_recent_orders(thirty_days_ago)
        logger.info("Calculating total revenue...")
        total_revenue = calculate_total_revenue(orders)
        logger.info("Getting previous period orders...")
        previous_period_orders = get_previous_period_orders(thirty_days_ago)
        logger.info("Calculating previous revenue...")
        previous_revenue = calculate_total_revenue(previous_period_orders)
        logger.info("Calculating revenue growth...")
        revenue_growth = calculate_revenue_growth(total_revenue, previous_revenue)
        logger.info("Calculating COGS and gross profit...")
        total_cogs, gross_profit, gross_margin = calculate_cogs_and_gross_profit(orders, buying_price_subquery)
        logger.info("Calculating total orders...")
        total_orders = calculate_total_orders(orders)
        logger.info("Calculating average order value...")
        avg_order_value = calculate_avg_order_value(total_revenue, total_orders)
        logger.info("Getting top selling products...")
        top_selling_processed = get_top_selling_products(orders, buying_price_subquery)
        logger.info("Calculating top selling metrics...")
        top5_revenue, top5_percentage, other_percentage, top_product_names, top_product_values = calculate_top_selling_metrics(top_selling_processed, total_revenue)
        logger.info("Calculating monthly sales...")
        monthly_labels, monthly_sales_data, monthly_profit_data = calculate_monthly_sales(today, twelve_months_ago, orders, buying_price_subquery)
        logger.info("Calculating sales trend metrics...")
        sales_trend_metrics = calculate_sales_trend(total_revenue, previous_revenue, total_orders, previous_period_orders)
        logger.info("Calculating daily sales...")
        daily_sales = calculate_daily_sales(orders, buying_price_subquery)
        logger.info("Calculating total units...")
        total_units = calculate_total_units(orders)
        logger.info("Calculating profitability matrix...")
        profitability_matrix = calculate_profitability_matrix(orders, buying_price_subquery)
        logger.info("Calculating category profit...")
        category_profit = calculate_category_profit(orders, buying_price_subquery)
        logger.info("Getting near expiry products...")
        near_expiry = get_near_expiry_products(today)

        # Prepare context for template
        context = {
            'total_revenue': total_revenue,
            'revenue_growth': round(revenue_growth, 2),
            'gross_profit': gross_profit,
            'gross_margin': round(gross_margin, 2),
            'avg_order_value': avg_order_value,
            'total_orders': total_orders,
            'default_start_date': thirty_days_ago,
            'default_end_date': today,
            'total_inventory_value': total_inventory_value,
            'low_stock_count': low_stock_items.count(),
            'critical_stock_count': critical_stock_count,
            'expiring_soon_count': near_expiry.count(),
            'inventory': inventory_data,
            'inventory_trend_labels': inventory_trend_labels,
            'inventory_trend_values': inventory_trend_values,
            'low_stock_items': low_stock_items,
            'total_products': total_products,
            'average_reorder_quantity': round(average_reorder_quantity, 2),
            'category': category_data,
            'category_names': [cat['name'] for cat in category_data],
            'category_values': [cat['total_value'] for cat in category_data],
            'top_selling': top_selling_processed,
            'top_product_names': top_product_names,
            'top_product_values': top_product_values,
            'top5_percentage': round(top5_percentage, 2),
            'other_percentage': round(other_percentage, 2),
            'monthly_sales': monthly_sales_data,
            'monthly_labels': monthly_labels,
            'monthly_profit_data': monthly_profit_data,
            'sales_trend': sales_trend_metrics,
            'daily_sales': daily_sales,
            'total_units': total_units,
            'profitability_matrix': profitability_matrix,
            'category_profit': category_profit,
            'near_expiry': near_expiry,
            'current_date': today.strftime("%Y-%m-%d"),
            'report_range': f"{thirty_days_ago.strftime('%b %d')} - {today.strftime('%b %d')}"
        }
        return render(request, 'InvApp/report_analysis.html', context)

    except Exception as e:
        logger.error(f"Error in report_analysis: {e}")
        return render(request, 'InvApp/report_analysis.html', {'error': str(e)})