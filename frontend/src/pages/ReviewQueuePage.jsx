/**
 * pages/ReviewQueuePage.jsx
 * ─────────────────────────
 * Review queue page with filter bar, data table, pagination,
 * and bulk actions. Uses mock data when the backend is unavailable.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, CheckCircle2, XCircle } from 'lucide-react';
import { recordsAPI } from '../api/client';
import ReviewTable from '../components/ReviewTable';
import ConfirmModal from '../components/ConfirmModal';
import './ReviewQueuePage.css';

/* ── Mock data ────────────────────────────────────────────── */
function generateMockRecords(count = 25) {
  const statuses = ['uploaded', 'parsed', 'suspicious', 'approved', 'failed', 'locked'];
  const sources = ['sap_fuel', 'electricity', 'travel'];
  const scopes = [1, 2, 3];
  const units = ['litres', 'kWh', 'km'];

  return Array.from({ length: count }, (_, i) => ({
    id: crypto.randomUUID ? crypto.randomUUID() : `rec-${String(i).padStart(4, '0')}-${Math.random().toString(36).slice(2, 10)}`,
    source_type: sources[i % 3],
    date: `2024-03-${String((i % 28) + 1).padStart(2, '0')}`,
    original_value: (Math.random() * 500 + 10).toFixed(1),
    original_unit: units[i % 3],
    emissions_kg_co2e: (Math.random() * 2000 + 50).toFixed(1),
    scope: scopes[i % 3],
    status: statuses[i % statuses.length],
    is_suspicious: i % 7 === 0,
  }));
}

const MOCK_RECORDS = generateMockRecords(48);

export default function ReviewQueuePage() {
  const navigate = useNavigate();

  /* ── State ──────────────────────────────────────────────── */
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(new Set());
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    status: '',
    source_type: '',
    scope: '',
    search: '',
  });
  const [confirmModal, setConfirmModal] = useState({ open: false, type: '' });

  const pageSize = 10;

  /* ── Fetch records ──────────────────────────────────────── */
  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const res = await recordsAPI.list({ page, ...filters });
        setRecords(res.data.results || res.data);
      } catch {
        setRecords(MOCK_RECORDS);
      }
      setLoading(false);
    };
    fetch();
  }, [page, filters]);

  /* ── Derived ────────────────────────────────────────────── */
  const filtered = records.filter((r) => {
    if (filters.status && r.status !== filters.status) return false;
    if (filters.source_type && r.source_type !== filters.source_type) return false;
    if (filters.scope && String(r.scope) !== filters.scope) return false;
    if (filters.search) {
      const q = filters.search.toLowerCase();
      return (
        r.id.toLowerCase().includes(q) ||
        r.source_type.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const paged = filtered.slice((page - 1) * pageSize, page * pageSize);

  /* ── Handlers ───────────────────────────────────────────── */
  const handleToggle = (id) =>
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const handleToggleAll = (checked) => {
    if (checked) {
      setSelected(new Set(paged.map((r) => r.id)));
    } else {
      setSelected(new Set());
    }
  };

  const handleBulkAction = (type) => {
    if (selected.size === 0) return;
    setConfirmModal({
      open: true,
      type,
      title: type === 'approve' ? 'Approve Selected Records' : 'Reject Selected Records',
      message: `Are you sure you want to ${type} ${selected.size} record(s)?`,
    });
  };

  const handleConfirm = useCallback(
    (comment) => {
      // In prototype mode, just update statuses locally
      const newStatus = confirmModal.type === 'approve' ? 'approved' : 'failed';
      setRecords((prev) =>
        prev.map((r) => (selected.has(r.id) ? { ...r, status: newStatus } : r))
      );
      setSelected(new Set());
      setConfirmModal({ open: false, type: '' });
    },
    [confirmModal.type, selected]
  );

  const handleApprove = (id) => {
    setRecords((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'approved' } : r))
    );
  };

  const handleReject = (id) => {
    setRecords((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'failed' } : r))
    );
  };

  const handleView = (id) => navigate(`/review/${id}`);

  const handleFilterChange = (key, value) => {
    setFilters((f) => ({ ...f, [key]: value }));
    setPage(1);
  };

  /* ── Render ─────────────────────────────────────────────── */
  return (
    <div className="review-page">
      <div className="page-header animate-fade-in-up">
        <h1 className="page-title">Review Queue</h1>
        <p className="page-subtitle">
          Review, approve, or reject normalized ESG records
        </p>
      </div>

      {/* ── Filter bar ────────────────────────────────────── */}
      <div className="review-page__filters glass-card animate-fade-in-up delay-1" style={{ opacity: 0 }}>
        <div className="review-page__filter-row">
          <div className="review-page__search">
            <Search size={16} />
            <input
              className="input-field"
              type="text"
              placeholder="Search records…"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>

          <select
            className="input-field"
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="uploaded">Uploaded</option>
            <option value="parsed">Parsed</option>
            <option value="suspicious">Suspicious</option>
            <option value="approved">Approved</option>
            <option value="failed">Failed</option>
            <option value="locked">Locked</option>
          </select>

          <select
            className="input-field"
            value={filters.source_type}
            onChange={(e) => handleFilterChange('source_type', e.target.value)}
          >
            <option value="">All Sources</option>
            <option value="sap_fuel">SAP Fuel</option>
            <option value="electricity">Electricity</option>
            <option value="travel">Travel</option>
          </select>

          <select
            className="input-field"
            value={filters.scope}
            onChange={(e) => handleFilterChange('scope', e.target.value)}
          >
            <option value="">All Scopes</option>
            <option value="1">Scope 1</option>
            <option value="2">Scope 2</option>
            <option value="3">Scope 3</option>
          </select>
        </div>

        {/* Bulk actions + count */}
        <div className="review-page__actions-bar">
          <span className="review-page__count">
            Showing {paged.length} of {filtered.length} records
          </span>

          <div className="review-page__bulk">
            <button
              className="btn btn-sm btn-success"
              disabled={selected.size === 0}
              onClick={() => handleBulkAction('approve')}
            >
              <CheckCircle2 size={14} /> Approve Selected
            </button>
            <button
              className="btn btn-sm btn-danger"
              disabled={selected.size === 0}
              onClick={() => handleBulkAction('reject')}
            >
              <XCircle size={14} /> Reject Selected
            </button>
          </div>
        </div>
      </div>

      {/* ── Table ─────────────────────────────────────────── */}
      <div className="animate-fade-in-up delay-2" style={{ opacity: 0 }}>
        {loading ? (
          <div className="skeleton skeleton-card" style={{ height: 400 }} />
        ) : (
          <ReviewTable
            records={paged}
            selected={selected}
            onToggle={handleToggle}
            onToggleAll={handleToggleAll}
            onApprove={handleApprove}
            onReject={handleReject}
            onView={handleView}
          />
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
              // Add ellipsis
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

      {/* ── Confirm Modal ─────────────────────────────────── */}
      <ConfirmModal
        open={confirmModal.open}
        title={confirmModal.title}
        message={confirmModal.message}
        confirmLabel={confirmModal.type === 'approve' ? 'Approve' : 'Reject'}
        confirmVariant={confirmModal.type === 'approve' ? 'success' : 'danger'}
        showComment={confirmModal.type === 'reject'}
        onConfirm={handleConfirm}
        onCancel={() => setConfirmModal({ open: false, type: '' })}
      />
    </div>
  );
}
