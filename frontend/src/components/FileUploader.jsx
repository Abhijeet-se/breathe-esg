/**
 * components/FileUploader.jsx
 * ───────────────────────────
 * Drag-and-drop file upload zone with progress bar.
 *
 * Props:
 *  • sourceType  — selected data source type
 *  • onUploadComplete — callback({ batch_id, summary })
 *
 * Accepts .csv, .xlsx, .xls files. Shows animated progress bar
 * during upload. Falls back to mock response when backend is
 * unavailable.
 */

import React, { useState, useRef, useCallback } from 'react';
import { UploadCloud, File, X } from 'lucide-react';
import { uploadAPI } from '../api/client';
import './FileUploader.css';

const ACCEPTED = ['.csv', '.xlsx', '.xls'];

function isAccepted(name) {
  return ACCEPTED.some((ext) => name.toLowerCase().endsWith(ext));
}

export default function FileUploader({ sourceType, onUploadComplete }) {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  /* ── Drag handlers ──────────────────────────────────────── */
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragging(false), []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped && isAccepted(dropped.name)) {
      setFile(dropped);
      setError('');
    } else {
      setError('Only .csv, .xlsx, and .xls files are accepted.');
    }
  }, []);

  /* ── File input change ──────────────────────────────────── */
  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected && isAccepted(selected.name)) {
      setFile(selected);
      setError('');
    } else if (selected) {
      setError('Only .csv, .xlsx, and .xls files are accepted.');
    }
  };

  /* ── Upload ─────────────────────────────────────────────── */
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);
    setError('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_type', sourceType);

    try {
      const res = await uploadAPI.uploadFile(formData, (e) => {
        const pct = Math.round((e.loaded * 100) / e.total);
        setProgress(pct);
      });
      onUploadComplete?.(res.data);
    } catch {
      // Mock response for demo purposes
      // Simulate progress
      for (let i = 0; i <= 100; i += 10) {
        await new Promise((r) => setTimeout(r, 80));
        setProgress(i);
      }
      onUploadComplete?.({
        batch_id: 'demo-batch-001',
        summary: {
          total: 142,
          parsed: 130,
          failed: 5,
          suspicious: 7,
        },
      });
    } finally {
      setUploading(false);
    }
  };

  /* ── Clear selection ────────────────────────────────────── */
  const handleClear = () => {
    setFile(null);
    setProgress(0);
    setError('');
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="file-uploader">
      {/* Drop zone */}
      <div
        className={`file-uploader__zone ${dragging ? 'file-uploader__zone--active' : ''} ${file ? 'file-uploader__zone--has-file' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !file && inputRef.current?.click()}
        role="button"
        tabIndex={0}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileChange}
          hidden
        />

        {file ? (
          <div className="file-uploader__selected">
            <File size={24} />
            <div>
              <p className="file-uploader__filename">{file.name}</p>
              <p className="file-uploader__filesize">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button className="btn-icon" onClick={(e) => { e.stopPropagation(); handleClear(); }}>
              <X size={16} />
            </button>
          </div>
        ) : (
          <>
            <UploadCloud size={40} className="file-uploader__icon" />
            <p className="file-uploader__label">
              Drag & drop CSV or Excel files
            </p>
            <p className="file-uploader__hint">
              or click to browse · .csv, .xlsx, .xls
            </p>
          </>
        )}
      </div>

      {/* Error */}
      {error && <p className="file-uploader__error">{error}</p>}

      {/* Progress bar */}
      {uploading && (
        <div className="file-uploader__progress">
          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
          </div>
          <span className="file-uploader__pct">{progress}%</span>
        </div>
      )}

      {/* Upload button */}
      {file && !uploading && (
        <button className="btn btn-primary btn-lg" onClick={handleUpload}>
          <UploadCloud size={18} /> Upload File
        </button>
      )}
    </div>
  );
}
