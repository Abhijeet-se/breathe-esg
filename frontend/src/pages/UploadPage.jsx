/**
 * pages/UploadPage.jsx
 * ────────────────────
 * Data upload page with:
 *  1. Source type selector (SAP Fuel, Electricity, Travel) as 3 styled cards
 *  2. FileUploader drag-and-drop zone
 *  3. Post-upload UploadSummary
 */

import React, { useState } from 'react';
import { Fuel, Zap, Plane } from 'lucide-react';
import FileUploader from '../components/FileUploader';
import UploadSummary from '../components/UploadSummary';
import './UploadPage.css';

const SOURCE_TYPES = [
  {
    id: 'sap_fuel',
    label: 'SAP Fuel Log',
    description: 'Fleet & vehicle fuel consumption data',
    icon: Fuel,
    color: '#f97316',
  },
  {
    id: 'electricity',
    label: 'Electricity',
    description: 'Grid electricity consumption readings',
    icon: Zap,
    color: '#3b82f6',
  },
  {
    id: 'travel',
    label: 'Business Travel',
    description: 'Flights, rail, and hotel stays',
    icon: Plane,
    color: '#8b5cf6',
  },
];

export default function UploadPage() {
  const [sourceType, setSourceType] = useState('sap_fuel');
  const [uploadResult, setUploadResult] = useState(null);

  const handleUploadComplete = (data) => {
    setUploadResult(data);
  };

  return (
    <div className="upload-page">
      <div className="page-header animate-fade-in-up">
        <h1 className="page-title">Upload Data</h1>
        <p className="page-subtitle">
          Select a data source type, then upload your CSV or Excel file
        </p>
      </div>

      {/* ── Source Type Selector ─────────────────────────── */}
      <div className="upload-page__sources animate-fade-in-up delay-1" style={{ opacity: 0 }}>
        {SOURCE_TYPES.map((src) => (
          <button
            key={src.id}
            className={`upload-page__source glass-card ${sourceType === src.id ? 'upload-page__source--active' : ''}`}
            onClick={() => { setSourceType(src.id); setUploadResult(null); }}
            style={{ '--accent': src.color }}
          >
            <div className="upload-page__source-icon" style={{ color: src.color }}>
              <src.icon size={28} />
            </div>
            <div>
              <p className="upload-page__source-label">{src.label}</p>
              <p className="upload-page__source-desc">{src.description}</p>
            </div>
          </button>
        ))}
      </div>

      {/* ── File Uploader ───────────────────────────────── */}
      <div className="animate-fade-in-up delay-2" style={{ opacity: 0 }}>
        <FileUploader
          sourceType={sourceType}
          onUploadComplete={handleUploadComplete}
        />
      </div>

      {/* ── Upload Summary ──────────────────────────────── */}
      {uploadResult && (
        <UploadSummary
          summary={uploadResult.summary}
          batchId={uploadResult.batch_id}
        />
      )}
    </div>
  );
}
