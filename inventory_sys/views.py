from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import RegistrationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from datetime import datetime, date
from django.urls import reverse
from .models import Customer, Product, Order,User, Category, Supplier
from django.http import HttpResponse
from django.utils import timezone
from .models import Order, Stock, StockAdjustment
from django.db.models import Sum
from django.db.models import F, Avg
from django.http import JsonResponse



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
    if request.method == "POST":
        logout(request)
        return redirect('login')  # Redirect to login after logout
    return render(request, 'Invapp/logout.html')   


def product_list(request):

    suppliers = Supplier.objects.all()
    categories = Category.objects.all()
    products = Product.objects.all()
    
    paginator = Paginator(products, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        print(request.POST)

        product_name = request.POST.get('name')
        buying_price = request.POST.get('buying_price')
        quantity_in_stock = request.POST.get('quantity_in_stock')
        supplier_id = request.POST.get('supplier_id')
        units = request.POST.get('units')
        selling_price = request.POST.get('selling_price')
        manufacture_date = request.POST.get('manufacture_date')
        reorder_quantity = request.POST.get('reorder_quantity')
        reorder_level = request.POST.get('reorder_level')

        

        # Validate Category
        if  category_id is None:
            return HttpResponse("Error: Category is required!", status=400)

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return HttpResponse("Error: Category not found!", status=400)

        # Validate Supplier
        try:
            supplier = Supplier.objects.get(id=supplier_id)
        except Supplier.DoesNotExist:
            return HttpResponse("Error: Supplier not found!", status=400)

        # Create Product
        Product.objects.create(
            name=product_name,
            buying_price=buying_price,
            quantity_in_stock=quantity_in_stock,
            supplier=supplier,  # Assign supplier object
            units=units,
            category=category,  # Assign category object
            selling_price=selling_price,
            manufacture_date=manufacture_date,
            reorder_quantity=reorder_quantity,
            reorder_level=reorder_level
        )

        messages.success(request, 'Product added successfully!')
        return redirect('product_list')

    return render(request, 'Invapp/product_list.html', {'page_obj': page_obj, 'suppliers': suppliers, 'categories': categories})


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

    # Pagination
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
        discounts = request.POST.getlist('productDiscount[]')
        order_date = request.POST.get('orderDate', date.today().strftime('%Y-%m-%d'))
        final_total = request.POST.get('finalTotal')
        
        product_list = []
        for i in range(len(products)):
            order = {
                'product_id': products[i],
                'quantity': int(order_quantities[i]),
                'unit': units[i],
                'price_per_unit': float(price_per_units[i]),
                'total_price': float(total_prices[i]),
                'discount': float(discounts[i]),  # Fix KeyError
                'order_date': order_date,
                'final_total': float(final_total)  # Fix KeyError
            }
            product_list.append(order)        
         
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            print("Error: Customer not found")  
            return redirect('order_page')

        payment_method = request.POST.get('paymentMethod', 'cash')   
       
        for item in product_list:
            try:
                product_id = item['product_id']
                unit_id = item['unit']
                unit_price = item['price_per_unit'] 
                total_price = item['total_price']
                quantity = item['quantity']
                discount = item['discount']  

               
                product = Product.objects.get(product_id=product_id)

                if quantity <= 0 or quantity > product.quantity_in_stock:
                    print(f"Error: Invalid quantity {quantity} for product {product_id}")
                    continue 

                Order.objects.create(
                    customer=customer,
                    product=product,
                    quantity=quantity,
                    price_per_unit=unit_price,
                    total_price=total_price,
                    units=unit_id,
                    payment_method=payment_method, 
                    discount=discount, 
                    order_date=order_date,
                    final_total=final_total, 
                )

                product.quantity_in_stock -= quantity
                product.save()
                
            except Product.DoesNotExist:
                print(f"Error: Product {product_id} not found")  
                continue 

        return redirect('order_page')

    return render(request, 'Invapp/order_page.html')

def get_sales_data(request):
    orders = Order.objects.values('order_date').annotate(total_quantity=Sum('quantity')).order_by('order_date')

    labels = [order['order_date'].strftime('%b') for order in orders]  # Get month names
    data = [order['total_quantity'] for order in orders]  # Get total quantity per month

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

        total_quantity_in_stock = Product.objects.aggregate(total_stock=Sum('quantity_in_stock'))['total_stock']
        tol_adjustments = StockAdjustment.objects.filter(adjustment_type='subtract').aggregate(total=Sum('quantity'))['total'] or 0      
        adjust_total  = total_adjustments + tol_adjustments
        total_stock_in = total_new_stock + total_quantity_in_stock 
        average_adjustments =+adjust_total
        stock_out = total_quantity + tol_adjustments
        closing_stock = total_stock_in + stock_out

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
        'stock_transactions': stock_transactions,
        'total_new_stock': total_new_stock,
        'total_quantity_in_stock': total_quantity_in_stock,
        'total_stock_in': total_stock_in,
        'average_adjustments': average_adjustments,
        'tol_adjustments': tol_adjustments,
        'closing_stock': closing_stock,
        'total_quantity_in_stock': total_quantity_in_stock,
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



# @login_required
def home_view(request):
    orders = Order.objects.all()
    low_stock_items = Product.objects.filter(quantity_in_stock__lt=F('reorder_level')).values(
    'name', 'quantity_in_stock', 'reorder_level', 'reorder_quantity'
)

    total_orders = Order.objects.count()
    total_customers = Order.objects.values('customer').distinct().count()
    total_cash_made = Order.objects.aggregate(Sum('final_total'))['final_total__sum'] or 0
    total_quantity = Order.objects.aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_products = Product.objects.count() 
    low_stock_count = low_stock_items.count() 
    categories = Category.objects.count() 
    suppliers = Supplier.objects.count()  
    
    # Stock Data
    total_stock_in = Stock.objects.aggregate(Sum('new_stock'))['new_stock__sum'] or 0
    total_stock_out = StockAdjustment.objects.filter(adjustment_type='subtract').aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_quantity_in_stock = Product.objects.aggregate(Sum('quantity_in_stock'))['quantity_in_stock__sum'] or 0
    
         
    total_new_stock = Stock.objects.aggregate(total=Sum('new_stock'))['total'] or 0
    total_adjustments = StockAdjustment.objects.filter(adjustment_type='add').aggregate(total=Sum('quantity'))['total'] or 0
    total_stock_in = total_new_stock + total_adjustments 
    tol_adjustments = StockAdjustment.objects.filter(adjustment_type='subtract').aggregate(total=Sum('quantity'))['total'] or 0
    stock_out = total_quantity + tol_adjustments
    adjust_total  = total_adjustments + tol_adjustments
    average_adjustments =+adjust_total

    # Recent Orders
    recent_orders = Order.objects.order_by('-order_date')[:5].select_related('customer')

    context = {
        'stock_out': stock_out,
        'total_orders': total_orders,
        'categories': categories,
        'suppliers': suppliers,
        'total_customers': total_customers,
        'total_cash_made': total_cash_made,
        'total_quantity': total_quantity,
        'total_products': total_products,
        'total_stock_in': total_stock_in,
        'total_stock_out': total_stock_out,
        'total_quantity_in_stock': total_quantity_in_stock,
        'low_stock_items': low_stock_items,
        'recent_orders': recent_orders,
        'low_stock_count': low_stock_count,
        'adjust_total': adjust_total,
        'total_new_stock': total_new_stock,
        'total_adjustments': total_adjustments,
        'tol_adjustments': tol_adjustments,
        'average_adjustments': average_adjustments,
    }

    return render(request, 'InvApp/home.html', context)


def catalog(request):
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    if request.method == 'POST':
        if 'add_category' in request.POST:
            name = request.POST.get('category_name')
            description = request.POST.get('category_description')
            category_type = request.POST.get('category_type')

            if name and category_type:
                Category.objects.create(name=name, description=description, category_type=category_type)
                return redirect('catalog')

        if 'add_supplier' in request.POST:
            name = request.POST.get('supplier_name')
            contact_person = request.POST.get('supplier_contact')
            phone = request.POST.get('supplier_phone')
            email = request.POST.get('supplier_email')
            address = request.POST.get('supplier_address')

            if name and phone:
                Supplier.objects.create(name=name, contact_person=contact_person, phone=phone, email=email, address=address)
                return redirect('catalog')
            
        categories = Category.objects.count() 
        suppliers = Supplier.objects.count()   

    context = {'categories': categories, 'suppliers': suppliers,}
    return render(request, 'InvApp/catalog.html', context)



def stock_adjustments(request):
    products = Product.objects.all()
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
        adjust_total = total_adjustments + tol_adjustments
        average_adjustments = adjust_total
        
        stock_adjustments_list.append({
            'product_name': product.name,
            'stock_in': stock_in,
            'stock_out': stock_out,
            'adjustments': adjustments,
        })
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        adjustment_type = request.POST.get('adjustment_type')
        quantity = request.POST.get('quantity')
        reason = request.POST.get('reason')
        adjustment_date = request.POST.get('adjustmentDate')
        
        product = Product.objects.get(product_id=product_id)
        
        if not quantity or not quantity.isdigit():
            messages.error(request, "Invalid quantity.")
            return redirect('stock_adjustments')
        
        quantity = int(quantity)
        
        if adjustment_date:
            try:
                adjustment_date = datetime.strptime(adjustment_date, "%Y-%m-%d").date()
            except ValueError:
                messages.error(request, "Invalid date format.")
                return redirect('stock_adjustments')
        else:
            adjustment_date = datetime.today().date()
        
        adjustment = StockAdjustment.objects.create(
            product=product,
            adjustment_type=adjustment_type,
            quantity=quantity,
            reason=reason,
            adjustment_date=adjustment_date
        )
        
        if hasattr(adjustment, 'apply_adjustment'):
            adjustment.apply_adjustment()
        else:
            messages.error(request, "Stock adjustment method not found.")
            return redirect('stock_adjustments')
        
        messages.success(request, "Stock adjusted successfully!")
        return redirect('stock_adjustments')
    
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
        'adjust_total': adjust_total,
        'average_adjustments': average_adjustments,
    }
    
    return render(request, 'InvApp/adjust.html', context)
