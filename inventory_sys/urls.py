from django.urls import path
from . import views
from .views import HomeDashboardView
from .views import BulkUpdateOrdersView

urlpatterns = [
    # path('', views.home_view, name='home'),
    path('', HomeDashboardView.as_view(), name='home'),  
    path('Invapp/logout/', views.logout_view, name='logout'),  
    path('Invapp/confirm_logout/', views.confirm_logout, name='confirm_logout'),  
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
    path('report/', views.report_page, name='report'),
    path('stock/add/', views.add_stock, name='add_stock'),
    path('stock-adjustments/', views.stock_adjustments, name='stock_adjustments'),
    path('product/catalog/', views.catalog, name='catalog'),
    path('get-sales-data/', views.get_sales_data, name='get_sales_data'),
    path('get-stock-data/', views.get_stock_data, name='get_stock_data'),
    path('report_analysis/', views.report_analysis, name='report_analysis'),
    path('product_history/<int:product_id>/', views.product_history, name='product_history'),
    path('orders/', views.order_page, name='order_page'),
    path('orders/place/', views.place_order, name='place_order'),
    path('orders/bulk-update/', BulkUpdateOrdersView.as_view(), name='bulk_update_orders'),
    path('orders/export/', views.export_orders_csv, name='export_orders_csv'),
    path('report_analysis/', views.report_analysis, name='report_analysis'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    # path('export_dashboard_csv/', views.export_dashboard_csv, name='export_dashboard_csv'),
    
]
 

