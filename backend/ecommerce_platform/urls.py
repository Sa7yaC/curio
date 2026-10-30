import os
from django.contrib import admin
from django.urls import path, include

# Practice 5: Limit & Hide Admin Access
# Allows configuring an obscure admin path in production (e.g., 'management-portal-secure/')
admin_path = os.environ.get('DJANGO_ADMIN_URL', 'admin/').strip('/')
if admin_path:
    admin_path = f"{admin_path}/"

urlpatterns = [
    path(admin_path, admin.site.urls),
    path('api/', include('store.urls')),
]