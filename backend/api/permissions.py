"""
Custom DRF Permissions
=======================

Permission classes for the Breathe ESG API.

Design Decisions:
- Permissions are layered: base auth -> tenant membership -> role -> record state
- IsTenantMember ensures users can only access their own tenant's data
- IsAdmin gates approval/lock actions (sensitive operations)
- IsNotLocked prevents editing records that have been finalized

These permissions are combined in views using permission_classes lists.
DRF requires ALL permissions in the list to pass (AND logic).
"""

from rest_framework.permissions import BasePermission


class IsTenantMember(BasePermission):
    """
    Ensures the authenticated user belongs to the same tenant as the
    resource being accessed.

    This is the primary multi-tenancy enforcement permission. It checks
    that request.tenant is set (by TenantMiddleware) and that the user
    has an associated tenant.

    For object-level checks, it verifies the object's tenant matches
    the request tenant.
    """
    message = "You do not have access to this tenant's resources."

    def has_permission(self, request, view):
        """Check that the user has a tenant assigned."""
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request, 'tenant') and
            request.tenant is not None
        )

    def has_object_permission(self, request, view, obj):
        """Check that the object belongs to the user's tenant."""
        # The object must have a 'tenant' or 'tenant_id' attribute
        if hasattr(obj, 'tenant_id'):
            return str(obj.tenant_id) == str(request.tenant.id)
        if hasattr(obj, 'tenant'):
            return str(obj.tenant.id) == str(request.tenant.id)
        # For objects without direct tenant (e.g., RawRecord via batch)
        if hasattr(obj, 'batch') and hasattr(obj.batch, 'tenant_id'):
            return str(obj.batch.tenant_id) == str(request.tenant.id)
        return True


class IsAnalyst(BasePermission):
    """
    Allows access to users with 'analyst' or 'admin' role.

    Analysts can: upload data, view records, edit records, flag issues.
    Since admins have all analyst permissions, this also allows admins.
    """
    message = "You need at least Analyst role to perform this action."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role in ('analyst', 'admin')
        )


class IsAdmin(BasePermission):
    """
    Restricts access to users with 'admin' role only.

    Admins can: approve/reject records, lock records, manage data sources,
    view global audit logs.
    """
    message = "This action requires Admin role."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role == 'admin'
        )


class IsNotLocked(BasePermission):
    """
    Prevents modifications to records that have been locked.

    Locked records are finalized and cannot be edited, approved, or rejected.
    Only applies to unsafe methods (PATCH, PUT, DELETE).
    GET requests are always allowed.
    """
    message = "This record has been locked and cannot be modified."

    def has_object_permission(self, request, view, obj):
        # Allow read-only access to locked records
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Check if the object (NormalizedRecord) is locked
        if hasattr(obj, 'status'):
            return obj.status != 'locked'

        return True
