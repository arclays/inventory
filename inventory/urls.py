"""
URL configuration for inventory project.

The `urlpatterns` list routes URLs to views. For more information see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from inventory_sys.views import HomeDashboardView
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(template_name='InvApp/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', include('django.contrib.auth.urls')),  
    path('register/', include('inventory_sys.urls')),  
    path('', include('inventory_sys.urls')),  
    path('home/', HomeDashboardView.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)