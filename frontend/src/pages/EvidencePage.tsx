import React from 'react';
import { PhaseGateNotice } from '../components/common/PhaseGateNotice';

export const EvidencePage: React.FC = () => {
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <PhaseGateNotice
        pageName="Evidence Ingestion & Registry"
        targetPhase="Phase 1 — Evidence Ingest"
        phaseNumber={1}
        stageName="discovery"
        description="Ingest raw disk images, block devices, and slack dump files. On ingest, all evidence files are immediately hashed with SHA-256 for cryptographic chain of custody and treated as strictly read-only."
        apiEndpoint="/api/v1/discovery/ingest"
        apiMethod="POST"
        expectedCoreModule="core.integrity_analyzer.IntegrityAnalyzer"
      />
    </div>
  );
};
