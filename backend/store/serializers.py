from rest_framework import serializers
from .models import Tenant, User, Product, ProductSize, Order, OrderItem
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
import uuid

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'store_name', 'contact_email', 'contact_phone', 
                  'domain', 'subdomain', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


from django.utils.text import slugify

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    tenant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    store_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 
                  'last_name', 'phone', 'address', 'role', 'tenant_id', 'store_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Sanitize text fields
        for field in ['username', 'first_name', 'last_name', 'phone', 'address', 'store_name']:
            if field in attrs and isinstance(attrs[field], str):
                attrs[field] = attrs[field].strip()

        # Validate role
        role = attrs.get('role', 'customer')
        valid_roles = [c[0] for c in User.ROLE_CHOICES]
        if role not in valid_roles:
            role = 'customer'

        tenant = None

        if role == 'store_owner':
            # Store owners create a brand new store
            raw_store_name = attrs.get('store_name') or attrs.get('username')
            if not raw_store_name:
                raise serializers.ValidationError({"store_name": "Store name is required when registering as a store owner."})
            
            store_title = raw_store_name.strip()
            base_slug = slugify(store_title) or "store"
            subdomain = base_slug
            counter = 1
            while Tenant.objects.filter(subdomain=subdomain).exists():
                subdomain = f"{base_slug}-{counter}"
                counter += 1

            tenant_name = store_title
            counter = 1
            while Tenant.objects.filter(name=tenant_name).exists():
                tenant_name = f"{store_title} ({counter})"
                counter += 1

            tenant = Tenant.objects.create(
                name=tenant_name,
                store_name=store_title,
                contact_email=attrs.get('email', ''),
                contact_phone=attrs.get('phone', ''),
                subdomain=subdomain,
                is_active=True
            )

        elif role == 'staff':
            # Staff must belong to an existing store
            tenant_id = attrs.get('tenant_id')
            if not tenant_id:
                raise serializers.ValidationError({"tenant_id": "Store Tenant ID is required when registering as staff."})
            try:
                tenant = Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                raise serializers.ValidationError({"tenant_id": "Invalid or inactive Store Tenant ID."})

        else:
            # Customer: Customers can shop in any store!
            # Never require the customer to enter a tenant ID.
            tenant_id = attrs.get('tenant_id')
            if tenant_id:
                tenant = Tenant.objects.filter(id=tenant_id, is_active=True).first()
            if not tenant:
                tenant = Tenant.objects.filter(is_active=True).first()
            if not tenant:
                tenant = Tenant.objects.create(
                    name="Curio",
                    store_name="Curio",
                    subdomain="curio",
                    is_active=True
                )

        attrs['role'] = role
        attrs['tenant'] = tenant
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        validated_data.pop('store_name', None)
        validated_data.pop('tenant_id', None)
        tenant = validated_data.pop('tenant')
        
        user = User.objects.create_user(tenant=tenant, **validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.store_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'phone', 'address', 'role', 'tenant', 'tenant_name']
        read_only_fields = ['id', 'tenant']


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ['id', 'size', 'stock']


class ProductSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    tenant_store_name = serializers.CharField(source='tenant.store_name', read_only=True)
    sizes = ProductSizeSerializer(many=True, required=False)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category', 
                  'image_url', 'is_active', 'sizes', 'created_by', 'created_by_username', 
                  'tenant', 'tenant_store_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'tenant', 'created_at', 'updated_at']

    def validate_category(self, value):
        if not value:
            return value
        cleaned = value.strip()
        request = self.context.get('request')
        tenant = getattr(getattr(request, 'user', None), 'tenant', None)
        if tenant:
            existing = Product.objects.filter(
                tenant=tenant,
                category__iexact=cleaned
            ).values_list('category', flat=True).first()
            if existing:
                return existing
        return cleaned.title() if cleaned.islower() else cleaned

    def create(self, validated_data):
        sizes_data = validated_data.pop('sizes', None)
        request = self.context.get('request')
        validated_data['tenant'] = request.user.tenant
        validated_data['created_by'] = request.user
        
        if sizes_data is not None and len(sizes_data) > 0:
            validated_data['stock'] = sum(s.get('stock', 0) for s in sizes_data)
        
        product = super().create(validated_data)
        
        if sizes_data is not None:
            for size_item in sizes_data:
                ProductSize.objects.create(product=product, **size_item)
                
        return product

    def update(self, instance, validated_data):
        sizes_data = validated_data.pop('sizes', None)
        
        if sizes_data is not None:
            validated_data['stock'] = sum(s.get('stock', 0) for s in sizes_data)
            instance.sizes.all().delete()
            for size_item in sizes_data:
                ProductSize.objects.create(product=instance, **size_item)
                
        return super().update(instance, validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'size', 'quantity', 'price', 'subtotal']
        read_only_fields = ['id', 'price', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    assigned_staff_name = serializers.CharField(source='assigned_staff.get_full_name', read_only=True)
    
    store_name = serializers.CharField(source='tenant.store_name', read_only=True)
    tenant_id = serializers.IntegerField(source='tenant.id', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'customer', 'customer_name', 'status', 
                  'total_amount', 'shipping_address', 'notes', 'assigned_staff', 
                  'assigned_staff_name', 'store_name', 'tenant_id', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'order_number', 'customer', 'total_amount', 'store_name', 'tenant_id', 'created_at', 'updated_at']

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        request = self.context.get('request')
        
        # Validating stock, active status, and computing subtotals
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            size = item_data.get('size')
            
            # Check if product is active
            if not product.is_active:
                raise serializers.ValidationError(
                    f"Product '{product.name}' is currently inactive and cannot be ordered."
                )
            
            # Size-specific stock check
            if size:
                product_size = ProductSize.objects.filter(product=product, size=size).first()
                if not product_size:
                    raise serializers.ValidationError(
                        f"Size '{size}' is not available for {product.name}."
                    )
                if product_size.stock < quantity:
                    raise serializers.ValidationError(
                        f"Insufficient stock for {product.name} (Size {size}). Available: {product_size.stock}"
                    )
            else:
                # Regular product stock check
                if product.stock < quantity:
                    raise serializers.ValidationError(
                        f"Insufficient stock for {product.name}. Available: {product.stock}"
                    )
            
            item_data['price'] = product.price
            item_data['subtotal'] = product.price * quantity
        
        # Group items by tenant so cross-store orders are recorded per store
        tenant_groups = {}
        for item_data in items_data:
            product = item_data['product']
            item_tenant = product.tenant or getattr(request, 'tenant', None) or request.user.tenant
            if item_tenant not in tenant_groups:
                tenant_groups[item_tenant] = []
            tenant_groups[item_tenant].append(item_data)

        created_orders = []
        for item_tenant, t_items in tenant_groups.items():
            order_total = sum(i['subtotal'] for i in t_items)
            order = Order.objects.create(
                tenant=item_tenant,
                customer=request.user,
                order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                total_amount=order_total,
                shipping_address=validated_data.get('shipping_address', ''),
                notes=validated_data.get('notes', ''),
            )
            for item_data in t_items:
                product = item_data['product']
                quantity = item_data['quantity']
                size = item_data.get('size')
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    size=size,
                    quantity=quantity,
                    price=item_data['price'],
                    subtotal=item_data['subtotal']
                )
                if size:
                    product_size = ProductSize.objects.filter(product=product, size=size).first()
                    if product_size:
                        product_size.stock = max(0, product_size.stock - quantity)
                        product_size.save()
                
                product.stock = max(0, product.stock - quantity)
                product.save()

            created_orders.append(order)

        return created_orders[0]

    def update(self, instance, validated_data):
        validated_data.pop('items', None)
        validated_data.pop('customer', None)
        
        return super().update(instance, validated_data)

class OrderListSerializer(serializers.ModelSerializer):
    """Simplified serializer for order listing"""
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    items_count = serializers.IntegerField(source='items.count', read_only=True)
    store_name = serializers.CharField(source='tenant.store_name', read_only=True)
    tenant_id = serializers.IntegerField(source='tenant.id', read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'customer_name', 'status', 'total_amount', 
                  'items_count', 'store_name', 'tenant_id', 'created_at']
