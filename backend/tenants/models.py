"""
Tenants Models
==============

Multi-tenancy foundation for Breathe ESG.

Design Decisions:
- Multi-tenancy is implemented via a Tenant foreign key on every model that holds
  tenant-specific data. This is simpler than schema-based multi-tenancy and works
  well with SQLite for development.
- The custom User model extends AbstractUser with:
  - UUID primary key (consistent with all other models)
  - tenant FK (every user belongs to exactly one tenant)
  - role field (analyst vs admin) for permission gating
  - email as the login credential instead of username
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class Tenant(models.Model):
    """
    Represents an organization/company using the platform.

    All data in the system is scoped to a tenant. This ensures complete data
    isolation between organizations sharing the same database.

    Fields:
        name: Human-readable organization name (e.g., "Acme Corp")
        domain: Unique identifier/subdomain for the tenant (e.g., "acme")
        is_active: Soft-disable flag - inactive tenants can't log in or access data
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this tenant"
    )
    name = models.CharField(
        max_length=255,
        help_text="Organization display name"
    )
    domain = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique domain/slug for tenant identification"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive tenants are locked out of the platform"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Custom user model for Breathe ESG platform.

    Extends Django's AbstractUser to add:
    - UUID primary key (standard across all models)
    - Tenant relationship (every user belongs to one org)
    - Role-based access (analyst can view/edit, admin can approve/lock)
    - Email-based login (username field is set to 'email')

    Role Permissions:
    - analyst: Upload data, view records, edit records, flag issues
    - admin: All analyst permissions + approve/reject/lock records, manage data sources
    """
    ROLE_CHOICES = [
        ('analyst', 'Analyst'),
        ('admin', 'Admin'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,  # Null allowed for superusers who aren't tied to a tenant
        blank=True,
        help_text="The organization this user belongs to"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='analyst',
        help_text="Determines the user's permission level within the platform"
    )

    # Use email as the primary login credential instead of username
    # USERNAME_FIELD tells Django auth to authenticate via email
    USERNAME_FIELD = 'email'
    # username is still required by AbstractUser, but email is used for login
    REQUIRED_FIELDS = ['username']

    # Ensure email is unique across the entire platform
    email = models.EmailField(unique=True)

    class Meta:
        ordering = ['email']

    def __str__(self):
        return f"{self.email} ({self.tenant.name if self.tenant else 'No Tenant'})"

    @property
    def is_admin(self):
        """Convenience property to check if user has admin role."""
        return self.role == 'admin'

    @property
    def is_analyst(self):
        """Convenience property to check if user has analyst or admin role."""
        return self.role in ('analyst', 'admin')
