import React from 'react';
import { PhaseGateNotice } from '../components/common/PhaseGateNotice';

export const ReportsPage: React.FC = () => {
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <PhaseGateNotice
        pageName="Forensic Reports & Provenance Export"
        targetPhase="Phase 7 & 8 — Provenance Export & Reporting"
        phaseNumber={7}
        stageName="export"
        description="Generates court-ready forensic audit dossiers with bit-level byte provenance mapping: every reconstructed output byte traces back to its source fragment ID, sector offset, edge confidence score, and human investigator approval record."
        apiEndpoint="/api/v1/export/provenance"
        apiMethod="POST"
        expectedCoreModule="core.reconstruction_engine.ReconstructionEngine"
      />
    </div>
  );
};
