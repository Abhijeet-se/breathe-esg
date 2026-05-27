/**
 * pages/AuditTrailPage.jsx
 * ────────────────────────
 * Global audit trail view showing all record changes across
 * the tenant. Supports filters (date range, action type, user)
 * and pagination. Falls back to mock data.
 */

import React, { useState, useEffect } from 'react';
import { ArrowRight } from 'lucide-react';
import { auditAPI } from '../api/client';
import './AuditTrailPage.css';

/* ── Mock Data ────────────────────────────────────────────── */
const ACTIONS = ['create', 'edit', 'approve', 'reject', 'lock'];
const USERS = ['jane.doe@acme.com', 'admin@acme.com', 'john.smith@acme.com', 'system'];
const FIELDS = [null, 'emissions_kg_co2e', 'scope', 'normalized_value', 'status', 'category'];

function generateMockAudit(count = 60) {
  return Array.from({ length: count }, (_, i) => {
    const action = ACTIONS[i % ACTIONS.length];
    const field = action === 'edit' ? FIELDS[1 + (i % (FIELDS.length - 1))] : null;
    return {
      id: i + 1,
      record_id: `rec-${String(i % 20).padStart(4, '0')}`,
      action,
      field,
      old_value: field ? `old_${i}` : null,
      new_value: field ? `new_${i}` : null,
      changed_by: USERS[i % USERS.length],
      timestamp: new Date(Date.now() - i * 3600 * 1000 * 2).toISOString(),
    };
  });
}

const MOCK_AUDIT = generateMockAudit();

const ACTION_COLORS = {
  create:  '#3b82f6',
  edit:    '#f59e0b',
  approve: '#10b981',
  reject:  '#ef4444',
  lock:    '#8b5cf6',
};

export default function AuditTrailPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({ action: '', user: '' });
  const pageSize = 15;

  /* ── Fetch ──────────────────────────────────────────────── */
  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const res = await auditAPI.list({ page, ...filters });
        setEntries(res.data.results || res.data);
      } catch {
        setEntries(MOCK_AUDIT);
      }
      setLoading(false);
    };
    fetch();
  }, [page, filters]);

  /* ── Client-side filter (for mock mode) ─────────────────── */
  const filtered = entries.filter((e) => {
    if (filters.action && e.action !== filters.action) return false;
    if (filters.user && !e.changed_by.toLowerCase().includes(filters.user.toLowerCase())) return false;
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const paged = filtered.slice((page - 1) * pageSize, page * pageSize);

  const handleFilterChange = (key, value) => {
    setFilters((f) => ({ ...f, [key]: value }));
    setPage(1);
  };

  /* ── Render ─────────────────────────────────────────────── */
  return (
    <div className="audit-page">
      <div className="page-header animate-fade-in-up">
        <h1 className="page-title">Audit Trail</h1>
        <p className="page-subtitle">
          Complete history of changes across all records
        </p>
      </div>

      {/* ── Filters ───────────────────────────────────────── */}
      <div className="audit-page__filters glass-card animate-fade-in-up delay-1" style={{ opacity: 0 }}>
        <select
          className="input-field"
          value={filters.action}
          onChange={(e) => handleFilterChange('action', e.target.value)}
        >
          <option value="">All Actions</option>
          {ACTIONS.map((a) => (
            <option key={a} value={a}>{a.charAt(0).toUpperCase() + a.slice(1)}</option>
          ))}
        </select>
        <input
          className="input-field"
          type="text"
          placeholder="Filter by user…"
          value={filters.user}
          onChange={(e) => handleFilterChange('user', e.target.value)}
        />
      </div>

      {/* ── Table ─────────────────────────────────────────── */}
      <div className="animate-fade-in-up delay-2" style={{ opacity: 0 }}>
        {loading ? (
          <div className="skeleton skeleton-card" style={{ height: 460 }} />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Record ID</th>
                  <th>Action</th>
                  <th>Field</th>
                  <th>Old Value</th>
                  <th></th>
                  <th>New Value</th>
                  <th>Changed By</th>
                </tr>
              </thead>
              <tbody>
                {paged.map((entry) => (
                  <tr key={entry.id}>
                    <td style={{ whiteSpace: 'nowrap', fontSize: 'var(--font-size-xs)' }}>
                      {new Date(entry.timestamp).toLocaleString('en-US', {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                      })}
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>
                      {entry.record_id.slice(0, 12)}
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          color: ACTION_COLORS[entry.action] || 'var(--text-secondary)',
                          background: `${ACTION_COLORS[entry.action]}22`,
                        }}
                      >
                        {entry.action}
                      </span>
                    </td>
                    <td style={{ color: 'var(--text-secondary)' }}>{entry.field || '—'}</td>
                    <td style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-xs)' }}>
                      {entry.old_value || '—'}
                    </td>
                    <td>
                      {entry.field && <ArrowRight size={12} style={{ color: 'var(--text-tertiary)' }} />}
                    </td>
                    <td style={{ color: 'var(--color-success)', fontWeight: 600, fontSize: 'var(--font-size-xs)' }}>
                      {entry.new_value || '—'}
                    </td>
                    <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-tertiary)' }}>
                      {entry.changed_by}
                    </td>
                  </tr>
                ))}

                {paged.length === 0 && (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', padding: 'var(--space-10)', color: 'var(--text-tertiary)' }}>
                      No audit entries found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Pagination ────────────────────────────────────── */}
      {totalPages > 1 && (
        <div className="pagination">
          <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter((p) => Math.abs(p - page) <= 2 || p === 1 || p === totalPages)
            .map((p, idx, arr) => {
              const prev = arr[idx - 1];
              const showEllipsis = prev && p - prev > 1;
              return (
                <React.Fragment key={p}>
                  {showEllipsis && <span style={{ color: 'var(--text-tertiary)' }}>…</span>}
                  <button className={p === page ? 'active' : ''} onClick={() => setPage(p)}>
                    {p}
                  </button>
                </React.Fragment>
              );
            })}
          <button disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </button>
        </div>
      )}
    </div>
  );
}
