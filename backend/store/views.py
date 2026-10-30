
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Q
from .models import Tenant, User, Product, Order
from .serializers import (
    TenantSerializer, UserRegistrationSerializer, UserSerializer,
    ProductSerializer, OrderSerializer, OrderListSerializer
)
from .permissions import (
    IsTenantUser, IsStoreOwner, IsStoreOwnerOrStaff, 
    IsStaffOrReadOnly, CanManageOrder
)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer to include tenant_id and role"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom claims
        data['tenant_id'] = self.user.tenant.id
        data['tenant_name'] = self.user.tenant.store_name
        data['role'] = self.user.role
        data['user_id'] = self.user.id
        data['username'] = self.user.username
        
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims to token
        token['tenant_id'] = user.tenant.id
        token['role'] = user.role
        token['username'] = user.username
        
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

#  user 
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

# tenant
class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_superuser:
            return Tenant.objects.filter(id=self.request.user.tenant.id)
        return Tenant.objects.all()

# product
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsTenantUser, IsStaffOrReadOnly]

    # different query or filters
    def get_queryset(self):
        user = self.request.user
        tenant = None

        # For store managers / staff, strictly scope to their assigned store
        if user.is_authenticated and user.role in ['store_owner', 'staff']:
            tenant = user.tenant
        else:
            # Customers and shoppers can browse all stores or filter by tenant_id:
            qp = getattr(self.request, 'query_params', self.request.GET)
            tenant_id = qp.get('tenant_id')
            if tenant_id:
                try:
                    tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                except (Tenant.DoesNotExist, ValueError):
                    pass
            elif hasattr(self.request, 'tenant') and self.request.tenant:
                tenant = self.request.tenant

        queryset = Product.objects.all()
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        queryset = queryset.prefetch_related('sizes', 'tenant')
        
        qp = getattr(self.request, 'query_params', self.request.GET)
        category = qp.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        is_active = qp.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        search = qp.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all product categories"""
        user = request.user
        tenant = None

        if user.is_authenticated and user.role in ['store_owner', 'staff']:
            tenant = user.tenant
        else:
            qp = getattr(request, 'query_params', request.GET)
            tenant_id = qp.get('tenant_id')
            if tenant_id:
                try:
                    tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                except (Tenant.DoesNotExist, ValueError):
                    pass
            elif hasattr(request, 'tenant') and request.tenant:
                tenant = request.tenant

        qs = Product.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)

        categories = (
            qs.order_by('category')
            .values_list('category', flat=True)
            .distinct()
        )
        seen = set()
        unique_categories = []
        for cat in categories:
            if cat:
                clean = cat.strip()
                if clean and clean.lower() not in seen:
                    seen.add(clean.lower())
                    unique_categories.append(clean)
        return Response({'categories': unique_categories})

# orders
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsTenantUser, CanManageOrder]

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        return OrderSerializer

    # query and filters
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'customer':
            # Customers can see all orders they placed across any store
            queryset = Order.objects.filter(customer=user).select_related(
                'customer', 'assigned_staff', 'tenant'
            ).prefetch_related('items__product')
        else:
            # Store managers & staff view orders within their store
            tenant = user.tenant
            queryset = Order.objects.filter(tenant=tenant).select_related(
                'customer', 'assigned_staff', 'tenant'
            ).prefetch_related('items__product')
            
            if user.role == 'staff':
                queryset = queryset.filter(
                    Q(assigned_staff=user) | Q(status='pending')
                )

        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['get'])
    def staff_members(self, request):
        """Get all staff members belonging to the current user's tenant"""
        if request.user.role not in ['store_owner', 'staff']:
            return Response(
                {'error': 'Only store managers and staff can view team members.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        staff_qs = User.objects.filter(tenant=request.user.tenant, role='staff').order_by('username')
        staff_list = [
            {
                'id': u.id,
                'username': u.username,
                'first_name': u.first_name,
                'last_name': u.last_name,
                'full_name': (u.get_full_name() or u.username).strip(),
                'email': u.email,
            }
            for u in staff_qs
        ]
        return Response(staff_list)

    @action(detail=True, methods=['post'])
    def assign_staff(self, request, pk=None):
        """Assign staff to an order by ID or username (store owner only)"""
        if request.user.role != 'store_owner':
            return Response(
                {'error': 'Only store owners can assign staff'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        order = self.get_object()
        staff_id = request.data.get('staff_id')
        staff_username = request.data.get('username') or request.data.get('staff_username')
        
        if not staff_id and not staff_username:
            return Response(
                {'error': 'Please select or provide a staff member ID or username.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if staff_id:
                staff = User.objects.get(
                    id=staff_id, 
                    tenant=request.user.tenant, 
                    role='staff'
                )
            else:
                staff = User.objects.get(
                    username__iexact=str(staff_username).strip(),
                    tenant=request.user.tenant,
                    role='staff'
                )
            order.assigned_staff = staff
            order.save()
            
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': f'Staff member "{staff_username or staff_id}" not found with role "Staff" in your store.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Get current user's orders across all tenants/stores"""
        queryset = Order.objects.filter(
            customer=request.user
        ).select_related('customer', 'tenant').prefetch_related('items__product').order_by('-created_at')
        
        serializer = OrderListSerializer(queryset, many=True)
        return Response(serializer.data)