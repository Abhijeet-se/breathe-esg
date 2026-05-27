"""
Tenant Admin Configuration
===========================

Register Tenant and User models with Django admin for direct database management.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin configuration for Tenant model."""
    list_display = ['name', 'domain', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'domain']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for custom User model.
    Extends Django's built-in UserAdmin to include tenant and role fields.
    """
    list_display = ['email', 'username', 'tenant', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'tenant']
    search_fields = ['email', 'username', 'first_name', 'last_name']

    # Add tenant and role to the fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Breathe ESG', {
            'fields': ('tenant', 'role'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Breathe ESG', {
            'fields': ('email', 'tenant', 'role'),
        }),
    )
