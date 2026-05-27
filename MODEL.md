# MODEL.md — Breathe ESG Data Model Documentation

## Overview

The Breathe ESG platform uses a strongly normalized relational schema designed for
multi-tenant ESG data ingestion, validation, normalization, and audit-tracked review workflows.

All models use UUID primary keys for security (no sequential ID guessing) and include
`created_at` / `updated_at` timestamps for auditability.

---

## Entity Relationship Summary

```
Tenant ─┬─> User (many)
         ├─> DataSource (many)
         ├─> UploadBatch (many)
         └─> NormalizedRecord (many, denormalized FK for query performance)

DataSource ──> UploadBatch (many)

UploadBatch ──> RawRecord (many)

RawRecord ──1:1──> NormalizedRecord

NormalizedRecord ─┬─> AuditLog (many)
                   └─> ApprovalRecord (many)
```

---

## Models

### 1. Tenant
Represents a corporate client / organization. All data is isolated per tenant.

| Field       | Type       | Description                          |
|-------------|------------|--------------------------------------|
| id          | UUID (PK)  | Unique tenant identifier             |
| name        | varchar    | Company display name                 |
| domain      | varchar    | Unique domain identifier             |
| is_active   | boolean    | Whether tenant can access the system |
| created_at  | datetime   | Record creation timestamp            |
| updated_at  | datetime   | Last modification timestamp          |

**Design Decision:** Tenant isolation is enforced via foreign keys on every data model
and a middleware that attaches the tenant context from the authenticated user's profile.
This is simpler than schema-per-tenant and works well for < 1000 tenants.

---

### 2. User (extends AbstractUser)
Platform users with role-based access control.

| Field      | Type         | Description                              |
|------------|--------------|------------------------------------------|
| id         | UUID (PK)    | Unique user identifier                   |
| tenant     | FK(Tenant)   | Which organization this user belongs to  |
| role       | enum         | 'analyst' or 'admin'                     |
| email      | varchar      | Used as the primary login credential     |
| first_name | varchar      | User's first name                        |
| last_name  | varchar      | User's last name                         |

**Roles:**
- **Analyst:** Can upload data, review records, approve/reject records.
- **Admin:** All analyst capabilities + can lock records, manage data sources, view global audit logs.

---

### 3. DataSource
Defines a configured data feed (e.g., "SAP Plant Berlin", "Grid Electricity UK").

| Field            | Type         | Description                                  |
|------------------|--------------|----------------------------------------------|
| id               | UUID (PK)    | Unique data source identifier                |
| tenant           | FK(Tenant)   | Owning organization                          |
| name             | varchar      | Human-readable source name                   |
| source_type      | enum         | 'sap_fuel', 'electricity', 'travel'          |
| header_mappings  | JSON         | Optional column name remappings              |
| description      | text         | Free-form notes about this source            |
| created_at       | datetime     | Record creation timestamp                    |
| updated_at       | datetime     | Last modification timestamp                  |

**Design Decision:** Header mappings are stored as JSON to support arbitrary column
renaming, especially for SAP exports with German headers (e.g., `Werk` → `plant_code`).

---

### 4. UploadBatch
Represents a single file upload event.

| Field           | Type          | Description                              |
|-----------------|---------------|------------------------------------------|
| id              | UUID (PK)     | Unique batch identifier                  |
| tenant          | FK(Tenant)    | Owning organization                      |
| data_source     | FK(DataSource)| Which data source this belongs to        |
| file_name       | varchar       | Original uploaded file name              |
| file            | FileField     | Stored file reference                    |
| status          | enum          | 'uploading', 'processing', 'completed', 'failed' |
| total_rows      | integer       | Total rows detected in file              |
| parsed_rows     | integer       | Successfully parsed rows                 |
| failed_rows     | integer       | Rows that failed validation              |
| suspicious_rows | integer       | Rows flagged as suspicious               |
| approved_rows   | integer       | Rows that have been approved             |
| uploaded_by     | FK(User)      | User who initiated the upload            |
| error_summary   | text          | High-level error description if failed   |
| created_at      | datetime      | Upload timestamp                         |
| updated_at      | datetime      | Last modification timestamp              |

---

### 5. RawRecord
Stores the exact original data from each row in an upload, preserving source-of-truth.

| Field          | Type            | Description                          |
|----------------|-----------------|--------------------------------------|
| id             | UUID (PK)       | Unique raw record identifier         |
| batch          | FK(UploadBatch) | Parent upload batch                  |
| row_number     | integer         | 1-indexed row number from the file   |
| original_data  | JSON            | Exact key-value pairs from the row   |
| file_hash      | varchar         | SHA-256 hash for duplicate detection |
| created_at     | datetime        | Record creation timestamp            |

**Design Decision:** We preserve the exact original data as JSON to maintain an
immutable audit trail. The normalized record links back here 1:1 so analysts can
always compare processed values against the original source.

---

### 6. NormalizedRecord
The primary working record after parsing, normalization, and emissions calculation.

| Field              | Type            | Description                                  |
|--------------------|-----------------|----------------------------------------------|
| id                 | UUID (PK)       | Unique normalized record identifier          |
| raw_record         | 1:1(RawRecord)  | Link to original raw data                    |
| tenant             | FK(Tenant)      | Denormalized for query performance           |
| batch              | FK(UploadBatch) | Denormalized for batch-level queries         |
| source_type        | varchar         | Denormalized: 'sap_fuel', 'electricity', 'travel' |
| scope              | enum            | 'scope_1', 'scope_2', 'scope_3'             |
| category           | varchar         | E.g., 'Stationary Combustion'                |
| record_date        | date            | The business date of this record             |
| original_unit      | varchar         | Unit as received from the source             |
| original_value     | decimal(16,4)   | Value as received from the source            |
| normalized_unit    | varchar         | Standardized metric unit                     |
| normalized_value   | decimal(16,4)   | Converted standardized value                 |
| emissions_kg_co2e  | decimal(16,4)   | Calculated carbon equivalent in kg CO2e      |
| status             | enum            | Workflow state (see Status Lifecycle below)  |
| validation_errors  | JSON            | Array of validation error objects            |
| suspicious_flag    | boolean         | Whether anomaly detection flagged this row   |
| suspicious_reason  | text            | Explanation of why it was flagged            |
| edited_by          | FK(User, null)  | Last user to edit this record                |
| approved_by        | FK(User, null)  | User who approved this record                |
| approved_at        | datetime(null)  | Timestamp of approval                        |
| locked_at          | datetime(null)  | Timestamp of audit lock                      |
| created_at         | datetime        | Record creation timestamp                    |
| updated_at         | datetime        | Last modification timestamp                  |

**Status Lifecycle:**
```
Uploaded → Parsed → [Failed | Suspicious | Approved] → Locked
                              ↑                ↓
                              └── (Edit) ──────┘
```

**Design Decision:** Denormalizing `tenant`, `batch`, and `source_type` onto this model
enables efficient dashboard aggregation queries without requiring JOINs through
UploadBatch → DataSource → Tenant chains.

---

### 7. AuditLog
Immutable log of every change made to a NormalizedRecord.

| Field              | Type                  | Description                        |
|--------------------|-----------------------|------------------------------------|
| id                 | UUID (PK)             | Unique log entry identifier        |
| normalized_record  | FK(NormalizedRecord)  | Which record was changed           |
| action             | enum                  | 'create', 'edit', 'status_change', 'approve', 'reject', 'lock' |
| field_name         | varchar (nullable)    | Which field was changed            |
| old_value          | text (nullable)       | Previous value                     |
| new_value          | text (nullable)       | New value                          |
| changed_by         | FK(User)              | Who made the change                |
| created_at         | datetime              | When the change occurred           |

**Design Decision:** AuditLog records are append-only and never updated or deleted.
This ensures a tamper-resistant history suitable for regulatory compliance.

---

### 8. ApprovalRecord
Tracks formal approve/reject decisions by reviewers.

| Field              | Type                  | Description                        |
|--------------------|-----------------------|------------------------------------|
| id                 | UUID (PK)             | Unique approval record identifier  |
| normalized_record  | FK(NormalizedRecord)  | Which record was reviewed          |
| reviewer           | FK(User)              | Who performed the review           |
| action             | enum                  | 'approve' or 'reject'             |
| comments           | text                  | Reviewer notes / rejection reason  |
| created_at         | datetime              | When the decision was made         |

---

## Indexing Strategy

Key indexes for query performance:
- `NormalizedRecord.tenant_id` — tenant isolation queries
- `NormalizedRecord.status` — review queue filtering
- `NormalizedRecord.batch_id` — batch-level aggregations
- `NormalizedRecord.scope` — emissions reporting by scope
- `AuditLog.normalized_record_id` — audit trail lookups
- `UploadBatch.tenant_id, created_at` — recent activity queries

---

## Multi-Tenancy Model

We use **shared-schema, shared-database** multi-tenancy with row-level isolation:
- Every data-bearing model has a `tenant` foreign key
- Django middleware extracts the tenant from the authenticated user
- All querysets are filtered by `tenant=request.tenant`
- API serializers enforce tenant context in `perform_create()`

This approach was chosen over:
- **Schema-per-tenant:** Too complex for a prototype, doesn't scale past ~50 tenants on PostgreSQL
- **Database-per-tenant:** Operational overhead of managing many databases
- **Django-tenants library:** Adds complexity; row-level filtering is sufficient here
