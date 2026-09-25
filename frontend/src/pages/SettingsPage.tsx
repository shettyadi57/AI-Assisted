import React from 'react';
import { useInvestigation } from '../context/InvestigationContext';

export const SettingsPage: React.FC = () => {
  const { apiHealth, isApiOnline } = useInvestigation();

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      <div>
        <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: 600 }}>Forensic Workbench Configuration</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)', marginTop: '4px' }}>
          Global environmental parameters, cryptographic policies, and database bindings.
        </p>
      </div>

      <div className="forensic-card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600 }}>API & Engine Binding</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 'var(--space-3)', alignItems: 'center' }}>
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>Backend Target:</span>
          <span className="font-mono" style={{ fontSize: 'var(--text-sm)', color: '#38BDF8' }}>
            http://localhost:8000/api/v1 (Vite Proxy: /api)
          </span>

          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>API Status:</span>
          <span style={{ fontSize: 'var(--text-sm)', color: isApiOnline ? '#10B981' : '#EF4444', fontWeight: 600 }}>
            {isApiOnline ? `HEALTHY (Version ${apiHealth?.version})` : 'OFFLINE'}
          </span>

          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>Primary Hash Algorithm:</span>
          <span className="font-mono" style={{ fontSize: 'var(--text-sm)' }}>
            SHA-256 (Mandatory per Section 20)
          </span>

          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>Database File:</span>
          <span className="font-mono" style={{ fontSize: 'var(--text-sm)' }}>
            reconstruct.db (SQLite v3)
          </span>
        </div>
      </div>

      <div className="forensic-card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600 }}>Scoring &amp; Classification Subsystems (Phase 9)</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 'var(--space-3)', alignItems: 'center' }}>
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>Relationship Scoring:</span>
          <div>
            <span style={{ fontSize: 'var(--text-sm)', color: '#10B981', fontWeight: 600 }}>
              Deterministic Heuristic Engine (Active)
            </span>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>
              Multi-signal 5-factor scoring (signature, offset continuity, structure, entropy, contradictions).
            </div>
          </div>

          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>ML-Assisted Scoring:</span>
          <div>
            <span className="font-mono" style={{ fontSize: 'var(--text-xs)', color: '#F59E0B', fontWeight: 600 }}>
              Interface Ready (No model trained yet)
            </span>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>
              Phase 9 ML extension point seam implemented. ONNX scoring interface ready for future model weights.
            </div>
          </div>

          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>Fragment Classifier:</span>
          <div>
            <span style={{ fontSize: 'var(--text-sm)', color: '#38BDF8', fontWeight: 600 }}>
              Signature Registry (Active)
            </span>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: '2px' }}>
              Data-driven magic byte, trailer marker, and chunk CRC verification for PDF, JPEG, PNG, ZIP, etc.
            </div>
          </div>
        </div>
      </div>

      <div className="forensic-card" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600 }}>Legal &amp; Integrity Notice</h3>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)' }}>
          This workbench is designed strictly as an investigator-in-the-loop forensic reconstruction prototype.
          All candidate assemblies and provenance traces are derived deterministically from multi-signal byte analysis
          and validated via cryptographic SHA-256 signatures.
        </p>
        <div
          className="font-mono"
          style={{
            fontSize: 'var(--text-xs)',
            padding: 'var(--space-3)',
            background: 'var(--bg-page)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            color: '#F87171',
          }}
        >
          DISCLAIMER: {apiHealth?.disclaimer || 'Portfolio / prototype tool. Not legally admissible.'}
        </div>
      </div>
    </div>
  );
};
