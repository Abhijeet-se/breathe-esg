"""
API Filters
============

DRF filter backends for queryset filtering.

These filters integrate with django-filter to provide URL query parameter
filtering on API list endpoints. Each filter class defines which fields
can be filtered and how.
"""

import django_filters
from ingestion.models import NormalizedRecord, UploadBatch, AuditLog


class NormalizedRecordFilter(django_filters.FilterSet):
    """
    Filter for NormalizedRecord list endpoint.

    Supported query parameters:
    - status: exact match (e.g., ?status=approved)
    - scope: exact match (e.g., ?scope=scope_1)
    - source_type: exact match (e.g., ?source_type=sap_fuel)
    - batch: exact UUID match (e.g., ?batch=<uuid>)
    - suspicious_flag: boolean (e.g., ?suspicious_flag=true)
    - date_from/date_to: date range filter on record_date
    - category: case-insensitive contains (e.g., ?category=combustion)
    """
    date_from = django_filters.DateFilter(
        field_name='record_date', lookup_expr='gte',
        help_text="Filter records on or after this date (YYYY-MM-DD)"
    )
    date_to = django_filters.DateFilter(
        field_name='record_date', lookup_expr='lte',
        help_text="Filter records on or before this date (YYYY-MM-DD)"
    )
    category = django_filters.CharFilter(
        field_name='category', lookup_expr='icontains',
        help_text="Filter by category (case-insensitive partial match)"
    )

    class Meta:
        model = NormalizedRecord
        fields = [
            'status', 'scope', 'source_type', 'batch',
            'suspicious_flag',
        ]


class UploadBatchFilter(django_filters.FilterSet):
    """
    Filter for UploadBatch list endpoint.

    Supported query parameters:
    - status: exact match
    - data_source: exact UUID match
    """
    class Meta:
        model = UploadBatch
        fields = ['status', 'data_source']


class AuditLogFilter(django_filters.FilterSet):
    """
    Filter for AuditLog list endpoint.

    Supported query parameters:
    - action: exact match
    - normalized_record: exact UUID match
    """
    class Meta:
        model = AuditLog
        fields = ['action', 'normalized_record']
