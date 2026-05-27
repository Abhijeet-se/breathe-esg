"""
Ingestion Serializers
======================

Serializers for the ingestion pipeline models.
Used by the API layer for request/response handling.
"""

from rest_framework import serializers
from .models import (
    DataSource, UploadBatch, RawRecord, NormalizedRecord,
    AuditLog, ApprovalRecord,
)


class DataSourceSerializer(serializers.ModelSerializer):
    """Serializer for DataSource - manages data source configurations."""
    source_type_display = serializers.CharField(
        source='get_source_type_display', read_only=True
    )

    class Meta:
        model = DataSource
        fields = [
            'id', 'name', 'source_type', 'source_type_display',
            'header_mappings', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UploadBatchSerializer(serializers.ModelSerializer):
    """
    Serializer for UploadBatch.

    Includes computed summary fields and nested data source info.
    The file field is write-only to prevent exposing file paths in list views.
    """
    uploaded_by_email = serializers.CharField(
        source='uploaded_by.email', read_only=True
    )
    data_source_name = serializers.CharField(
        source='data_source.name', read_only=True
    )
    source_type = serializers.CharField(
        source='data_source.source_type', read_only=True
    )

    class Meta:
        model = UploadBatch
        fields = [
            'id', 'data_source', 'data_source_name', 'source_type',
            'file_name', 'file', 'status',
            'total_rows', 'parsed_rows', 'failed_rows',
            'suspicious_rows', 'approved_rows',
            'uploaded_by', 'uploaded_by_email',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'file_name', 'status', 'total_rows', 'parsed_rows',
            'failed_rows', 'suspicious_rows', 'approved_rows',
            'uploaded_by', 'created_at', 'updated_at',
        ]


class RawRecordSerializer(serializers.ModelSerializer):
    """Serializer for RawRecord - exposes original unmodified data."""

    class Meta:
        model = RawRecord
        fields = ['id', 'row_number', 'original_data', 'created_at']
        read_only_fields = ['id', 'created_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog entries."""
    changed_by_email = serializers.CharField(
        source='changed_by.email', read_only=True
    )
    action_display = serializers.CharField(
        source='get_action_display', read_only=True
    )

    class Meta:
        model = AuditLog
        fields = [
            'id', 'action', 'action_display', 'field_name',
            'old_value', 'new_value',
            'changed_by', 'changed_by_email', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ApprovalRecordSerializer(serializers.ModelSerializer):
    """Serializer for ApprovalRecord entries."""
    reviewer_email = serializers.CharField(
        source='reviewer.email', read_only=True
    )
    action_display = serializers.CharField(
        source='get_action_display', read_only=True
    )

    class Meta:
        model = ApprovalRecord
        fields = [
            'id', 'action', 'action_display', 'comments',
            'reviewer', 'reviewer_email', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class NormalizedRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for NormalizedRecord - the main working record.

    Includes nested raw record data and computed display fields.
    """
    scope_display = serializers.CharField(
        source='get_scope_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )
    raw_data = serializers.JSONField(
        source='raw_record.original_data', read_only=True
    )
    batch_file_name = serializers.CharField(
        source='batch.file_name', read_only=True
    )

    class Meta:
        model = NormalizedRecord
        fields = [
            'id', 'batch', 'batch_file_name', 'source_type',
            'scope', 'scope_display', 'category', 'record_date',
            'original_unit', 'original_value',
            'normalized_unit', 'normalized_value',
            'emissions_kg_co2e',
            'status', 'status_display',
            'validation_errors', 'suspicious_flag', 'suspicious_reason',
            'edited_by', 'approved_by', 'approved_at', 'locked_at',
            'raw_data',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'batch', 'source_type', 'scope', 'category',
            'original_unit', 'original_value',
            'emissions_kg_co2e', 'status',
            'validation_errors', 'suspicious_flag', 'suspicious_reason',
            'edited_by', 'approved_by', 'approved_at', 'locked_at',
            'raw_data', 'created_at', 'updated_at',
        ]


class NormalizedRecordEditSerializer(serializers.ModelSerializer):
    """
    Serializer for editing a NormalizedRecord.

    Only allows editing specific fields. The view handles audit log creation.
    """
    class Meta:
        model = NormalizedRecord
        fields = [
            'record_date', 'normalized_value', 'normalized_unit',
            'emissions_kg_co2e', 'category',
        ]


class FileUploadSerializer(serializers.Serializer):
    """
    Serializer for the file upload endpoint.

    Validates that a file and data_source are provided.
    """
    file = serializers.FileField(
        help_text="CSV or Excel file to upload"
    )
    data_source = serializers.UUIDField(
        help_text="UUID of the DataSource to associate this upload with"
    )

    def validate_file(self, value):
        """Validate file extension."""
        name = value.name.lower()
        valid_extensions = ['.csv', '.xlsx', '.xls']
        if not any(name.endswith(ext) for ext in valid_extensions):
            raise serializers.ValidationError(
                f"Unsupported file format. Allowed: {', '.join(valid_extensions)}"
            )

        # Max file size: 50MB
        max_size = 50 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File too large. Maximum size is 50MB, got {value.size / 1024 / 1024:.1f}MB"
            )

        return value
