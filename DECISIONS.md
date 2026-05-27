# DECISIONS.md — Architectural Decision Records

This document records the key architectural and design decisions made during the
development of the Breathe ESG Data Ingestion Platform.

---

## ADR-001: Django + DRF for Backend

**Status:** Accepted

**Context:**
We needed a backend framework that provides ORM, authentication, admin interface,
and API capabilities out of the box for rapid prototype development.

**Decision:**
Use Django 4.2 with Django REST Framework.

**Rationale:**
- Django's ORM handles complex model relationships cleanly
- Built-in migration system ensures schema versioning
- DRF provides serialization, viewsets, permissions, and throttling
- Large ecosystem of packages (JWT, CORS, database URL parsing)
- Excellent admin interface for debugging data
- Well-suited for data-heavy applications

**Alternatives Considered:**
- FastAPI: Faster async performance, but less mature ORM story and no built-in admin
- Express.js: Would require separate ORM (Prisma/TypeORM), more boilerplate
- Spring Boot: Java overhead not justified for a prototype

---

## ADR-002: React + Vite for Frontend

**Status:** Accepted

**Context:**
The frontend needs to be a modern SPA with complex data tables, file upload
interactions, and real-time-feeling workflows.

**Decision:**
Use React 18 with Vite build tool and Vanilla CSS.

**Rationale:**
- React's component model is ideal for complex data-driven UIs
- Vite provides fast HMR (Hot Module Replacement) for development
- Vanilla CSS with Custom Properties gives full control over the design system
- No CSS framework dependency to manage or customize

**Alternatives Considered:**
- Next.js: SSR benefits not needed for an internal enterprise dashboard
- Vue.js: Equally viable; React chosen for larger ecosystem
- Tailwind CSS: Avoided per project guidelines; Vanilla CSS offers more control

---

## ADR-003: Row-Level Multi-Tenancy

**Status:** Accepted

**Context:**
Enterprise clients need complete data isolation. Each company must only see their
own uploaded data, records, and audit trails.

**Decision:**
Implement row-level tenant isolation via foreign keys and middleware filtering.

**Rationale:**
- Simplest approach that provides strong isolation
- Single database reduces operational complexity
- Middleware ensures every request is tenant-scoped
- All querysets automatically filtered
- Easy to implement in both models and serializers

**Trade-offs:**
- Requires discipline: every query must include tenant filter
- No schema-level isolation (a bug could leak data)
- Performance could degrade with very large tenant datasets (mitigated by indexing)

---

## ADR-004: UUID Primary Keys

**Status:** Accepted

**Context:**
Records are shared across API boundaries and may be referenced in audit reports.

**Decision:**
Use UUID v4 as primary keys for all models.

**Rationale:**
- Prevents sequential ID enumeration attacks
- Safe to expose in URLs and API responses
- Globally unique across tenants and databases
- Compatible with future distributed/sharded architectures

**Trade-offs:**
- Slightly larger storage than integer PKs
- Not naturally sortable (we use `created_at` for ordering)
- Index performance slightly lower than integers

---

## ADR-005: Raw + Normalized Record Separation

**Status:** Accepted

**Context:**
ESG data undergoes significant transformation: unit conversion, emissions calculation,
header mapping, and validation. We need to preserve the original data for audit purposes.

**Decision:**
Maintain separate `RawRecord` and `NormalizedRecord` models linked 1:1.

**Rationale:**
- `RawRecord.original_data` (JSON) preserves the exact uploaded values
- `NormalizedRecord` contains processed, standardized values
- Analysts can compare original vs. normalized during review
- Audit trail can reference both states
- Locked records maintain immutable connection to source data

**Alternatives Considered:**
- Single record with both original and normalized fields: Would create very wide tables
- Storing original data only in the file: Harder to query and compare row-by-row

---

## ADR-006: Synchronous Processing (No Celery)

**Status:** Accepted (prototype scope)

**Context:**
File uploads need to be parsed, validated, and normalized. This could be done
synchronously or asynchronously.

**Decision:**
Process uploads synchronously in the API request-response cycle.

**Rationale:**
- Eliminates need for message broker (Redis/RabbitMQ) and Celery worker
- Simpler deployment topology
- Acceptable for prototype file sizes (< 10,000 rows)
- Upload progress is handled by the frontend's file upload tracking

**Production Upgrade Path:**
For production with large files (> 50,000 rows), add:
1. Celery with Redis as broker
2. WebSocket/SSE for real-time progress updates
3. Chunked processing in background tasks

---

## ADR-007: JWT Authentication

**Status:** Accepted

**Context:**
The SPA frontend needs stateless authentication for API calls.

**Decision:**
Use djangorestframework-simplejwt for token-based authentication.

**Rationale:**
- Stateless: no server-side session storage needed
- Standard Bearer token pattern for API calls
- Built-in token refresh mechanism
- Compatible with deployment on stateless platforms (Render, Railway)

**Configuration:**
- Access token lifetime: 30 minutes
- Refresh token lifetime: 7 days
- Token stored in localStorage (acceptable for internal enterprise app)

---

## ADR-008: Emissions Factor Approach

**Status:** Accepted

**Context:**
The normalization engine needs to convert raw quantities into kg CO2e emissions.

**Decision:**
Use static emission factors from published sources (DEFRA, EPA, GHG Protocol).

**Rationale:**
- Deterministic and auditable calculations
- Industry-standard factors
- Easy to update when new factors are published
- Sufficient for prototype accuracy

**Factors Used:**
| Source Type    | Factor              | Value          | Reference       |
|---------------|---------------------|----------------|-----------------|
| Diesel        | per liter           | 2.68 kg CO2e   | DEFRA 2023      |
| Petrol        | per liter           | 2.31 kg CO2e   | DEFRA 2023      |
| Natural Gas   | per m³              | 2.00 kg CO2e   | DEFRA 2023      |
| Electricity   | per kWh             | 0.38 kg CO2e   | IEA Global Avg  |
| Flight        | per passenger-km    | 0.255 kg CO2e  | DEFRA 2023      |
| Train         | per passenger-km    | 0.041 kg CO2e  | DEFRA 2023      |
| Hotel         | per room-night      | 31.1 kg CO2e   | Cornell/CHSB    |
| Car           | per km              | 0.21 kg CO2e   | EPA 2023        |

**Future Improvement:**
- Location-specific grid emission factors for Scope 2
- Flight class multipliers (business = 2.9x economy)
- Dynamic factor database with versioning

---

## ADR-009: Validation as a Pipeline

**Status:** Accepted

**Context:**
Each uploaded row needs multiple validation checks before being accepted.

**Decision:**
Implement validation as a composable pipeline of check functions.

**Rationale:**
- Each validation rule is a pure function: `(record, context) → [errors]`
- Rules can be composed into chains per source type
- Easy to add new rules without modifying existing ones
- Validation results stored as JSON array on the record
- Enables both blocking (fail) and non-blocking (suspicious) outcomes

---

## ADR-010: Audit Log as Append-Only Event Stream

**Status:** Accepted

**Context:**
Regulatory compliance requires a tamper-resistant record of all changes.

**Decision:**
AuditLog table is append-only. No updates or deletes are ever performed.

**Rationale:**
- Provides a complete, immutable history of every change
- Each entry captures: who, what, when, old value, new value
- Can reconstruct the full state of any record at any point in time
- Suitable for SOX, GHG Protocol, and CSRD audit requirements

---

## ADR-011: Status Lifecycle State Machine

**Status:** Accepted

**Context:**
Records move through a defined lifecycle from upload to audit lock.

**Decision:**
Implement a strict status transition model:
```
uploaded → parsed → approved → locked
                  → failed (terminal unless re-parsed)
                  → suspicious → approved → locked
                               → rejected (can be re-reviewed)
```

**Rationale:**
- Prevents invalid state transitions (e.g., locking a failed record)
- Each transition creates an audit log entry
- Locked records cannot be edited (enforced at API level)
- Clear workflow for analysts: review → decide → lock

---

## ADR-012: Denormalized Fields on NormalizedRecord

**Status:** Accepted

**Context:**
Dashboard queries need to aggregate records by tenant, source type, and scope.

**Decision:**
Denormalize `tenant_id`, `source_type`, and `batch_id` onto `NormalizedRecord`.

**Rationale:**
- Eliminates multi-table JOINs for dashboard statistics
- Acceptable trade-off: minimal storage overhead
- Data consistency maintained by application logic (set once during creation)
- Critical for performant queries: `SELECT COUNT(*) WHERE tenant_id=X AND status='approved'`
