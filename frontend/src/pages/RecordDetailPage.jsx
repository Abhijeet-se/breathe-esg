/**
 * pages/RecordDetailPage.jsx
 * ──────────────────────────
 * Split-pane detail view for a single normalized record.
 *
 *   Left pane:  Record data form (editable when not locked)
 *               + validation errors
 *   Right pane: Audit timeline for this record
 *   Bottom:     Action buttons (Save, Approve, Reject, Lock)
 *
 * Uses mock data when backend is unavailable.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Lock, CheckCircle2, XCircle, Save } from 'lucide-react';
import { recordsAPI, auditAPI } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import ScopeTag from '../components/ScopeTag';
import RecordEditor from '../components/RecordEditor';
import ValidationErrors from '../components/ValidationErrors';
import AuditTimeline from '../components/AuditTimeline';
import ConfirmModal from '../components/ConfirmModal';
import './RecordDetailPage.css';

/* ── Mock record ──────────────────────────────────────────── */
const MOCK_RECORD = {
  id: 'a1b2c3d4-e5f6-7890-abcd-1234567890ab',
  source_type: 'sap_fuel',
  date: '2024-03-15',
  original_value: '245.5',
  original_unit: 'litres',
  normalized_value: '245.5',
  normalized_unit: 'litres',
  emissions_kg_co2e: '612.3',
  scope: 1,
  category: 'mobile_combustion',
  status: 'parsed',
  is_suspicious: false,
  validation_errors: [
    { field: 'emissions_kg_co2e', rule: 'range_check', message: 'Value exceeds expected range for this category', severity: 'warning' },
  ],
};

export default function RecordDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [record, setRecord] = useState(null);
  const [auditEntries, setAuditEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [modal, setModal] = useState({ open: false, type: '' });

  /* ── Fetch record + audit log ───────────────────────────── */
  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const [recRes, auditRes] = await Promise.all([
          recordsAPI.get(id),
          auditAPI.getForRecord(id),
        ]);
        setRecord(recRes.data);
        setAuditEntries(auditRes.data.results || auditRes.data);
      } catch {
        // Fallback to mock
        setRecord({ ...MOCK_RECORD, id });
        setAuditEntries([]);
      }
      setLoading(false);
    };
    fetch();
  }, [id]);

  /* ── Field change handler ───────────────────────────────── */
  const handleChange = useCallback((field, value) => {
    setRecord((r) => ({ ...r, [field]: value }));
  }, []);

  /* ── Save ───────────────────────────────────────────────── */
  const handleSave = async () => {
    setSaving(true);
    try {
      await recordsAPI.update(id, {
        normalized_value: record.normalized_value,
        normalized_unit: record.normalized_unit,
        emissions_kg_co2e: record.emissions_kg_co2e,
        scope: record.scope,
        category: record.category,
      });
    } catch {
      /* demo mode — just keep local state */
    }
    setSaving(false);
  };

  /* ── Approve / Reject / Lock ────────────────────────────── */
  const handleAction = useCallback(
    async (comment) => {
      const type = modal.type;
      try {
        if (type === 'approve') await recordsAPI.approve(id, comment);
        else if (type === 'reject') await recordsAPI.reject(id, comment);
        else if (type === 'lock') await recordsAPI.lock(id);
      } catch {
        /* demo mode */
      }

      const statusMap = { approve: 'approved', reject: 'failed', lock: 'locked' };
      setRecord((r) => ({ ...r, status: statusMap[type] || r.status }));
      setModal({ open: false, type: '' });
    },
    [id, modal.type]
  );

  const isLocked = record?.status === 'locked';

  /* ── Loading skeleton ───────────────────────────────────── */
  if (loading) {
    return (
      <div className="record-detail">
        <div className="skeleton skeleton-heading" style={{ width: '30%' }} />
        <div className="record-detail__body">
          <div className="skeleton skeleton-card" style={{ height: 350 }} />
          <div className="skeleton skeleton-card" style={{ height: 350 }} />
        </div>
      </div>
    );
  }

  if (!record) {
    return (
      <div className="empty-state">
        <p>Record not found</p>
        <button className="btn btn-ghost" onClick={() => navigate('/review')}>
          Back to Review Queue
        </button>
      </div>
    );
  }

  return (
    <div className="record-detail animate-fade-in">
      {/* ── Header ────────────────────────────────────────── */}
      <div className="record-detail__header">
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/review')}>
          <ArrowLeft size={16} /> Back
        </button>
        <div className="record-detail__header-info">
          <h1 className="page-title">Record Detail</h1>
          <span className="record-detail__id" title={record.id}>
            {record.id.slice(0, 12)}…
          </span>
        </div>
        <div className="record-detail__header-badges">
          <StatusBadge status={record.status} />
          <ScopeTag scope={record.scope} />
        </div>
      </div>

      {/* ── Locked banner ─────────────────────────────────── */}
      {isLocked && (
        <div className="locked-banner">
          <Lock size={16} /> This record is locked for audit — editing is disabled.
        </div>
      )}

      {/* ── Body (split) ──────────────────────────────────── */}
      <div className="record-detail__body">
        {/* Left: Editor + Validation Errors */}
        <div className="glass-card" style={{ padding: 'var(--space-6)' }}>
          <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 600, marginBottom: 'var(--space-5)' }}>
            Record Data
          </h3>
          <RecordEditor
            record={record}
            onChange={handleChange}
            onSave={handleSave}
            onCancel={() => navigate('/review')}
            disabled={isLocked}
          />
          <ValidationErrors errors={record.validation_errors} />
        </div>

        {/* Right: Audit Timeline */}
        <div className="glass-card">
          <AuditTimeline entries={auditEntries} />
        </div>
      </div>

      {/* ── Action buttons ────────────────────────────────── */}
      {!isLocked && (
        <div className="record-detail__actions">
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? <span className="spinner" /> : <><Save size={16} /> Save Changes</>}
          </button>
          <button
            className="btn btn-success"
            onClick={() => setModal({ open: true, type: 'approve', title: 'Approve Record', message: 'Mark this record as approved?' })}
            disabled={record.status === 'approved'}
          >
            <CheckCircle2 size={16} /> Approve
          </button>
          <button
            className="btn btn-danger"
            onClick={() => setModal({ open: true, type: 'reject', title: 'Reject Record', message: 'Are you sure you want to reject this record?' })}
          >
            <XCircle size={16} /> Reject
          </button>
          <button
            className="btn btn-ghost"
            onClick={() => setModal({ open: true, type: 'lock', title: 'Lock Record', message: 'Lock this record for audit? This cannot be easily undone.' })}
          >
            <Lock size={16} /> Lock
          </button>
        </div>
      )}

      {/* ── Confirm Modal ─────────────────────────────────── */}
      <ConfirmModal
        open={modal.open}
        title={modal.title}
        message={modal.message}
        confirmLabel={modal.type === 'approve' ? 'Approve' : modal.type === 'reject' ? 'Reject' : 'Lock'}
        confirmVariant={modal.type === 'approve' ? 'success' : modal.type === 'reject' ? 'danger' : 'primary'}
        showComment={modal.type === 'reject'}
        onConfirm={handleAction}
        onCancel={() => setModal({ open: false, type: '' })}
      />
    </div>
  );
}
