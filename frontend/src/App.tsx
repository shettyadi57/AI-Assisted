import React from 'react';
import { InvestigationProvider, useInvestigation } from './context/InvestigationContext';
import { AppShell } from './components/layout/AppShell';
import { OverviewPage } from './pages/OverviewPage';
import { EvidencePage } from './pages/EvidencePage';
import { FragmentsPage } from './pages/FragmentsPage';
import { ReconstructionPage } from './pages/ReconstructionPage';
import { ValidationPage } from './pages/ValidationPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

const PageRouter: React.FC = () => {
  const { currentPage } = useInvestigation();

  switch (currentPage) {
    case 'overview':
      return <OverviewPage />;
    case 'evidence':
      return <EvidencePage />;
    case 'fragments':
      return <FragmentsPage />;
    case 'reconstruction':
      return <ReconstructionPage />;
    case 'validation':
      return <ValidationPage />;
    case 'reports':
      return <ReportsPage />;
    case 'settings':
      return <SettingsPage />;
    default:
      return <OverviewPage />;
  }
};

export const App: React.FC = () => {
  return (
    <InvestigationProvider>
      <AppShell>
        <PageRouter />
      </AppShell>
    </InvestigationProvider>
  );
};

export default App;
