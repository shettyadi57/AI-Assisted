import React, { useState } from 'react';
import { useInvestigation } from '../../context/InvestigationContext';

interface PhaseGateNoticeProps {
  pageName: string;
  targetPhase: string;
  phaseNumber: number;
  stageName: string;
  description: string;
  apiEndpoint: string;
  apiMethod?: string;
  expectedCoreModule: string;
}

export const PhaseGateNotice: React.FC<PhaseGateNoticeProps> = ({
  pageName,
  targetPhase,
  phaseNumber,
  stageName,
  description,
  apiEndpoint,
  apiMethod = 'POST',
  expectedCoreModule,
}) => {
  const { testPhaseEndpoint, lastEndpointTest } = useInvestigation();
  const [testing, setTesting] = useState(false);
  const [activeResult, setActiveResult] = useState<any>(null);

  const handleTest = async () => {
    setTesting(true);
    const res = await testPhaseEndpoint(apiEndpoint, apiMethod);
    setActiveResult(res);
    setTesting(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Top Banner */}
      <div
        className="forensic-card"
        style={{
          borderLeft: '4px solid #38BDF8',
          background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.05) 0%, rgba(18, 24, 36, 1) 100%)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 'var(--space-4)' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
              <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: 600, color: 'var(--text-primary)' }}>
                {pageName}
              </h2>
              <span className="badge badge-phase">
                Scheduled for {targetPhase}
              </span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-base)', maxWidth: '640px' }}>
              {description}
            </p>
          </div>

          <button
            className="btn-primary"
            onClick={handleTest}
            disabled={testing}
            id={`btn-test-${stageName}`}
          >
            {testing ? 'Probing...' : `Verify HTTP 501 Skeleton (${apiMethod} ${apiEndpoint})`}
          </button>
        </div>
      </div>

      {/* Grid of Interface Specifications */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--space-6)' }}>
        <div className="forensic-card">
          <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-3)' }}>
            Core Analysis Module
          </div>
          <div className="font-mono" style={{ fontSize: 'var(--text-sm)', color: '#38BDF8', padding: 'var(--space-3)', background: 'var(--bg-page)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            {expectedCoreModule}
          </div>
          <p style={{ marginTop: 'var(--space-3)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
            Pure Python typed interface raising <code className="font-mono">NotImplementedError</code> until Phase {phaseNumber}.
          </p>
        </div>

        <div className="forensic-card">
          <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 'var(--space-3)' }}>
            FastAPI Pipeline Route
          </div>
          <div className="font-mono" style={{ fontSize: 'var(--text-sm)', color: '#F59E0B', padding: 'var(--space-3)', background: 'var(--bg-page)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            {apiMethod} {apiEndpoint}
          </div>
          <p style={{ marginTop: 'var(--space-3)', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
            Currently returns status <code className="font-mono">501 Not Implemented</code> with target phase payload.
          </p>
        </div>
      </div>

      {/* Live Probe Result Box */}
      {activeResult && (
        <div
          className="forensic-card"
          style={{
            borderLeft: activeResult.statusCode === 501 ? '4px solid #10B981' : '4px solid #EF4444',
            background: 'var(--bg-surface)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
            <span style={{ fontSize: 'var(--text-xs)', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-secondary)' }}>
              Live Endpoint Verification Result
            </span>
            <span className="font-mono" style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
              {activeResult.timestamp}
            </span>
          </div>

          <pre
            className="font-mono"
            style={{
              padding: 'var(--space-4)',
              background: 'var(--bg-page)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              fontSize: 'var(--text-sm)',
              color: '#38BDF8',
              overflowX: 'auto',
            }}
          >
            {JSON.stringify(activeResult, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
