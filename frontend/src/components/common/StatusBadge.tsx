import React from 'react';
import { FORENSIC_STATUS_COLORS, ForensicStatusKey } from '../../tokens';

interface StatusBadgeProps {
  status: ForensicStatusKey;
  label?: string;
  showDot?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, showDot = true }) => {
  const token = FORENSIC_STATUS_COLORS[status] || FORENSIC_STATUS_COLORS.uncertain;
  const displayLabel = label || token.label;

  return (
    <span
      className="badge"
      style={{
        color: token.color,
        backgroundColor: token.bg,
        border: `1px solid ${token.border}`,
      }}
    >
      {showDot && (
        <span
          style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: token.color,
            display: 'inline-block',
          }}
        />
      )}
      {displayLabel}
    </span>
  );
};
