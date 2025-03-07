from django.urls import path
from . import views



urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'), 
    # path('logout/', views.logout_view, name='logout'),
    path('Invapp/logout/', views.login_view, name='logout'),  
    path('register/', views.register_view, name='register'), 
    path('protected/', views.ProtectedView.as_view(), name='protected'),
    path('customers/', views.customer_list, name='customer_list'),
    path('stock/', views.stock_view, name='stock'),
    path('stockchange/', views.stock_change, name='stock_change'),
    path('add-stock/', views.add_stock, name='add_stock'),
    path('products/', views.product_list, name='product_list'),
    path('products/update/<int:product_id>/', views.product_update, name='product_update'),
    path('customers/edit/<int:customer_id>/', views.customer_edit, name='customer_edit'),
    path('customers/delete/<int:customer_id>/', views.customer_confirm_delete, name='customer_confirm_delete'),
    path('products/delete/<int:product_id>/', views.product_confirm_delete, name='product_confirm_delete'),
    path('order/', views.order_page, name='order_page'),
    path('place_order/', views.place_order, name='place_order'),
    path('report/', views.report, name='report'),
    path('stock-transactions-api/', views.stock_transaction_api, name='stock_transaction_api'),
   

   
] 

