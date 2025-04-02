from django.urls import path
from . import views



urlpatterns = [
    path('', views.home_view, name='home'),
    path('Invapp/logout/', views.logout_view, name='logout'),  
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('customers/', views.customer_list, name='customer_list'),
    path('stock/', views.stock_view, name='stock'),
    path('add-stock/', views.add_stock, name='add_stock'),
    path('products/', views.product_list, name='product_list'),
    path('products/update/<int:product_id>/', views.product_update, name='product_update'),
    path('customers/edit/<int:customer_id>/', views.customer_edit, name='customer_edit'),
    path('customers/delete/<int:customer_id>/', views.customer_confirm_delete, name='customer_confirm_delete'),
    path('products/delete/<int:product_id>/', views.product_confirm_delete, name='product_confirm_delete'),
    path("get-selling-price/<int:product_id>/", views.get_selling_price, name="get_selling_price"),
    path('order/', views.order_page, name='order_page'),
    path('place_order/', views.place_order, name='place_order'),
    path('report/', views.report_page, name='report'),
    path('stock/add/', views.add_stock, name='add_stock'),
    path('reorder/', views.reorder_alerts, name='reorder_alerts'),
    path('stock-adjustments/', views.stock_adjustments, name='stock_adjustments'),
    path('product/catalog/', views.catalog, name='catalog'),
    path('get-sales-data/', views.get_sales_data, name='get_sales_data'),
    path('get-stock-data/', views.get_stock_data, name='get_stock_data'),
   

   
] 

