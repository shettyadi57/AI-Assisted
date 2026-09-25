import React from 'react';
import { useInvestigation } from '../context/InvestigationContext';
import { StatusBadge } from '../components/common/StatusBadge';
import { FORENSIC_STATUS_COLORS, ForensicStatusKey } from '../tokens';

export const OverviewPage: React.FC = () => {
  const { apiHealth, isApiOnline } = useInvestigation();

  const forensicStatuses: ForensicStatusKey[] = [
    'valid',
    'recovered',
    'missing',
    'corrupted',
    'duplicate',
    'uncertain',
  ];

  const pipelineStages = [
    { name: '1. Discovery & Ingest', phase: 'Phase 1', route: '/api/v1/discovery', status: 'SKELETON (501)' },
    { name: '2. Fragment Identification', phase: 'Phase 2', route: '/api/v1/analysis', status: 'SKELETON (501)' },
    { name: '3. Relationship Linking', phase: 'Phase 3', route: '/api/v1/linking', status: 'SKELETON (501)' },
    { name: '4. Candidate Reconstruction', phase: 'Phase 4', route: '/api/v1/reconstruction', status: 'SKELETON (501)' },
    { name: '5. Validation & Provenance', phase: 'Phase 6/7', route: '/api/v1/export', status: 'SKELETON (501)' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Hero Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
          <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 700 }}>
            Forensic Investigation Overview
          </h1>
          <span className="badge badge-phase">Phase 0 Scaffolding</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-base)', maxWidth: '800px' }}>
          Welcome to Reconstruct. This investigator workbench formulates file fragment reassembly
          as an explainable, multi-factor graph problem where human investigators review and accept/reject
          candidate edges prior to finalization.
        </p>
      </div>

      {/* System Status Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 'var(--space-4)' }}>
        <div className="forensic-card">
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
            Active Monorepo Phase
          </div>
          <div style={{ fontSize: 'var(--text-xl)', fontWeight: 700, color: '#38BDF8' }}>
            Phase 0: Skeleton
          </div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginTop: '4px' }}>
            All interfaces typed, no fake data
          </div>
        </div>

        <div className="forensic-card">
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
            FastAPI Backend Engine
          </div>
          <div style={{ fontSize: 'var(--text-xl)', fontWeight: 700, color: isApiOnline ? '#10B981' : '#EF4444' }}>
            {isApiOnline ? 'Online (/api/v1)' : 'Offline'}
          </div>
          <div className="font-mono" style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginTop: '4px' }}>
            {apiHealth?.status ? `v${apiHealth.version} • healthy` : 'Run uvicorn backend.main:app'}
          </div>
        </div>

        <div className="forensic-card">
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
            Database Storage
          </div>
          <div style={{ fontSize: 'var(--text-xl)', fontWeight: 700, color: '#F59E0B' }}>
            SQLite (7 Tables)
          </div>
          <div className="font-mono" style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginTop: '4px' }}>
            reconstruct.db • 001_initial_schema
          </div>
        </div>

        <div className="forensic-card">
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-2)' }}>
            Core Analysis Core
          </div>
          <div style={{ fontSize: 'var(--text-xl)', fontWeight: 700, color: '#A855F7' }}>
            Pure Python 3.13
          </div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Zero FastAPI imports in /core
          </div>
        </div>
      </div>

      {/* Forensic Status States Showcase */}
      <div className="forensic-card">
        <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
          Forensic Classification States (Design Tokens)
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)', marginBottom: 'var(--space-4)' }}>
          Per the master specification, states are never collapsed to a single generic status. Every fragment
          and candidate belongs to one of six rigorously distinguished states:
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-4)' }}>
          {forensicStatuses.map((st) => (
            <div
              key={st}
              style={{
                padding: 'var(--space-3)',
                background: 'var(--bg-page)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--space-2)',
              }}
            >
              <StatusBadge status={st} />
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-secondary)' }}>
                {FORENSIC_STATUS_COLORS[st].description}
              </span>
              <span className="font-mono" style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                {FORENSIC_STATUS_COLORS[st].color}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Pipeline Stage Skeletons Table */}
      <div className="forensic-card">
        <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
          Pipeline Stage Skeletons
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)', marginBottom: 'var(--space-4)' }}>
          All pipeline endpoints are registered and return HTTP 501 with target phase payload until implemented:
        </p>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: 'var(--text-sm)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '8px 12px' }}>Stage Name</th>
                <th style={{ padding: '8px 12px' }}>Target Phase</th>
                <th style={{ padding: '8px 12px' }}>API Route Prefix</th>
                <th style={{ padding: '8px 12px' }}>Response Status</th>
              </tr>
            </thead>
            <tbody>
              {pipelineStages.map((ps) => (
                <tr key={ps.route} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '10px 12px', fontWeight: 500 }}>{ps.name}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span className="badge badge-phase">{ps.phase}</span>
                  </td>
                  <td className="font-mono" style={{ padding: '10px 12px', color: '#F59E0B' }}>{ps.route}</td>
                  <td className="font-mono" style={{ padding: '10px 12px', color: '#EF4444' }}>{ps.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
