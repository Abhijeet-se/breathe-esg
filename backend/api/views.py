"""
API Views
=========

All API endpoints for the Breathe ESG Data Ingestion Platform.

Endpoint Summary:
-----------------
Authentication:
    POST   /api/auth/login/          JWT token pair
    POST   /api/auth/refresh/        Refresh access token
    GET    /api/auth/me/             Current user info

Dashboard:
    GET    /api/dashboard/stats/     Aggregate statistics

Upload & Batches:
    GET    /api/batches/             List upload batches
    POST   /api/batches/             Create new batch (unused - use /api/upload/)
    GET    /api/batches/{id}/        Batch detail with summary
    POST   /api/upload/              File upload + parsing

Records:
    GET    /api/records/             List normalized records (filterable)
    GET    /api/records/{id}/        Record detail with raw data + audit trail
    PATCH  /api/records/{id}/        Edit record fields
    POST   /api/records/{id}/approve/    Approve record
    POST   /api/records/{id}/reject/     Reject record
    POST   /api/records/{id}/lock/       Lock record (admin only)

Audit:
    GET    /api/records/{id}/audit-trail/   Audit log for a record
    GET    /api/audit-logs/                 Global audit log (admin only)

Data Sources:
    GET/POST    /api/data-sources/       List/create data sources
    GET/PATCH   /api/data-sources/{id}/  Detail/update data source

Design Decisions:
- All list endpoints filter by request.tenant (multi-tenancy)
- Upload endpoint triggers synchronous parsing (no Celery for prototype)
- Record edits create audit log entries automatically
- Approval/rejection actions use custom @action decorators
"""

import logging
from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from tenants.models import User
from tenants.serializers import UserSerializer
from ingestion.models import (
    DataSource, UploadBatch, RawRecord, NormalizedRecord,
    AuditLog, ApprovalRecord,
)
from ingestion.serializers import (
    DataSourceSerializer, UploadBatchSerializer, RawRecordSerializer,
    NormalizedRecordSerializer, NormalizedRecordEditSerializer,
    AuditLogSerializer, ApprovalRecordSerializer, FileUploadSerializer,
)
from ingestion.parsers.sap_parser import SAPParser
from ingestion.parsers.electricity_parser import ElectricityParser
from ingestion.parsers.travel_parser import TravelParser
from ingestion.validators import ValidationEngine
from ingestion.normalizer import NormalizationEngine

from .permissions import IsTenantMember, IsAnalyst, IsAdmin, IsNotLocked
from .filters import NormalizedRecordFilter, UploadBatchFilter, AuditLogFilter

logger = logging.getLogger(__name__)


# =============================================================================
# PARSER REGISTRY
# =============================================================================
# Maps source_type strings to parser class instances
PARSER_REGISTRY = {
    'sap_fuel': SAPParser,
    'electricity': ElectricityParser,
    'travel': TravelParser,
}


# =============================================================================
# AUTHENTICATION VIEWS
# =============================================================================
class CurrentUserView(APIView):
    """
    GET /api/auth/me/ - Returns the currently authenticated user's info.

    This is used by the frontend to determine the user's role and tenant
    after login. The JWT token is decoded by DRF middleware before this
    view is called.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


# =============================================================================
# DASHBOARD VIEWS
# =============================================================================
class DashboardStatsView(APIView):
    """
    GET /api/dashboard/stats/ - Aggregated statistics for the dashboard.

    Returns record counts by status, recent batch uploads, and emissions
    summaries. All data is scoped to the user's tenant.
    """
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get(self, request):
        tenant = request.tenant

        # Count records by status
        status_counts = (
            NormalizedRecord.objects
            .filter(tenant=tenant)
            .values('status')
            .annotate(count=Count('id'))
        )
        status_map = {item['status']: item['count'] for item in status_counts}

        total_records = sum(status_map.values())

        # Count records by scope
        scope_counts = (
            NormalizedRecord.objects
            .filter(tenant=tenant)
            .values('scope')
            .annotate(
                count=Count('id'),
                total_emissions=Sum('emissions_kg_co2e'),
            )
        )

        # Recent batches (last 10)
        recent_batches = (
            UploadBatch.objects
            .filter(tenant=tenant)
            .order_by('-created_at')[:10]
        )
        recent_batches_data = UploadBatchSerializer(recent_batches, many=True).data

        # Total emissions
        total_emissions = (
            NormalizedRecord.objects
            .filter(tenant=tenant, status__in=['parsed', 'approved', 'locked'])
            .aggregate(total=Sum('emissions_kg_co2e'))
        )

        return Response({
            'total_records': total_records,
            'approved': status_map.get('approved', 0),
            'failed': status_map.get('failed', 0),
            'suspicious': status_map.get('suspicious', 0),
            'pending': status_map.get('parsed', 0) + status_map.get('uploaded', 0),
            'locked': status_map.get('locked', 0),
            'total_emissions_kg_co2e': str(total_emissions['total'] or 0),
            'by_scope': list(scope_counts),
            'recent_batches': recent_batches_data,
        })


# =============================================================================
# DATA SOURCE VIEWS
# =============================================================================
class DataSourceViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for DataSource configurations.

    GET  /api/data-sources/          List all data sources for the tenant
    POST /api/data-sources/          Create a new data source
    GET  /api/data-sources/{id}/     Get data source detail
    PATCH /api/data-sources/{id}/    Update data source
    DELETE /api/data-sources/{id}/   Delete data source
    """
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        """Filter data sources to current tenant only."""
        if not self.request.tenant:
            return DataSource.objects.none()
        return DataSource.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        """Automatically set the tenant from the request."""
        serializer.save(tenant=self.request.tenant)


# =============================================================================
# UPLOAD BATCH VIEWS
# =============================================================================
class UploadBatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and detail views for upload batches.

    GET /api/batches/       List all batches for the tenant
    GET /api/batches/{id}/  Batch detail with row count summary
    """
    serializer_class = UploadBatchSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filterset_class = UploadBatchFilter

    def get_queryset(self):
        """Filter batches to current tenant."""
        if not self.request.tenant:
            return UploadBatch.objects.none()
        return (
            UploadBatch.objects
            .filter(tenant=self.request.tenant)
            .select_related('data_source', 'uploaded_by')
        )


# =============================================================================
# FILE UPLOAD VIEW
# =============================================================================
class FileUploadView(APIView):
    """
    POST /api/upload/ - Upload a file for ingestion.

    This is the main entry point for data ingestion. The view:
    1. Validates the uploaded file
    2. Creates an UploadBatch record
    3. Selects the appropriate parser based on data source type
    4. Parses the file, creating RawRecord + NormalizedRecord for each row
    5. Runs validation and anomaly detection on each record
    6. Updates batch counters
    7. Returns the batch summary

    Processing is synchronous (no Celery) to keep the prototype simple.
    For production, this would be moved to an async task queue.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated, IsTenantMember, IsAnalyst]

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_obj = serializer.validated_data['file']
        data_source_id = serializer.validated_data['data_source']

        # Verify data source belongs to tenant
        try:
            data_source = DataSource.objects.get(
                id=data_source_id,
                tenant=request.tenant,
            )
        except DataSource.DoesNotExist:
            return Response(
                {'detail': 'Data source not found or does not belong to your tenant.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Create the upload batch record
        batch = UploadBatch.objects.create(
            tenant=request.tenant,
            data_source=data_source,
            file_name=file_obj.name,
            file=file_obj,
            status='processing',
            uploaded_by=request.user,
        )

        try:
            # Select parser based on source type
            parser_class = PARSER_REGISTRY.get(data_source.source_type)
            if not parser_class:
                batch.status = 'failed'
                batch.save()
                return Response(
                    {'detail': f"No parser for source type '{data_source.source_type}'"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            parser = parser_class()
            validator = ValidationEngine()
            normalizer = NormalizationEngine()

            # Parse the file
            parsed_results, parse_errors = parser.parse_file(
                file_obj, file_obj.name
            )

            batch.total_rows = len(parsed_results) + len(parse_errors)

            # Process each parsed row
            parsed_count = 0
            failed_count = len(parse_errors)
            suspicious_count = 0

            with transaction.atomic():
                # Create RawRecords and NormalizedRecords for failed parses
                for error in parse_errors:
                    RawRecord.objects.create(
                        batch=batch,
                        row_number=error.row_number,
                        original_data=error.original_data,
                    )

                # Create records for successfully parsed rows
                for parsed in parsed_results:
                    row_number = parsed.pop('_row_number', 0)
                    original_data = parsed.pop('_original_data', {})

                    # Create immutable raw record
                    raw_record = RawRecord.objects.create(
                        batch=batch,
                        row_number=row_number,
                        original_data=original_data,
                    )

                    try:
                        # Normalize values and calculate emissions
                        normalized = normalizer.normalize(
                            parsed, data_source.source_type
                        )

                        # Run validation
                        validation_errors = validator.validate_record(
                            parsed, data_source.source_type
                        )
                        validation_error_dicts = [
                            e.to_dict() for e in validation_errors
                        ]

                        # Check for hard errors vs warnings
                        has_hard_errors = any(
                            e.severity == 'error' for e in validation_errors
                        )
                        has_warnings = any(
                            e.severity == 'warning' for e in validation_errors
                        )

                        # Determine record status
                        if has_hard_errors:
                            record_status = 'failed'
                            failed_count += 1
                        elif has_warnings:
                            record_status = 'suspicious'
                            suspicious_count += 1
                        else:
                            record_status = 'parsed'
                            parsed_count += 1

                        # Build suspicious reason from warnings
                        suspicious_reasons = [
                            e.message for e in validation_errors
                            if e.severity == 'warning'
                        ]

                        # Create the normalized record
                        record = NormalizedRecord.objects.create(
                            raw_record=raw_record,
                            tenant=request.tenant,
                            batch=batch,
                            source_type=data_source.source_type,
                            scope=normalized['scope'],
                            category=normalized['category'],
                            record_date=parsed.get('date', date.today()),
                            original_unit=normalized['original_unit'],
                            original_value=normalized['original_value'],
                            normalized_unit=normalized['normalized_unit'],
                            normalized_value=normalized['normalized_value'],
                            emissions_kg_co2e=normalized['emissions_kg_co2e'],
                            status=record_status,
                            validation_errors=validation_error_dicts,
                            suspicious_flag=has_warnings,
                            suspicious_reason=(
                                '; '.join(suspicious_reasons)
                                if suspicious_reasons else None
                            ),
                        )

                        # Create audit log entry
                        AuditLog.objects.create(
                            normalized_record=record,
                            action='create',
                            new_value=f"Parsed from row {row_number}",
                            changed_by=request.user,
                        )

                    except Exception as e:
                        # If normalization fails, create a failed record
                        logger.error(
                            f"Error normalizing row {row_number}: {e}",
                            exc_info=True,
                        )
                        failed_count += 1
                        # Create a minimal normalized record with failed status
                        NormalizedRecord.objects.create(
                            raw_record=raw_record,
                            tenant=request.tenant,
                            batch=batch,
                            source_type=data_source.source_type,
                            scope=parsed.get('scope', 'scope_1'),
                            category=parsed.get('category', 'Unknown'),
                            record_date=parsed.get('date', date.today()),
                            original_unit=parsed.get('unit', 'unknown'),
                            original_value=Decimal(
                                str(parsed.get('quantity', 0))
                            ),
                            normalized_unit='unknown',
                            normalized_value=Decimal('0'),
                            emissions_kg_co2e=Decimal('0'),
                            status='failed',
                            validation_errors=[{
                                'field': None,
                                'rule': 'normalization_error',
                                'message': str(e),
                                'severity': 'error',
                            }],
                        )

                # Update batch counters
                batch.parsed_rows = parsed_count
                batch.failed_rows = failed_count
                batch.suspicious_rows = suspicious_count
                batch.status = 'completed'
                batch.save()

        except Exception as e:
            logger.error(f"File processing failed: {e}", exc_info=True)
            batch.status = 'failed'
            batch.save()
            return Response(
                {'detail': f'File processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Return batch summary
        return Response(
            UploadBatchSerializer(batch).data,
            status=status.HTTP_201_CREATED,
        )


# =============================================================================
# NORMALIZED RECORD VIEWS
# =============================================================================
class NormalizedRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD + workflow actions for normalized records.

    GET    /api/records/              List records (with filters)
    GET    /api/records/{id}/         Record detail
    PATCH  /api/records/{id}/         Edit record
    POST   /api/records/{id}/approve/ Approve record
    POST   /api/records/{id}/reject/  Reject record
    POST   /api/records/{id}/lock/    Lock record (admin only)
    GET    /api/records/{id}/audit-trail/  Audit log for this record
    """
    permission_classes = [IsAuthenticated, IsTenantMember]
    filterset_class = NormalizedRecordFilter
    search_fields = ['category', 'source_type']
    ordering_fields = [
        'record_date', 'emissions_kg_co2e', 'status',
        'created_at', 'updated_at',
    ]

    def get_serializer_class(self):
        if self.action in ('partial_update', 'update'):
            return NormalizedRecordEditSerializer
        return NormalizedRecordSerializer

    def get_queryset(self):
        """Filter records to current tenant."""
        if not self.request.tenant:
            return NormalizedRecord.objects.none()
        return (
            NormalizedRecord.objects
            .filter(tenant=self.request.tenant)
            .select_related('raw_record', 'batch', 'edited_by', 'approved_by')
        )

    def perform_update(self, serializer):
        """
        Override update to create audit log entries for each changed field.

        Tracks what was changed, the old and new values, and who made the change.
        Also prevents editing locked records.
        """
        instance = serializer.instance

        if instance.status == 'locked':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Cannot edit a locked record.")

        # Capture old values before save
        old_values = {}
        for field_name in serializer.validated_data:
            old_values[field_name] = str(getattr(instance, field_name, ''))

        # Save the changes
        serializer.save(edited_by=self.request.user)

        # Create audit log entries for each changed field
        for field_name, old_value in old_values.items():
            new_value = str(getattr(instance, field_name, ''))
            if old_value != new_value:
                AuditLog.objects.create(
                    normalized_record=instance,
                    action='edit',
                    field_name=field_name,
                    old_value=old_value,
                    new_value=new_value,
                    changed_by=self.request.user,
                )

    # --- Custom Actions ---

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsTenantMember, IsAdmin])
    def approve(self, request, pk=None):
        """
        POST /api/records/{id}/approve/ - Approve a record.

        Only admins can approve. Creates both an ApprovalRecord and AuditLog entry.
        Updates the record status to 'approved'.
        """
        record = self.get_object()

        if record.status == 'locked':
            return Response(
                {'detail': 'Cannot approve a locked record.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if record.status == 'approved':
            return Response(
                {'detail': 'Record is already approved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update record
        old_status = record.status
        record.status = 'approved'
        record.approved_by = request.user
        record.approved_at = timezone.now()
        record.save()

        # Create approval record
        comments = request.data.get('comments', '')
        ApprovalRecord.objects.create(
            normalized_record=record,
            reviewer=request.user,
            action='approve',
            comments=comments,
        )

        # Create audit log
        AuditLog.objects.create(
            normalized_record=record,
            action='approve',
            field_name='status',
            old_value=old_status,
            new_value='approved',
            changed_by=request.user,
        )

        # Update batch counter
        batch = record.batch
        batch.approved_rows = (
            NormalizedRecord.objects
            .filter(batch=batch, status='approved')
            .count()
        )
        batch.save()

        return Response(
            NormalizedRecordSerializer(record).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsTenantMember, IsAdmin])
    def reject(self, request, pk=None):
        """
        POST /api/records/{id}/reject/ - Reject a record.

        Requires a comment explaining the reason for rejection.
        Sets status back to 'suspicious' so it can be re-reviewed.
        """
        record = self.get_object()

        if record.status == 'locked':
            return Response(
                {'detail': 'Cannot reject a locked record.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comments = request.data.get('comments', '')
        if not comments:
            return Response(
                {'detail': 'Comments are required when rejecting a record.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update record
        old_status = record.status
        record.status = 'suspicious'
        record.suspicious_flag = True
        record.suspicious_reason = f"Rejected: {comments}"
        record.approved_by = None
        record.approved_at = None
        record.save()

        # Create approval record
        ApprovalRecord.objects.create(
            normalized_record=record,
            reviewer=request.user,
            action='reject',
            comments=comments,
        )

        # Create audit log
        AuditLog.objects.create(
            normalized_record=record,
            action='reject',
            field_name='status',
            old_value=old_status,
            new_value='suspicious',
            changed_by=request.user,
        )

        return Response(
            NormalizedRecordSerializer(record).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsTenantMember, IsAdmin])
    def lock(self, request, pk=None):
        """
        POST /api/records/{id}/lock/ - Lock a record (admin only).

        Locking is a terminal action - locked records cannot be edited,
        approved, or rejected. This is used to finalize records for
        reporting periods.
        """
        record = self.get_object()

        if record.status != 'approved':
            return Response(
                {'detail': 'Only approved records can be locked.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = record.status
        record.status = 'locked'
        record.locked_at = timezone.now()
        record.save()

        # Create audit log
        AuditLog.objects.create(
            normalized_record=record,
            action='lock',
            field_name='status',
            old_value=old_status,
            new_value='locked',
            changed_by=request.user,
        )

        return Response(
            NormalizedRecordSerializer(record).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'], url_path='audit-trail')
    def audit_trail(self, request, pk=None):
        """
        GET /api/records/{id}/audit-trail/ - Get audit log for a record.

        Returns all audit log entries for the specified record,
        ordered by most recent first.
        """
        record = self.get_object()
        audit_logs = (
            AuditLog.objects
            .filter(normalized_record=record)
            .select_related('changed_by')
            .order_by('-created_at')
        )
        serializer = AuditLogSerializer(audit_logs, many=True)
        return Response(serializer.data)


# =============================================================================
# GLOBAL AUDIT LOG VIEW
# =============================================================================
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/audit-logs/ - Global audit log (admin only).

    Lists all audit log entries across all records for the tenant.
    Useful for compliance reporting and system monitoring.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, IsAdmin]
    filterset_class = AuditLogFilter

    def get_queryset(self):
        """Filter audit logs to current tenant's records."""
        if not self.request.tenant:
            return AuditLog.objects.none()
        return (
            AuditLog.objects
            .filter(normalized_record__tenant=self.request.tenant)
            .select_related('changed_by', 'normalized_record')
            .order_by('-created_at')
        )


# =============================================================================
# HEALTH CHECK VIEW
# =============================================================================
class HealthCheckView(APIView):
    """
    GET /api/health/ - Simple health check for deployment monitoring.

    Returns 200 OK if the server is running. No authentication required.
    Used by Docker HEALTHCHECK, Render health checks, and load balancers.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({'status': 'ok', 'service': 'breathe-esg'})

