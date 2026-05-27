"""
Ingestion Admin Configuration
==============================

Register ingestion models with Django admin for debugging and data inspection.
"""

from django.contrib import admin
from .models import (
    DataSource, UploadBatch, RawRecord, NormalizedRecord,
    AuditLog, ApprovalRecord,
)


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_type', 'tenant', 'created_at']
    list_filter = ['source_type', 'tenant']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(UploadBatch)
class UploadBatchAdmin(admin.ModelAdmin):
    list_display = [
        'file_name', 'data_source', 'status', 'total_rows',
        'parsed_rows', 'failed_rows', 'suspicious_rows', 'approved_rows',
        'uploaded_by', 'created_at',
    ]
    list_filter = ['status', 'tenant', 'data_source']
    search_fields = ['file_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ['row_number', 'batch', 'created_at']
    list_filter = ['batch']
    readonly_fields = ['id', 'created_at']


@admin.register(NormalizedRecord)
class NormalizedRecordAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'scope', 'category', 'record_date', 'original_value',
        'original_unit', 'emissions_kg_co2e', 'status', 'suspicious_flag',
    ]
    list_filter = ['status', 'scope', 'source_type', 'suspicious_flag', 'tenant']
    search_fields = ['category']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'normalized_record', 'field_name', 'changed_by', 'created_at']
    list_filter = ['action']
    readonly_fields = ['id', 'created_at']


@admin.register(ApprovalRecord)
class ApprovalRecordAdmin(admin.ModelAdmin):
    list_display = ['action', 'normalized_record', 'reviewer', 'created_at']
    list_filter = ['action']
    readonly_fields = ['id', 'created_at']
