/**
 * components/ConfirmModal.jsx
 * ───────────────────────────
 * Reusable confirmation modal with dark overlay, glass card,
 * optional comment textarea, and keyboard-dismiss (Escape).
 *
 * Props:
 *  • open         — boolean
 *  • title        — heading text
 *  • message      — body text
 *  • confirmLabel — text for confirm button (default "Confirm")
 *  • confirmVariant — button class suffix (e.g. 'danger', 'success')
 *  • showComment  — boolean, if true shows a textarea for comments
 *  • onConfirm    — callback(comment: string)
 *  • onCancel     — callback
 */

import React, { useState, useEffect, useCallback } from 'react';

export default function ConfirmModal({
  open,
  title = 'Confirm Action',
  message = 'Are you sure you want to proceed?',
  confirmLabel = 'Confirm',
  confirmVariant = 'primary',
  showComment = false,
  onConfirm,
  onCancel,
}) {
  const [comment, setComment] = useState('');

  /* Reset comment when modal opens */
  useEffect(() => {
    if (open) setComment('');
  }, [open]);

  /* Close on Escape key */
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Escape' && open) onCancel?.();
    },
    [open, onCancel]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h3 className="modal-title">{title}</h3>
        <p className="modal-message">{message}</p>

        {showComment && (
          <div className="input-group" style={{ marginBottom: 'var(--space-6)' }}>
            <label className="input-label" htmlFor="modal-comment">
              Comment (optional)
            </label>
            <textarea
              id="modal-comment"
              className="input-field"
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Add a note…"
            />
          </div>
        )}

        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
          <button
            className={`btn btn-${confirmVariant}`}
            onClick={() => onConfirm?.(comment)}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
