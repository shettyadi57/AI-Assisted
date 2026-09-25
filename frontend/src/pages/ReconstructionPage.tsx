import React from 'react';
import { PhaseGateNotice } from '../components/common/PhaseGateNotice';

export const ReconstructionPage: React.FC = () => {
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <PhaseGateNotice
        pageName="Reconstruction & Candidate Traversal"
        targetPhase="Phase 4 — Candidate Reconstruction"
        phaseNumber={4}
        stageName="reconstruction"
        description="Traverses the scored candidate relationship graph to synthesize proposed file assemblies. Investigators inspect individual edges (signature match, offset continuity, structural validity, entropy) and explicitly accept or reject edges before finalization."
        apiEndpoint="/api/v1/reconstruction/candidates"
        apiMethod="POST"
        expectedCoreModule="core.reconstruction_engine.ReconstructionEngine & core.relationship_engine.RelationshipEngine"
      />
    </div>
  );
};
