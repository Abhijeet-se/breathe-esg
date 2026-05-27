"""
Ingestion Models
================

Core data models for the ESG emissions data ingestion pipeline.

Data Flow:
    1. User uploads a file -> UploadBatch created
    2. Parser reads file rows -> RawRecord created for each row (preserves original data)
    3. Normalizer processes each raw record -> NormalizedRecord created
    4. Validator checks each normalized record -> validation_errors & suspicious flags set
    5. Reviewer approves/rejects records -> ApprovalRecord created, AuditLog updated
    6. Admin locks approved records -> prevents further edits

Design Decisions:
- RawRecord preserves exact original data as JSON for audit trail
- NormalizedRecord has denormalized fields (tenant, source_type) for query performance
- AuditLog tracks every change for complete traceability
- Status workflow: uploaded -> parsed -> (failed|suspicious|approved|locked)
- All models use UUID primary keys and tenant-scoping
"""

import uuid
from django.db import models
from django.conf import settings


class DataSource(models.Model):
    """
    Represents a configured data source/integration.

    Each DataSource defines a type of data that can be ingested (e.g., SAP fuel data,
    electricity bills). The header_mappings field allows customizing column name mappings
    for sources that use non-standard headers.

    Examples:
        - "SAP Fuel Data - Germany Plant" (source_type='sap_fuel')
        - "Electricity Bills - US Operations" (source_type='electricity')
        - "Corporate Travel - 2024" (source_type='travel')
    """
    SOURCE_TYPE_CHOICES = [
        ('sap_fuel', 'SAP Fuel & Procurement'),
        ('electricity', 'Electricity Bills'),
        ('travel', 'Corporate Travel'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='data_sources',
    )
    name = models.CharField(
        max_length=255,
        help_text="Human-readable name for this data source"
    )
    source_type = models.CharField(
        max_length=50,
        choices=SOURCE_TYPE_CHOICES,
        help_text="Determines which parser is used for ingestion"
    )
    header_mappings = models.JSONField(
        null=True,
        blank=True,
        help_text="Custom column name mappings (JSON object). "
                  "Keys are expected field names, values are actual column headers."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class UploadBatch(models.Model):
    """
    Represents a single file upload and its processing state.

    Tracks the lifecycle of a file from upload through parsing completion.
    Row counters provide a quick summary without needing to count child records.

    Status Workflow:
        uploading -> processing -> completed | failed
    """
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='upload_batches',
    )
    data_source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='batches',
    )
    file_name = models.CharField(
        max_length=500,
        help_text="Original filename as uploaded by user"
    )
    file = models.FileField(
        upload_to='uploads/%Y/%m/',
        help_text="The actual uploaded file (CSV or Excel)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploading',
    )
    # Row counters for quick batch summary
    total_rows = models.IntegerField(default=0, help_text="Total rows detected in file")
    parsed_rows = models.IntegerField(default=0, help_text="Successfully parsed rows")
    failed_rows = models.IntegerField(default=0, help_text="Rows that failed parsing/validation")
    suspicious_rows = models.IntegerField(default=0, help_text="Rows flagged for review")
    approved_rows = models.IntegerField(default=0, help_text="Rows approved by reviewer")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_batches',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Upload batches'

    def __str__(self):
        return f"Batch {self.file_name} ({self.status})"


class RawRecord(models.Model):
    """
    Preserves the exact original data from each row of an uploaded file.

    This is the immutable audit trail - original_data is never modified after creation.
    Each RawRecord has exactly one corresponding NormalizedRecord (created during parsing).

    The original_data JSONField stores the row as a dict with original column names as keys.
    This preserves German headers, original number formats, etc.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.CASCADE,
        related_name='raw_records',
    )
    row_number = models.IntegerField(
        help_text="1-indexed row number from the original file (excluding header)"
    )
    original_data = models.JSONField(
        help_text="Complete original row data as key-value pairs"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['batch', 'row_number']
        # Ensure row numbers are unique within a batch
        unique_together = ['batch', 'row_number']

    def __str__(self):
        return f"Raw row {self.row_number} of {self.batch.file_name}"


class NormalizedRecord(models.Model):
    """
    The core working record - parsed, normalized, and ready for review.

    Contains both the original values (for reference) and normalized values
    (for calculations and reporting). Each record goes through a validation
    and approval workflow.

    Key Design Decisions:
    - tenant and source_type are denormalized from batch/data_source for query
      performance (avoids JOINs on every list query)
    - validation_errors stores structured error dicts for rich UI display
    - suspicious_flag + reason enable anomaly-based flagging separate from hard errors
    - status tracks the full record lifecycle

    Status Workflow:
        uploaded -> parsed -> approved -> locked  (happy path)
        uploaded -> parsed -> suspicious -> approved -> locked  (flagged path)
        uploaded -> failed  (parsing/validation failure)
    """
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('parsed', 'Parsed'),
        ('failed', 'Failed'),
        ('suspicious', 'Suspicious'),
        ('approved', 'Approved'),
        ('locked', 'Locked'),
    ]

    SCOPE_CHOICES = [
        ('scope_1', 'Scope 1 - Direct Emissions'),
        ('scope_2', 'Scope 2 - Indirect (Energy)'),
        ('scope_3', 'Scope 3 - Indirect (Value Chain)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    raw_record = models.OneToOneField(
        RawRecord,
        on_delete=models.CASCADE,
        related_name='normalized',
        help_text="Link to the original unmodified data"
    )
    # Denormalized fields for query performance
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='normalized_records',
    )
    batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.CASCADE,
        related_name='normalized_records',
    )
    source_type = models.CharField(
        max_length=50,
        help_text="Denormalized from DataSource for query performance"
    )

    # Emissions classification
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    category = models.CharField(
        max_length=100,
        help_text="E.g., 'Stationary Combustion', 'Purchased Electricity', 'Business Travel'"
    )
    record_date = models.DateField(
        help_text="The date this emission event occurred"
    )

    # Original values (preserved as-uploaded)
    original_unit = models.CharField(max_length=50)
    original_value = models.DecimalField(max_digits=18, decimal_places=6)

    # Normalized values (converted to standard units)
    normalized_unit = models.CharField(max_length=50)
    normalized_value = models.DecimalField(max_digits=18, decimal_places=6)

    # Calculated emissions
    emissions_kg_co2e = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        help_text="Calculated CO2-equivalent emissions in kilograms"
    )

    # Workflow status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        help_text="List of validation error dicts: [{field, rule, message, severity}]"
    )
    suspicious_flag = models.BooleanField(
        default=False,
        help_text="Whether anomaly detection flagged this record"
    )
    suspicious_reason = models.TextField(
        null=True,
        blank=True,
        help_text="Explanation of why this record was flagged"
    )

    # Tracking fields for the review workflow
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='edited_records',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_records',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        # Index for the most common query patterns
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'scope']),
            models.Index(fields=['tenant', 'source_type']),
            models.Index(fields=['batch', 'status']),
        ]

    def __str__(self):
        return f"Record {self.id} - {self.scope} {self.category} ({self.status})"


class AuditLog(models.Model):
    """
    Immutable audit trail for every change made to a NormalizedRecord.

    Every edit, status change, approval, rejection, and lock creates an entry.
    This provides complete traceability required for ESG compliance reporting.

    Note: AuditLog records are never updated or deleted - append only.
    """
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('edit', 'Edited'),
        ('status_change', 'Status Changed'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('lock', 'Locked'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    normalized_record = models.ForeignKey(
        NormalizedRecord,
        on_delete=models.CASCADE,
        related_name='audit_logs',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    field_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Which field was changed (null for non-edit actions)"
    )
    old_value = models.TextField(
        null=True,
        blank=True,
        help_text="Previous value before the change"
    )
    new_value = models.TextField(
        null=True,
        blank=True,
        help_text="New value after the change"
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_actions',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} on {self.normalized_record_id} by {self.changed_by}"


class ApprovalRecord(models.Model):
    """
    Records individual approval or rejection decisions on normalized records.

    Separate from AuditLog because approvals carry reviewer comments and form
    the basis of the approval workflow. A record may be rejected and re-submitted
    multiple times, creating multiple ApprovalRecords.
    """
    ACTION_CHOICES = [
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    normalized_record = models.ForeignKey(
        NormalizedRecord,
        on_delete=models.CASCADE,
        related_name='approval_records',
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reviews',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comments = models.TextField(
        blank=True,
        default='',
        help_text="Reviewer's comments explaining the decision"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} by {self.reviewer}"
