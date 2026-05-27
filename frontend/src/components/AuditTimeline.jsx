/**
 * components/AuditTimeline.jsx
 * ────────────────────────────
 * Vertical timeline displaying audit entries for a record.
 * Each node has an icon based on action type, timestamp,
 * user, and a diff display.
 *
 * Props:
 *  • entries — array of audit log objects
 *              { id, action, field, old_value, new_value, changed_by, timestamp }
 *              Falls back to mock data.
 */

import React from 'react';
import { Plus, Pencil, Check, X, Lock, ArrowRight } from 'lucide-react';
import './AuditTimeline.css';

/* Icon and color mapping for action types */
const ACTION_CONFIG = {
  create:  { icon: Plus,   color: '#3b82f6', label: 'Created' },
  edit:    { icon: Pencil, color: '#f59e0b', label: 'Edited' },
  approve: { icon: Check,  color: '#10b981', label: 'Approved' },
  reject:  { icon: X,      color: '#ef4444', label: 'Rejected' },
  lock:    { icon: Lock,   color: '#8b5cf6', label: 'Locked' },
};

const MOCK_ENTRIES = [
  { id: 1, action: 'create', field: null, old_value: null, new_value: null, changed_by: 'system', timestamp: '2024-03-15T10:30:00Z' },
  { id: 2, action: 'edit', field: 'emissions_kg_co2e', old_value: '120.5', new_value: '135.2', changed_by: 'jane.doe@acme.com', timestamp: '2024-03-15T11:15:00Z' },
  { id: 3, action: 'edit', field: 'scope', old_value: '2', new_value: '1', changed_by: 'jane.doe@acme.com', timestamp: '2024-03-15T11:16:00Z' },
  { id: 4, action: 'approve', field: null, old_value: 'parsed', new_value: 'approved', changed_by: 'admin@acme.com', timestamp: '2024-03-16T09:00:00Z' },
  { id: 5, action: 'lock', field: null, old_value: null, new_value: null, changed_by: 'admin@acme.com', timestamp: '2024-03-16T09:05:00Z' },
];

function formatTime(ts) {
  const d = new Date(ts);
  return d.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function AuditTimeline({ entries }) {
  const items = entries?.length ? entries : MOCK_ENTRIES;

  return (
    <div className="audit-timeline">
      <h3 className="audit-timeline__title">Audit History</h3>
      <div className="audit-timeline__list">
        {items.map((entry, idx) => {
          const config = ACTION_CONFIG[entry.action] || ACTION_CONFIG.edit;
          const Icon = config.icon;

          return (
            <div key={entry.id} className="audit-timeline__item">
              {/* Vertical connector line */}
              {idx < items.length - 1 && <div className="audit-timeline__line" />}

              {/* Node icon */}
              <div
                className="audit-timeline__node"
                style={{ background: config.color }}
              >
                <Icon size={14} color="white" />
              </div>

              {/* Content */}
              <div className="audit-timeline__content">
                <div className="audit-timeline__header">
                  <span className="audit-timeline__action" style={{ color: config.color }}>
                    {config.label}
                  </span>
                  <span className="audit-timeline__time">{formatTime(entry.timestamp)}</span>
                </div>

                <span className="audit-timeline__user">{entry.changed_by}</span>

                {/* Diff */}
                {entry.field && (
                  <div className="audit-timeline__diff">
                    <span className="audit-timeline__field">{entry.field}:</span>
                    <span className="audit-timeline__old">{entry.old_value || '—'}</span>
                    <ArrowRight size={12} />
                    <span className="audit-timeline__new">{entry.new_value || '—'}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
