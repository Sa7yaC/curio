from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Tenant, User, Product, Order, OrderItem

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'subdomain', 'contact_email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields =['store_name', 'subdomain', 'contact_email']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display =['username','email','tenant','role','is_active']
    list_filter=['role','is_active', 'tenant']
    search_fields= ['username','email','first_name', 'last_name']
    
    fieldsets=BaseUserAdmin.fieldsets +(
        ('Tenant Info', {'fields':('tenant', 'role', 'phone','address')}),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display=['name', 'tenant', 'category', 'price', 'stock', 'is_active','created_at']
    list_filter=['tenant','category','is_active', 'created_at']
    search_fields=['name', 'description','category']


class OrderItemInline(admin.TabularInline):
    model =OrderItem
    extra=0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'tenant', 'customer', 'status', 'total_amount', 'created_at']
    list_filter = ['tenant', 'status', 'created_at']
    search_fields = ['order_number', 'customer__username']
    inlines = [OrderItemInline]