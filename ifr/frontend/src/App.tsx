import React, { useEffect, useState } from 'react';
import AppShell from '@/components/layout/AppShell';
import PhaseZeroPage from '@/pages/PhaseZeroPage';
import { HealthResponse } from '@/types';

const App: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/health')
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(d => setHealth(d as HealthResponse))
      .catch(e => setHealthError(String(e)));
  }, []);

  return (
    <AppShell phase={health?.phase ?? null}>
      <PhaseZeroPage health={health} healthError={healthError} />
    </AppShell>
  );
};

export default App;
