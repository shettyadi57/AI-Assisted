import React from 'react';
import { PhaseGateNotice } from '../components/common/PhaseGateNotice';

export const ValidationPage: React.FC = () => {
  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <PhaseGateNotice
        pageName="Structural Format Validation"
        targetPhase="Phase 6 — Structural Validation"
        phaseNumber={6}
        stageName="validation"
        description="Performs format-specific deep AST and marker validation on reconstructed files (e.g., verifying JPEG Huffman streams and EOI markers, PDF xref tables and trailer dictionaries, PNG chunk CRC32 checksums, ZIP local file headers)."
        apiEndpoint="/api/v1/export/provenance"
        apiMethod="POST"
        expectedCoreModule="core.validators (PDFValidator, JPEGValidator, PNGValidator, ZIPValidator)"
      />
    </div>
  );
};
