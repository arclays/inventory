from django import forms
from .models import Product
from django.contrib.auth.models import User
from .models import Customer, Order

# class ProductForm(forms.ModelForm):
#     class Meta:
#         model = Product
#         fields = '__all__'
#         labels = {
#             'product_id': 'Product ID',
#             'name': 'Product Name',
#             'sku': 'SKU',
#             'price': 'Price', 
#             'units': 'units',
#             ' quantity_in_stock': ' quantity_in_stock',
#         }
            
#         widgets = {
#            'product_id': forms.NumberInput(attrs={ 'placeholder': 'e.g 1 ', 'class': 'form-control'}),
#         #    'selling_price': forms.NumberInput(attrs={ 'placeholder': 'e.g shs1000 ', 'class': 'form-control'}),
#            'units': forms.TextInput(attrs={ 'placeholder': 'e.g peice/dozen', 'class': 'form-control'}),
#             'name': forms.TextInput(attrs={ 'placeholder': 'e.g skirt ', 'class': 'form-control'}),
#             'price': forms.NumberInput(attrs={ 'placeholder': 'e.g shs1000.0 ', 'class': 'form-control'}),
#             'category': forms.TextInput(attrs={ 'placeholder': 'your category', 'class': 'form-control'}),
#             'quantity_in_stock': forms.NumberInput(attrs={ 'placeholder': 'e.g 1 ', 'class': 'form-control'}),
#             'supplier': forms.TextInput(attrs={ 'placeholder': 'your supplier ', 'class': 'form-control'}),
#             'reorder_level': forms.NumberInput(attrs={ 'placeholder': 'e.g 5 ', 'class': 'form-control'}),
#             'reorder_quantity': forms.NumberInput(attrs={ 'placeholder': 'e.g 10 ', 'class': 'form-control'}),
        
#         }  

class  RegistrationForm(forms.Form):
    username = forms.CharField()
    email = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Password_confirm")


#     class Meta:
#         models = User
#         feilds =[ 'username', 'email', 'password' , 'password_confirm'] 

#         def clean(self): 
#             cleaned_data = super().clean()
#             password = cleaned_data.get('password')
#             password_confirm = cleaned_data.get('password_confirm')

#             if password and password_confirm and password_confirm.lower() != password:
#                 raise forms.validationerror('Invalid password')
#             return cleaned_data
  

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone' , 'address']

# class OrderForm(forms.ModelForm):
#     class Meta:
#         model = Order
#         fields = '__all__'        

        

# def place_order(request):
#     if request.method == 'POST':
#         customer_id = request.POST.get('orderCustomer') 
#         quantity = request.POST.get('orderQuantity')

#         products = request.POST.getlist('products[]')
#         order_quantities = request.POST.getlist('orderQuantity[]')
#         units = request.POST.getlist('units[]')
#         price_per_units = request.POST.getlist('pricePerUnit[]')
#         total_prices = request.POST.getlist('totalPrice[]')


#         product_list = []
#         for i in range(len(products)):
#             order = {
#                 'product_id': products[i],
#                 'quantity': int(order_quantities[i]),
#                 'unit': units[i],
#                 'price_per_unit': float(price_per_units[i]),
#                 'total_price': float(total_prices[i])
#             }
#             product_list.append(order)
#             # total_amount=total_amount+float(total_prices[i])
#         # print(product_list)



#         customer = Customer.objects.get(id=customer_id)

#         payment_method = request.POST.get('paymentMethod', 'cash')  
#         discount = request.POST.get('discount', '0.00') 
#         # Convert discount to float 
#         try:
#             discount = float(discount)
#         except ValueError:
#             discount = 0.0 



#         # store items
#         for item in product_list:
#             product_id =item['product_id']
#             unit_id = item['unit']
#             unit_price = item['unit_price']
#             total_price = item['total_price']
#             quantity = item['quantity']
            

#             product = Product.objects.get(product_id=product_id)
#             quantity = int(quantity)
#             if quantity <= 0 or quantity > product.quantity_in_stock:
#                 pass
#             else:
#                 # Create Order 
#                Order.objects.create(
#                    customer=customer,
#                    product=product,
#                    quantity=quantity,
#                    price_per_unit=unit_price,
#                    total_price=total_price,
#                    units=unit_id,
#                    payment_method=payment_method, 
#                    discount=discount,  
# )

#                 # Deduct  stock
#         product.quantity_in_stock -= quantity
#         product.save()


#         return redirect('order_page')

#     return render(request, 'Invapp/order_page.html')





    # <!-- Stock Adjustments -->
    # <h4 class="mt-4 text-primary">Stock Adjustments</h4>
    # <table class="table table-bordered">
    #     <thead class="table-header">
    #         <tr>
    #             <th>Product</th>
    #             <th>Adjustment Type</th>
    #             <th>Quantity</th>
    #             <th>Date</th>
    #             <th>Reason</th>
    #         </tr>
    #     </thead>
    #     <tbody>
    #         {% for adjustment in stock_adjustments %}
    #         <tr>
    #             <td>{{ adjustment.product.name }}</td>
    #             <td>{{ adjustment.adjustment_type }}</td>
    #             <td>{{ adjustment.quantity }}</td>
    #             <td>{{ adjustment.adjustment_date }}</td>
    #             <td>{{ adjustment.reason }}</td>
    #         </tr>
    #         {% empty %}
    #         <tr>
    #             <td colspan="5" class="text-center">No stock adjustments recorded.</td>
    #         </tr>
    #         {% endfor %}
    #     </tbody>
    # </table>
    # <!-- Modal for Stock Adjustment -->
    # <div class="modal fade" id="stockAdjustmentModal" tabindex="-1" aria-labelledby="stockAdjustmentModalLabel" aria-hidden="true">
    #     <div class="modal-dialog">
    #       <div class="modal-content">
    #         <div class="modal-header">
    #           <h5 class="modal-title" id="stockAdjustmentModalLabel">Stock Adjustment</h5>
    #           <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
    #         </div>
    #         <div class="modal-body">
    #           <form method="POST"  action="{% url 'adjust_stock' %}">
    #             {% csrf_token %}
    #             <div class="form-group mb-3">
    #                 <label for="productName">Product Name </label>
    #                 <select id="productName" name="product_id" class="form-control" required>
    #                     <option value="">Select a product</option>
    #                     {% for product in products %}
    #                         <option value="{{ product.product_id }}">{{ product.name }}</option>
    #                     {% endfor %}
    #                 </select>
    #             </div>
    #             <div class="form-group mb-3">
    #               <label for="adjustment_type" class="form-label">Adjustment Type</label>
    #               <select class="form-select" id="adjustment_type" name="adjustment_type" required>
    #                 <option value="add">Add Stock</option>
    #                 <option value="subtract">Subtract Stock</option>
    #               </select>
    #             </div>
    #             <div class="form-group mb-3">
    #               <label for="quantity" class="form-label">Quantity</label>
    #               <input type="number" class="form-control" id="quantity" name="quantity" min="1" required>
    #             </div>
    #             <div class="form-group mb-3">
    #                 <label for="adjustmentDate">Adjustment Date</label>
    #                 <input type="date" id="adjustmentDate" name="adjustmentDate" class="form-control" required>
    #             </div>
    #             <div class="form-group mb-3">
    #               <label for="reason" class="form-label">Reason</label>
    #               <textarea class="form-control" id="reason" name="reason" rows="3" required></textarea>
    #             </div>
    #             <div class="modal-footer">
    #               <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
    #               <button type="submit" class="btn btn-primary">Apply Adjustment</button>
    #             </div>
    #           </form>
    #         </div>
    #       </div>
    #     </div>
    #   </div>


