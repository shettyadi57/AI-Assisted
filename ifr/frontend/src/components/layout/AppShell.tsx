/**
 * Application shell: top bar + sidebar + main content area.
 * Phase 0: layout scaffold only — nav items are labeled with their phase.
 */

import React from 'react';
import { PhaseInfo } from '@/types';

interface NavItem {
  id: string;
  label: string;
  availablePhase: number;   // 0 = available now; >0 = coming in that phase
  currentPhase: number;
}

const NavLink: React.FC<NavItem> = ({ id, label, availablePhase, currentPhase }) => {
  const isAvailable = availablePhase <= currentPhase;
  return (
    <li>
      <button
        id={`nav-${id}`}
        disabled={!isAvailable}
        aria-disabled={!isAvailable}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
          padding: '6px 12px',
          background: 'none',
          border: 'none',
          borderRadius: 'var(--radius)',
          color: isAvailable ? 'var(--text-primary)' : 'var(--text-disabled)',
          fontFamily: 'var(--font-sans)',
          fontSize: 'var(--text-sm)',
          cursor: isAvailable ? 'pointer' : 'not-allowed',
          textAlign: 'left',
          transition: 'background 120ms ease',
        }}
        onMouseEnter={e => {
          if (isAvailable) (e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-raised)';
        }}
        onMouseLeave={e => {
          (e.currentTarget as HTMLButtonElement).style.background = 'none';
        }}
      >
        <span>{label}</span>
        {!isAvailable && (
          <span className="phase-badge">P{availablePhase}</span>
        )}
      </button>
    </li>
  );
};


interface AppShellProps {
  phase: PhaseInfo | null;
  children: React.ReactNode;
}

const AppShell: React.FC<AppShellProps> = ({ phase, children }) => {
  const currentPhase = phase?.current_phase ?? 0;

  const navItems: Omit<NavItem, 'currentPhase'>[] = [
    { id: 'evidence',        label: 'Evidence',            availablePhase: 1 },
    { id: 'fragments',       label: 'Fragments',           availablePhase: 2 },
    { id: 'relationships',   label: 'Relationships',       availablePhase: 3 },
    { id: 'candidates',      label: 'Candidates',          availablePhase: 4 },
    { id: 'review',          label: 'Review Queue',        availablePhase: 5 },
    { id: 'validation',      label: 'Validation',          availablePhase: 6 },
    { id: 'provenance',      label: 'Provenance',          availablePhase: 7 },
    { id: 'reports',         label: 'Reports',             availablePhase: 8 },
    { id: 'signatures',      label: 'Signatures',          availablePhase: 0 },
    { id: 'audit-log',       label: 'Audit Log',           availablePhase: 5 },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* ── Top bar ──────────────────────────────────────────────────── */}
      <header
        id="app-topbar"
        role="banner"
        style={{
          height: 'var(--topbar-height)',
          minHeight: 'var(--topbar-height)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 var(--space-4)',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-subtle)',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontWeight: 600,
              fontSize: 'var(--text-md)',
              color: 'var(--text-primary)',
              letterSpacing: '-0.01em',
            }}
          >
            IFR
          </span>
          <span
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: 'var(--text-sm)',
              color: 'var(--text-muted)',
            }}
          >
            Intelligent Fragment Reconstruction
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          {phase && (
            <span className="phase-badge">
              Phase {phase.current_phase} — {phase.phase_label}
            </span>
          )}
        </div>
      </header>

      {/* ── Body: sidebar + main ──────────────────────────────────────── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <nav
          id="app-sidebar"
          aria-label="Primary navigation"
          style={{
            width: 'var(--sidebar-width)',
            minWidth: 'var(--sidebar-width)',
            background: 'var(--bg-surface)',
            borderRight: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            padding: 'var(--space-3) 0',
            overflowY: 'auto',
          }}
        >
          <ul
            style={{
              listStyle: 'none',
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              padding: '0 var(--space-2)',
            }}
          >
            {navItems.map(item => (
              <NavLink key={item.id} {...item} currentPhase={currentPhase} />
            ))}
          </ul>

          {/* Disclaimer at bottom */}
          <div
            style={{
              marginTop: 'auto',
              padding: 'var(--space-3) var(--space-3)',
              borderTop: '1px solid var(--border-subtle)',
              fontSize: 'var(--text-xs)',
              color: 'var(--text-muted)',
              lineHeight: 1.5,
            }}
          >
            Portfolio / prototype forensic tool.{' '}
            <strong>Not legally admissible.</strong>
          </div>
        </nav>

        {/* Main content */}
        <main
          id="app-main"
          role="main"
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: 'var(--space-6)',
            background: 'var(--bg-page)',
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppShell;
