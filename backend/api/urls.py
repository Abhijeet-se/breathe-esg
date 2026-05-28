"""
API URL Configuration
======================

Maps URL patterns to API views.

All endpoints are prefixed with /api/ (configured in breathe_esg/urls.py).

URL Structure:
    /api/auth/login/           POST   JWT login
    /api/auth/refresh/         POST   JWT refresh
    /api/auth/me/              GET    Current user

    /api/dashboard/stats/      GET    Dashboard statistics

    /api/upload/               POST   File upload
    /api/batches/              GET    List batches
    /api/batches/{id}/         GET    Batch detail

    /api/records/              GET    List records
    /api/records/{id}/         GET    Record detail
    /api/records/{id}/         PATCH  Edit record
    /api/records/{id}/approve/ POST   Approve record
    /api/records/{id}/reject/  POST   Reject record
    /api/records/{id}/lock/    POST   Lock record
    /api/records/{id}/audit-trail/ GET Audit trail

    /api/audit-logs/           GET    Global audit log

    /api/data-sources/         GET/POST   Data sources
    /api/data-sources/{id}/    GET/PATCH  Data source detail
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    CurrentUserView,
    DashboardStatsView,
    DataSourceViewSet,
    UploadBatchViewSet,
    FileUploadView,
    NormalizedRecordViewSet,
    AuditLogViewSet,
    HealthCheckView,
    SeedDataView,
)

# DRF Router for viewsets - automatically generates URL patterns
# for list, create, retrieve, update, partial_update, destroy
router = DefaultRouter()
router.register(r'data-sources', DataSourceViewSet, basename='datasource')
router.register(r'batches', UploadBatchViewSet, basename='batch')
router.register(r'records', NormalizedRecordViewSet, basename='record')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    # --- Authentication ---
    # JWT token endpoints from simplejwt
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Custom endpoint to get current user info
    path('auth/me/', CurrentUserView.as_view(), name='current_user'),

    # --- Dashboard ---
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),

    # --- File Upload ---
    # Separate from batches because it has custom parsing logic
    path('upload/', FileUploadView.as_view(), name='file_upload'),

    # --- Router-generated URLs ---
    # Includes: data-sources/, batches/, records/, audit-logs/
    # Plus custom actions: records/{id}/approve/, reject/, lock/, audit-trail/
    path('', include(router.urls)),

    # --- Health Check ---
    path('health/', HealthCheckView.as_view(), name='health_check'),

    # --- One-time seed endpoint ---
    path('seed/', SeedDataView.as_view(), name='seed_data'),
]
