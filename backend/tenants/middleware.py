"""
Tenant Middleware
=================

Attaches the current user's tenant to the request object so that all downstream
views and querysets can enforce tenant-scoped data access.

Design Decision:
- We extract tenant from the authenticated user rather than from request headers
  or URL parameters. This prevents tenant spoofing - a user can only ever access
  data belonging to their own tenant.
- Auth endpoints (/api/auth/) are excluded because the user isn't authenticated yet
  at those endpoints.
- We also check that the tenant is active, returning 403 if it's been disabled.
"""

from django.http import JsonResponse


class TenantMiddleware:
    """
    Middleware that attaches the authenticated user's tenant to request.tenant.

    After this middleware runs, views can access request.tenant to scope queries.
    Unauthenticated requests and auth endpoints get request.tenant = None.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Default: no tenant attached
        request.tenant = None

        # Skip tenant resolution for:
        # - Authentication endpoints (user not yet authenticated)
        # - Admin panel (has its own auth)
        # - Static/media files
        skip_paths = ['/api/auth/', '/admin/', '/static/', '/media/']
        if any(request.path.startswith(path) for path in skip_paths):
            return self.get_response(request)

        # If user is authenticated, extract their tenant
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user
            if hasattr(user, 'tenant') and user.tenant is not None:
                # Check if tenant is still active
                if not user.tenant.is_active:
                    return JsonResponse(
                        {'detail': 'Your organization account has been deactivated.'},
                        status=403
                    )
                request.tenant = user.tenant

        return self.get_response(request)
