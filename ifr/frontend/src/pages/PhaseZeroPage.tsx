/**
 * Phase 0 landing page: system map + signature registry preview.
 * Shows what IS available and what is coming in which phase.
 * No fake data, no fake progress bars.
 */

import React, { useEffect, useState } from 'react';
import { HealthResponse, FormatSignature, EvidenceStatus } from '@/types';

// ── Status chip helper ────────────────────────────────────────────────────
const StatusChip: React.FC<{ status: EvidenceStatus }> = ({ status }) => (
  <span className={`status-chip ${status.toLowerCase()}`}>{status}</span>
);

// ── Signal bar: visualizes a 0.0–1.0 signal or shows "not computed" ──────
const SignalBar: React.FC<{ label: string; value: number | null; comingPhase: number }> = ({
  label, value, comingPhase
}) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
    <span style={{ width: 180, fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', flexShrink: 0 }}>
      {label}
    </span>
    {value !== null ? (
      <>
        <div style={{
          flex: 1, height: 4, background: 'var(--bg-raised)', borderRadius: 2, overflow: 'hidden'
        }}>
          <div style={{
            width: `${value * 100}%`, height: '100%',
            background: value >= 0.85 ? 'var(--status-confirmed)' :
                        value >= 0.55 ? 'var(--status-inferred)' :
                        value >= 0.25 ? 'var(--status-uncertain)' : 'var(--status-corrupted)',
            borderRadius: 2,
          }} />
        </div>
        <span className="mono" style={{ width: 38, fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', textAlign: 'right' }}>
          {(value * 100).toFixed(0)}%
        </span>
      </>
    ) : (
      <span className="phase-badge">Phase {comingPhase}</span>
    )}
  </div>
);

// ── Confidence model explainer ────────────────────────────────────────────
const ConfidenceModelCard: React.FC = () => (
  <div style={{
    background: 'var(--bg-surface)',
    border: '1px solid var(--border-subtle)',
    borderRadius: 'var(--radius-md)',
    padding: 'var(--space-4)',
  }}>
    <div style={{ marginBottom: 'var(--space-3)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600 }}>Confidence Evidence Model</h3>
      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
        Rule 2 — never a bare percentage
      </span>
    </div>
    <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginBottom: 'var(--space-3)', lineHeight: 1.6 }}>
      Every fragment-to-fragment relationship is scored on five independent signals.
      The composite is derived from them — never stored or shown without its backing evidence.
    </p>
    <SignalBar label="Header signature match"   value={null} comingPhase={3} />
    <SignalBar label="Offset continuity"        value={null} comingPhase={3} />
    <SignalBar label="Structural validity"      value={null} comingPhase={6} />
    <SignalBar label="Entropy profile match"    value={null} comingPhase={3} />
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
      <span style={{ width: 180, fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', flexShrink: 0 }}>
        Contradiction count
      </span>
      <span className="phase-badge">Phase 3</span>
    </div>
    <div style={{
      marginTop: 'var(--space-3)', paddingTop: 'var(--space-2)',
      borderTop: '1px solid var(--border-subtle)',
      display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap',
    }}>
      {(['CONFIRMED','INFERRED','UNCERTAIN','MISSING','CORRUPTED','DUPLICATE'] as EvidenceStatus[]).map(s => (
        <StatusChip key={s} status={s} />
      ))}
    </div>
    <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginTop: 'var(--space-2)' }}>
      Status is always one of the six above — never a single green checkmark.
    </p>
  </div>
);

// ── Phase roadmap table ───────────────────────────────────────────────────
const PHASES: { n: number; label: string; status: 'done' | 'active' | 'upcoming' }[] = [
  { n: 0, label: 'Scaffolding — interfaces, schema, project structure', status: 'active' },
  { n: 1, label: 'Evidence ingest — upload, SHA-256 on ingest, read-only storage', status: 'upcoming' },
  { n: 2, label: 'Fragment identification — boundary detection, signature scan', status: 'upcoming' },
  { n: 3, label: 'Relationship scoring — 5-signal confidence model, edge graph', status: 'upcoming' },
  { n: 4, label: 'Reconstruction candidates — graph traversal, candidate assembly', status: 'upcoming' },
  { n: 5, label: 'Investigator workflow — accept/reject, append-only audit log', status: 'upcoming' },
  { n: 6, label: 'Structural validation — format-aware fragment and assembly checks', status: 'upcoming' },
  { n: 7, label: 'Provenance export — byte → fragment → edge → decision chain', status: 'upcoming' },
  { n: 8, label: 'Reporting — summary reports, audit log export', status: 'upcoming' },
  { n: 9, label: 'ML integration — FragmentClassifier / RelationshipScorer', status: 'upcoming' },
  { n: 10, label: 'Hardening — performance, error handling, packaging', status: 'upcoming' },
];

const PhaseTable: React.FC = () => (
  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-sm)' }}>
    <thead>
      <tr style={{ borderBottom: '1px solid var(--border-default)' }}>
        <th style={{ textAlign: 'left', padding: '6px 8px', color: 'var(--text-muted)', fontWeight: 500, width: 60 }}>Phase</th>
        <th style={{ textAlign: 'left', padding: '6px 8px', color: 'var(--text-muted)', fontWeight: 500 }}>Description</th>
        <th style={{ textAlign: 'right', padding: '6px 8px', color: 'var(--text-muted)', fontWeight: 500, width: 100 }}>Status</th>
      </tr>
    </thead>
    <tbody>
      {PHASES.map(p => (
        <tr key={p.n} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
          <td className="mono" style={{ padding: '6px 8px', color: 'var(--text-secondary)' }}>{p.n}</td>
          <td style={{ padding: '6px 8px', color: p.status === 'active' ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
            {p.label}
          </td>
          <td style={{ padding: '6px 8px', textAlign: 'right' }}>
            {p.status === 'active' && <span className="status-chip inferred">ACTIVE</span>}
            {p.status === 'done' && <span className="status-chip confirmed">DONE</span>}
            {p.status === 'upcoming' && <span className="phase-badge">P{p.n}</span>}
          </td>
        </tr>
      ))}
    </tbody>
  </table>
);

// ── Signature registry preview ────────────────────────────────────────────
const SignatureTable: React.FC<{ signatures: FormatSignature[] }> = ({ signatures }) => (
  <div style={{ overflowX: 'auto' }}>
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-xs)' }}>
      <thead>
        <tr style={{ borderBottom: '1px solid var(--border-default)' }}>
          {['Format ID', 'Display Name', 'Header Magic', 'Offset', 'Footer Magic', 'MIME Type'].map(h => (
            <th key={h} style={{ textAlign: 'left', padding: '5px 8px', color: 'var(--text-muted)', fontWeight: 500, whiteSpace: 'nowrap' }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {signatures.map(sig => (
          <tr key={sig.format_id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            <td className="mono" style={{ padding: '5px 8px', color: 'var(--accent)' }}>{sig.format_id}</td>
            <td style={{ padding: '5px 8px', color: 'var(--text-primary)' }}>{sig.display_name}</td>
            <td className="mono" style={{ padding: '5px 8px', color: 'var(--status-inferred)', whiteSpace: 'nowrap' }}>{sig.header_magic_hex}</td>
            <td className="mono" style={{ padding: '5px 8px', color: 'var(--text-secondary)' }}>{sig.header_offset}</td>
            <td className="mono" style={{ padding: '5px 8px', color: 'var(--text-muted)' }}>{sig.footer_magic_hex ?? '—'}</td>
            <td style={{ padding: '5px 8px', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{sig.mime_type}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

// ── Main page ─────────────────────────────────────────────────────────────
const PhaseZeroPage: React.FC<{ health: HealthResponse | null; healthError: string | null }> = ({
  health, healthError,
}) => {
  const [signatures, setSignatures] = useState<FormatSignature[]>([]);
  const [sigsLoading, setSigsLoading] = useState(true);
  const [sigsError, setSigsError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/signatures')
      .then(r => r.json())
      .then(d => { setSignatures(d.signatures); setSigsLoading(false); })
      .catch(e => { setSigsError(String(e)); setSigsLoading(false); });
  }, []);

  return (
    <div style={{ maxWidth: 960, display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

      {/* Header */}
      <div>
        <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 600, marginBottom: 6 }}>
          Phase 0 — Scaffolding
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)', lineHeight: 1.6, maxWidth: 680 }}>
          Project structure, database schema, analysis module interfaces, and
          design system established. No analysis is performed yet — all analysis
          features are gated behind their respective phases.
        </p>
      </div>

      {/* Backend health */}
      <section>
        <h2 style={{ fontSize: 'var(--text-md)', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
          Backend Connection
        </h2>
        {healthError ? (
          <div style={{
            padding: 'var(--space-3)', background: 'var(--status-corrupted-bg)',
            border: '1px solid rgba(239,68,68,0.25)', borderRadius: 'var(--radius)',
            fontSize: 'var(--text-sm)', color: 'var(--status-corrupted)',
          }}>
            <strong>Connection failed:</strong> {healthError}
            <br />
            <span style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-xs)' }}>
              Start the backend: <code className="mono">cd ifr/backend && uvicorn main:app --reload</code>
            </span>
          </div>
        ) : health ? (
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-3)',
          }}>
            {[
              { label: 'API Status',    value: health.status.toUpperCase(), mono: false },
              { label: 'DB Connected',  value: health.db_connected ? 'YES' : 'NO', mono: false },
              { label: 'Current Phase', value: String(health.phase.current_phase), mono: true },
            ].map(({ label, value, mono }) => (
              <div key={label} style={{
                background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius)', padding: 'var(--space-3)',
              }}>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
                <div className={mono ? 'mono' : ''} style={{ fontSize: 'var(--text-lg)', fontWeight: 600 }}>{value}</div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>Connecting…</p>
        )}
      </section>

      {/* Confidence model */}
      <section>
        <h2 style={{ fontSize: 'var(--text-md)', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
          Confidence Evidence Model
        </h2>
        <ConfidenceModelCard />
      </section>

      {/* Phase roadmap */}
      <section>
        <h2 style={{ fontSize: 'var(--text-md)', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
          Phase Roadmap
        </h2>
        <div style={{
          background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)', overflow: 'hidden',
        }}>
          <PhaseTable />
        </div>
      </section>

      {/* Signature registry */}
      <section>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
          <h2 style={{ fontSize: 'var(--text-md)', fontWeight: 600 }}>
            Signature Registry
          </h2>
          {!sigsLoading && !sigsError && (
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
              {signatures.length} formats registered
            </span>
          )}
        </div>
        <div style={{
          background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)', overflow: 'hidden',
        }}>
          {sigsLoading && (
            <p style={{ padding: 'var(--space-4)', color: 'var(--text-muted)', fontSize: 'var(--text-sm)' }}>Loading…</p>
          )}
          {sigsError && (
            <p style={{ padding: 'var(--space-4)', color: 'var(--status-corrupted)', fontSize: 'var(--text-sm)' }}>
              Failed to load signatures: {sigsError}
            </p>
          )}
          {!sigsLoading && !sigsError && <SignatureTable signatures={signatures} />}
        </div>
      </section>
    </div>
  );
};

export default PhaseZeroPage;
