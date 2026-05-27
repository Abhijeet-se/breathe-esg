/**
 * components/StatusBadge.jsx
 * ──────────────────────────
 * Pill-shaped badge that maps a record status to the appropriate
 * color and optional icon from the design system.
 *
 * Props:
 *  • status — one of: uploaded, parsed, failed, suspicious, approved, locked
 */

import React from 'react';
import { Lock } from 'lucide-react';

const LABEL_MAP = {
  uploaded: 'Uploaded',
  parsed: 'Parsed',
  failed: 'Failed',
  suspicious: 'Suspicious',
  approved: 'Approved',
  locked: 'Locked',
};

export default function StatusBadge({ status }) {
  const label = LABEL_MAP[status] || status;
  const className = `badge badge-${status}`;

  return (
    <span className={className}>
      {status === 'locked' && <Lock size={11} />}
      {label}
    </span>
  );
}
