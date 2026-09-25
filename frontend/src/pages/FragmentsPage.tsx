import React from 'react';
import { PhaseGateNotice } from '../components/common/PhaseGateNotice';

export const FragmentsPage: React.FC = () => {
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <PhaseGateNotice
        pageName="Fragment Carving & Identification"
        targetPhase="Phase 2 — Fragment Identification"
        phaseNumber={2}
        stageName="analysis"
        description="Scans ingested raw evidence media for format signatures (magic headers, footer trailers) and analyzes Shannon entropy fluctuations across sector boundaries to carve isolated, contiguous fragments."
        apiEndpoint="/api/v1/analysis/fragments"
        apiMethod="POST"
        expectedCoreModule="core.fragment_analyzer.FragmentAnalyzer & core.signature_registry.SignatureRegistry"
      />
    </div>
  );
};
