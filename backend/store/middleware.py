from django.utils.deprecation import MiddlewareMixin
from .models import Tenant

class TenantMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        # fetching tenant from header or subdomain
        host = request.get_host().split(':')[0]
        subdomain = host.split('.')[0] if '.' in host else None
        
        # fetching tenant from the headers
        tenant_id = request.META.get('HTTP_X_TENANT_ID')
        
        if tenant_id:
            try:
                request.tenant = Tenant.objects.get(id=tenant_id, is_active=True)
            except Tenant.DoesNotExist:
                request.tenant = None
        elif subdomain:
            try:
                request.tenant = Tenant.objects.get(subdomain=subdomain, is_active=True)
            except Tenant.DoesNotExist:
                request.tenant = None
        else:
            request.tenant = None
        
        return None
