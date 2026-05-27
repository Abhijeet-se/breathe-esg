"""
Tenant Serializers
==================

Serializers for Tenant and User models, used by the API layer.
"""

from rest_framework import serializers
from .models import Tenant, User


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant model - used in admin/management endpoints."""

    class Meta:
        model = Tenant
        fields = ['id', 'name', 'domain', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.

    Used for the /api/auth/me/ endpoint and user management.
    Includes tenant info as a nested object for convenience.
    Password is write-only to prevent leaking hashes.
    """
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'tenant', 'tenant_name', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant_name']
        extra_kwargs = {
            'tenant': {'required': False},  # Set automatically for non-superusers
        }

    # Map created_at/updated_at to Django's built-in fields
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)
    updated_at = serializers.DateTimeField(source='last_login', read_only=True)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Handles password hashing and tenant assignment.
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password', 'first_name', 'last_name', 'role', 'tenant']
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create user with properly hashed password."""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
