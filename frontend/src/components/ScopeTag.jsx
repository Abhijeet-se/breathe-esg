/**
 * components/ScopeTag.jsx
 * ───────────────────────
 * Small tag displaying "Scope 1 / 2 / 3" with color-coded styling.
 *
 * Props:
 *  • scope — number or string: 1, 2, or 3
 */

import React from 'react';

export default function ScopeTag({ scope }) {
  const s = Number(scope);
  if (![1, 2, 3].includes(s)) return null;

  return (
    <span className={`scope-tag scope-tag-${s}`}>
      Scope {s}
    </span>
  );
}
