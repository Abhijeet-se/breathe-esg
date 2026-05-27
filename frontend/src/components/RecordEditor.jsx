/**
 * components/RecordEditor.jsx
 * ───────────────────────────
 * Inline edit form for a normalized ESG record.
 * Shows original values as muted text below each editable field.
 *
 * Props:
 *  • record     — the record object
 *  • onChange    — callback(field, value) for edits
 *  • onSave     — callback()
 *  • onCancel   — callback()
 *  • disabled   — boolean, disables all fields (e.g. when locked)
 */

import React from 'react';
import './RecordEditor.css';

export default function RecordEditor({ record, onChange, onSave, onCancel, disabled }) {
  if (!record) return null;

  const handleChange = (field) => (e) => onChange?.(field, e.target.value);

  return (
    <div className="record-editor">
      <div className="record-editor__grid">
        {/* Normalized Value */}
        <div className="input-group">
          <label className="input-label">Normalized Value</label>
          <input
            className="input-field"
            type="number"
            step="any"
            value={record.normalized_value ?? ''}
            onChange={handleChange('normalized_value')}
            disabled={disabled}
          />
          <span className="record-editor__original">
            Original: {record.original_value} {record.original_unit}
          </span>
        </div>

        {/* Normalized Unit */}
        <div className="input-group">
          <label className="input-label">Normalized Unit</label>
          <input
            className="input-field"
            type="text"
            value={record.normalized_unit ?? ''}
            onChange={handleChange('normalized_unit')}
            disabled={disabled}
          />
        </div>

        {/* Emissions */}
        <div className="input-group">
          <label className="input-label">Emissions (kg CO₂e)</label>
          <input
            className="input-field"
            type="number"
            step="any"
            value={record.emissions_kg_co2e ?? ''}
            onChange={handleChange('emissions_kg_co2e')}
            disabled={disabled}
          />
        </div>

        {/* Scope */}
        <div className="input-group">
          <label className="input-label">Scope</label>
          <select
            className="input-field"
            value={record.scope ?? ''}
            onChange={handleChange('scope')}
            disabled={disabled}
          >
            <option value="">Select…</option>
            <option value="1">Scope 1</option>
            <option value="2">Scope 2</option>
            <option value="3">Scope 3</option>
          </select>
        </div>

        {/* Category */}
        <div className="input-group" style={{ gridColumn: '1 / -1' }}>
          <label className="input-label">Category</label>
          <input
            className="input-field"
            type="text"
            value={record.category ?? ''}
            onChange={handleChange('category')}
            disabled={disabled}
            placeholder="e.g. stationary_combustion"
          />
        </div>
      </div>

      {/* Actions */}
      {!disabled && (
        <div className="record-editor__actions">
          <button className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={onSave}>
            Save Changes
          </button>
        </div>
      )}
    </div>
  );
}
