# TRADEOFFS.md — Design Tradeoffs Analysis

This document analyzes the key tradeoffs made in the Breathe ESG platform design,
explaining what was gained and what was sacrificed in each decision.

---

## 1. Synchronous vs. Asynchronous File Processing

### Chosen: Synchronous processing

| Aspect          | Synchronous (Chosen)            | Asynchronous (Alternative)      |
|-----------------|----------------------------------|----------------------------------|
| Complexity      | ✅ Simple, no message broker     | ❌ Requires Redis + Celery       |
| Deployment      | ✅ Single process                | ❌ Worker process + broker       |
| File Size Limit | ❌ ~10K rows before timeout      | ✅ Unlimited with chunking       |
| User Feedback   | ❌ Blocks until complete         | ✅ Real-time progress via WS     |
| Error Handling  | ✅ Immediate error response      | ⚠️ Requires polling/notifications|
| Cost            | ✅ No additional infrastructure  | ❌ Redis hosting cost            |

**Verdict:** Acceptable for prototype. Clear upgrade path documented.

---

## 2. Shared-Schema vs. Schema-Per-Tenant Multi-Tenancy

### Chosen: Shared schema with row-level isolation

| Aspect          | Shared Schema (Chosen)          | Schema-Per-Tenant                |
|-----------------|----------------------------------|----------------------------------|
| Isolation       | ⚠️ Application-level only       | ✅ Database-level isolation      |
| Complexity      | ✅ Standard Django models        | ❌ Custom DB routing, migrations |
| Scalability     | ✅ Easy to add tenants           | ⚠️ 100+ schemas becomes slow    |
| Performance     | ⚠️ Large tables, needs indexes  | ✅ Smaller per-tenant tables     |
| Data Leak Risk  | ⚠️ Bug could expose data        | ✅ Impossible by DB design       |
| Migration       | ✅ Single migration run          | ❌ Must migrate each schema      |
| Backup/Restore  | ⚠️ All-or-nothing backup        | ✅ Per-tenant backup possible    |

**Verdict:** Row-level isolation is the industry standard for SaaS prototypes.
The risk of data leaks is mitigated by middleware enforcement and test coverage.

---

## 3. JSON vs. Columnar Storage for Raw Data

### Chosen: JSON field for original_data

| Aspect          | JSON Field (Chosen)             | Dedicated Columns                |
|-----------------|----------------------------------|----------------------------------|
| Flexibility     | ✅ Any source format stored      | ❌ Must know schema upfront      |
| Query Speed     | ❌ JSON queries are slower       | ✅ Native column indexing        |
| Storage         | ⚠️ Slightly larger              | ✅ More compact                  |
| Schema Changes  | ✅ No migrations needed          | ❌ Migration for each new field  |
| Audit Trail     | ✅ Exact original preserved      | ⚠️ Transformation lost          |
| Type Safety     | ❌ No DB-level type enforcement  | ✅ Database enforces types       |

**Verdict:** JSON storage for raw records is essential because source formats
vary by data source type (SAP, electricity, travel) and may change over time.
The normalized record provides the structured, queryable representation.

---

## 4. Static vs. Dynamic Emission Factors

### Chosen: Static factors in code

| Aspect          | Static Factors (Chosen)         | Dynamic Factor Database          |
|-----------------|----------------------------------|----------------------------------|
| Simplicity      | ✅ Constants in code             | ❌ Additional model + admin UI   |
| Auditability    | ✅ Version controlled            | ⚠️ Requires factor versioning   |
| Flexibility     | ❌ Code change to update         | ✅ Admin can update factors      |
| Accuracy        | ⚠️ Global averages only         | ✅ Location-specific possible    |
| Reproducibility | ✅ Same code = same result       | ⚠️ Must track which version used|

**Verdict:** Static factors are sufficient for a prototype and are easier to audit.
The code includes clear documentation of factor sources and values.

---

## 5. JWT in localStorage vs. httpOnly Cookies

### Chosen: JWT in localStorage

| Aspect          | localStorage (Chosen)           | httpOnly Cookies                 |
|-----------------|----------------------------------|----------------------------------|
| XSS Protection  | ❌ Vulnerable to XSS            | ✅ Not accessible to JS          |
| CSRF Protection | ✅ Not vulnerable to CSRF       | ❌ Requires CSRF tokens          |
| Implementation  | ✅ Simple axios interceptor     | ⚠️ More complex setup           |
| Cross-origin    | ✅ Works across origins          | ⚠️ SameSite cookie issues       |
| Mobile/API      | ✅ Same pattern for all clients  | ❌ Cookie-dependent              |

**Verdict:** For an internal enterprise tool with controlled deployment, localStorage
is acceptable. Production hardening would move to httpOnly cookies with CSRF protection.

---

## 6. Single Monorepo vs. Separate Repositories

### Chosen: Monorepo

| Aspect          | Monorepo (Chosen)               | Separate Repos                   |
|-----------------|----------------------------------|----------------------------------|
| Development     | ✅ Single clone, single PR      | ❌ Coordinate across repos       |
| CI/CD           | ⚠️ Must filter changed paths   | ✅ Independent pipelines         |
| Dependencies    | ✅ Shared configs               | ❌ Duplication of configs        |
| Team Scaling    | ⚠️ More merge conflicts        | ✅ Independent team velocity     |
| Deployment      | ✅ Atomic deploys               | ⚠️ Version compatibility issues |

**Verdict:** Monorepo is appropriate for a team of 1-5 developers working on a
tightly coupled frontend/backend application.

---

## 7. Denormalized Fields vs. Pure Normalization

### Chosen: Strategic denormalization on NormalizedRecord

**What's denormalized:**
- `tenant_id` (could be derived from batch → data_source → tenant)
- `source_type` (could be derived from batch → data_source)
- `batch_id` (could be derived from raw_record → batch)

**Why:**
Dashboard queries run every page load and aggregate across thousands of records.
Without denormalization, every stat query requires 3-4 JOINs:
```sql
-- Without denormalization (slow):
SELECT COUNT(*) FROM normalized_record nr
JOIN raw_record rr ON nr.raw_record_id = rr.id
JOIN upload_batch ub ON rr.batch_id = ub.id
WHERE ub.tenant_id = X AND nr.status = 'approved';

-- With denormalization (fast):
SELECT COUNT(*) FROM normalized_record
WHERE tenant_id = X AND status = 'approved';
```

**Risk:** Data inconsistency if the denormalized fields are not maintained.
**Mitigation:** These fields are set once during record creation and never updated.

---

## 8. All-in-One Upload Endpoint vs. Separate Steps

### Chosen: Single upload endpoint that triggers full pipeline

| Aspect          | Single Endpoint (Chosen)        | Multi-Step (Upload → Parse → Validate) |
|-----------------|----------------------------------|----------------------------------------|
| User Experience | ✅ Upload and get results        | ⚠️ Must trigger each step              |
| Simplicity      | ✅ One API call                  | ❌ 3+ API calls with state management  |
| Error Recovery  | ❌ Must re-upload entire file    | ✅ Can retry individual steps           |
| Partial Results | ❌ All-or-nothing                | ✅ Can review parsed before validating  |

**Verdict:** Single endpoint simplifies the prototype. The pipeline is:
`upload → parse → validate → normalize → save`. Each step's results are
recorded, and individual records can be re-validated after editing.

---

## Summary Matrix

| Decision              | Optimized For            | Sacrificed                   |
|-----------------------|--------------------------|------------------------------|
| Synchronous processing| Simplicity, deployment   | Large file support           |
| Shared-schema tenancy | Development speed        | Schema-level isolation       |
| JSON raw storage      | Flexibility, audit trail | Query performance on raw data|
| Static emission factors| Auditability, simplicity| Dynamic factor management    |
| JWT in localStorage   | Implementation simplicity| XSS protection               |
| Monorepo structure    | Development workflow     | Independent scaling          |
| Denormalized fields   | Query performance        | Storage efficiency           |
| Single upload endpoint| User experience          | Granular error recovery      |
