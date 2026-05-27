/**
 * components/ReviewTable.jsx
 * ──────────────────────────
 * Data table for the review queue. Supports:
 *  • Checkbox selection for bulk actions
 *  • Status badges, scope tags, suspicious flags
 *  • Inline approve/reject/view action buttons
 *  • Alternating row backgrounds and hover effects
 *
 * Props:
 *  • records      — array of normalized record objects
 *  • selected     — Set of selected record IDs
 *  • onToggle     — callback(id) to toggle selection
 *  • onToggleAll  — callback(checked) to select/deselect all
 *  • onApprove    — callback(id)
 *  • onReject     — callback(id)
 *  • onView       — callback(id)
 */

import React from 'react';
import { Check, X, Eye, AlertTriangle } from 'lucide-react';
import StatusBadge from './StatusBadge';
import ScopeTag from './ScopeTag';

export default function ReviewTable({
  records = [],
  selected = new Set(),
  onToggle,
  onToggleAll,
  onApprove,
  onReject,
  onView,
}) {
  const allSelected = records.length > 0 && records.every((r) => selected.has(r.id));

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="data-table">
        <thead>
          <tr>
            <th style={{ width: 40 }}>
              <input
                type="checkbox"
                className="checkbox"
                checked={allSelected}
                onChange={(e) => onToggleAll?.(e.target.checked)}
              />
            </th>
            <th>ID</th>
            <th>Source</th>
            <th>Date</th>
            <th>Value</th>
            <th>Emissions</th>
            <th>Scope</th>
            <th>Status</th>
            <th style={{ width: 40 }}></th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {records.map((rec) => (
            <tr key={rec.id} style={{ cursor: 'pointer' }} onClick={() => onView?.(rec.id)}>
              <td onClick={(e) => e.stopPropagation()}>
                <input
                  type="checkbox"
                  className="checkbox"
                  checked={selected.has(rec.id)}
                  onChange={() => onToggle?.(rec.id)}
                />
              </td>
              <td style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>
                {rec.id.slice(0, 8)}…
              </td>
              <td>{rec.source_type}</td>
              <td>{rec.date}</td>
              <td>
                {rec.original_value} {rec.original_unit}
              </td>
              <td style={{ fontWeight: 600 }}>
                {Number(rec.emissions_kg_co2e).toLocaleString(undefined, { maximumFractionDigits: 1 })}
              </td>
              <td>
                <ScopeTag scope={rec.scope} />
              </td>
              <td>
                <StatusBadge status={rec.status} />
              </td>
              <td>
                {rec.is_suspicious && (
                  <span title="Flagged as suspicious" style={{ color: 'var(--color-warning)' }}>
                    <AlertTriangle size={16} />
                  </span>
                )}
              </td>
              <td onClick={(e) => e.stopPropagation()}>
                <div style={{ display: 'flex', gap: 'var(--space-1)' }}>
                  <button
                    className="btn btn-sm btn-success"
                    onClick={() => onApprove?.(rec.id)}
                    title="Approve"
                    disabled={rec.status === 'approved' || rec.status === 'locked'}
                  >
                    <Check size={14} />
                  </button>
                  <button
                    className="btn btn-sm btn-danger"
                    onClick={() => onReject?.(rec.id)}
                    title="Reject"
                    disabled={rec.status === 'approved' || rec.status === 'locked'}
                  >
                    <X size={14} />
                  </button>
                  <button
                    className="btn btn-sm btn-ghost"
                    onClick={() => onView?.(rec.id)}
                    title="View details"
                  >
                    <Eye size={14} />
                  </button>
                </div>
              </td>
            </tr>
          ))}

          {records.length === 0 && (
            <tr>
              <td colSpan={10} style={{ textAlign: 'center', padding: 'var(--space-10)', color: 'var(--text-tertiary)' }}>
                No records found
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
