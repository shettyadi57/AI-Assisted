import React from 'react';
import { useInvestigation, PageId } from '../../context/InvestigationContext';

interface AppShellProps {
  children: React.ReactNode;
}

interface NavItem {
  id: PageId;
  label: string;
  icon: string;
  phaseLabel: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: '📊', phaseLabel: 'Phase 0' },
  { id: 'evidence', label: 'Evidence', icon: '💾', phaseLabel: 'Phase 1' },
  { id: 'fragments', label: 'Fragments', icon: '🧩', phaseLabel: 'Phase 2' },
  { id: 'reconstruction', label: 'Reconstruction', icon: '🔗', phaseLabel: 'Phase 4' },
  { id: 'validation', label: 'Validation', icon: '🛡️', phaseLabel: 'Phase 6' },
  { id: 'reports', label: 'Reports', icon: '📄', phaseLabel: 'Phase 8' },
  { id: 'settings', label: 'Settings', icon: '⚙️', phaseLabel: 'Phase 0' },
];

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { currentPage, setCurrentPage, apiHealth, isApiOnline, isLoadingHealth } = useInvestigation();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* ── Top Bar ────────────────────────────────────────────────────────── */}
      <header
        style={{
          height: 'var(--topbar-height)',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 var(--space-6)',
          flexShrink: 0,
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <div
              style={{
                width: '28px',
                height: '28px',
                borderRadius: 'var(--radius-sm)',
                background: 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                color: '#041016',
                fontSize: '14px',
              }}
            >
              RC
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontWeight: 700, fontSize: 'var(--text-base)', letterSpacing: '0.05em' }}>
                RECONSTRUCT
              </span>
              <span className="font-mono" style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                FORENSIC WORKBENCH
              </span>
            </div>
          </div>

          <span style={{ color: 'var(--border-medium)', margin: '0 var(--space-2)' }}>|</span>

          {/* Phase Badge */}
          <span className="badge badge-phase">
            Phase 0 — Scaffolding
          </span>
        </div>

        {/* Center / Right controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          {/* Mandatory Legal Warning */}
          <div
            style={{
              padding: '4px 10px',
              borderRadius: 'var(--radius-md)',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#FCA5A5',
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>⚠️</span>
            <span>PORTFOLIO PROTOTYPE — NOT LEGALLY ADMISSIBLE</span>
          </div>

          {/* Live Backend Connection Status */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              fontSize: 'var(--text-xs)',
              padding: '4px 10px',
              borderRadius: 'var(--radius-md)',
              background: isApiOnline ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
              border: `1px solid ${isApiOnline ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
              color: isApiOnline ? '#34D399' : '#F87171',
            }}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: isApiOnline ? '#10B981' : '#EF4444',
                boxShadow: isApiOnline ? '0 0 8px #10B981' : 'none',
              }}
            />
            <span className="font-mono">
              {isLoadingHealth ? 'CHECKING...' : isApiOnline ? `API ONLINE (v${apiHealth?.version})` : 'API OFFLINE'}
            </span>
          </div>
        </div>
      </header>

      {/* ── Main Layout Split: Sidebar + Page Canvas ──────────────────────── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Navigation Sidebar */}
        <aside
          style={{
            width: 'var(--sidebar-width)',
            background: 'var(--bg-surface)',
            borderRight: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            padding: 'var(--space-4) 0',
            flexShrink: 0,
          }}
        >
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px', padding: '0 var(--space-3)' }}>
            <div
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                padding: 'var(--space-2) var(--space-3)',
                marginBottom: 'var(--space-1)',
              }}
            >
              Workbench Navigation
            </div>

            {NAV_ITEMS.map((item) => {
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  id={`nav-${item.id}`}
                  onClick={() => setCurrentPage(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    border: 'none',
                    background: isActive ? 'var(--bg-raised)' : 'transparent',
                    color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                    fontWeight: isActive ? 600 : 500,
                    fontSize: 'var(--text-sm)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    textAlign: 'left',
                    boxShadow: isActive ? 'inset 3px 0 0 var(--border-focus)' : 'none',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) e.currentTarget.style.background = 'var(--bg-hover)';
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) e.currentTarget.style.background = 'transparent';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                    <span>{item.icon}</span>
                    <span>{item.label}</span>
                  </div>
                  <span
                    className="font-mono"
                    style={{
                      fontSize: '10px',
                      color: isActive ? 'var(--border-focus)' : 'var(--text-muted)',
                      background: 'rgba(255, 255, 255, 0.04)',
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    {item.phaseLabel}
                  </span>
                </button>
              );
            })}
          </nav>

          {/* Sidebar Footer */}
          <div style={{ padding: '0 var(--space-4)', borderTop: '1px solid var(--border-subtle)', paddingTop: 'var(--space-4)' }}>
            <div className="font-mono" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              SQLite: reconstruct.db
            </div>
            <div className="font-mono" style={{ fontSize: '10px', color: 'var(--text-disabled)', marginTop: '2px' }}>
              Schema v1 (7 Tables)
            </div>
          </div>
        </aside>

        {/* Page Content Viewport */}
        <main
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 'var(--space-8)',
            background: 'var(--bg-page)',
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
};
