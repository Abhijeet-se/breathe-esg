/**
 * components/UploadSummary.jsx
 * ────────────────────────────
 * Post-upload summary card showing parsed/failed/suspicious counts
 * with a mini bar visualization.
 *
 * Props:
 *  • summary — { total, parsed, failed, suspicious }
 *  • batchId — string
 */

import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, FileSpreadsheet } from 'lucide-react';
import './UploadSummary.css';

export default function UploadSummary({ summary, batchId }) {
  if (!summary) return null;

  const { total, parsed, failed, suspicious } = summary;

  const items = [
    { label: 'Total Rows', value: total, icon: FileSpreadsheet, color: '#3b82f6' },
    { label: 'Parsed', value: parsed, icon: CheckCircle2, color: '#10b981' },
    { label: 'Failed', value: failed, icon: XCircle, color: '#ef4444' },
    { label: 'Suspicious', value: suspicious, icon: AlertTriangle, color: '#f59e0b' },
  ];

  return (
    <div className="upload-summary glass-card animate-fade-in-up">
      <div className="upload-summary__header">
        <h3 className="upload-summary__title">Upload Complete</h3>
        {batchId && (
          <span className="upload-summary__batch">
            Batch: {batchId.slice(0, 8)}…
          </span>
        )}
      </div>

      <div className="upload-summary__grid">
        {items.map((item) => (
          <div key={item.label} className="upload-summary__item" style={{ '--accent': item.color }}>
            <item.icon size={20} style={{ color: item.color }} />
            <span className="upload-summary__value">{item.value}</span>
            <span className="upload-summary__label">{item.label}</span>
          </div>
        ))}
      </div>

      {/* Visual bar */}
      {total > 0 && (
        <div className="upload-summary__bar">
          <div
            className="upload-summary__segment"
            style={{ width: `${(parsed / total) * 100}%`, background: '#10b981' }}
            title={`Parsed: ${parsed}`}
          />
          <div
            className="upload-summary__segment"
            style={{ width: `${(suspicious / total) * 100}%`, background: '#f59e0b' }}
            title={`Suspicious: ${suspicious}`}
          />
          <div
            className="upload-summary__segment"
            style={{ width: `${(failed / total) * 100}%`, background: '#ef4444' }}
            title={`Failed: ${failed}`}
          />
        </div>
      )}
    </div>
  );
}
