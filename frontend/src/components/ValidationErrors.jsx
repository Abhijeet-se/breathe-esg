/**
 * components/ValidationErrors.jsx
 * ────────────────────────────────
 * Renders a list of validation errors / warnings for a record.
 *
 * Props:
 *  • errors — array of { field, rule, message, severity }
 *             severity is 'error' or 'warning'
 */

import React from 'react';
import { AlertCircle, AlertTriangle } from 'lucide-react';
import './ValidationErrors.css';

export default function ValidationErrors({ errors = [] }) {
  if (!errors.length) return null;

  return (
    <div className="validation-errors">
      <h4 className="validation-errors__heading">Validation Issues</h4>
      <ul className="validation-errors__list">
        {errors.map((err, i) => (
          <li
            key={i}
            className={`validation-errors__item validation-errors__item--${err.severity || 'error'}`}
          >
            <span className="validation-errors__icon">
              {err.severity === 'warning' ? (
                <AlertTriangle size={15} />
              ) : (
                <AlertCircle size={15} />
              )}
            </span>
            <div className="validation-errors__body">
              <span className="validation-errors__field">{err.field}</span>
              <span className="validation-errors__rule">{err.rule}</span>
              <span className="validation-errors__msg">{err.message}</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
