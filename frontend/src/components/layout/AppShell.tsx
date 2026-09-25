/**
 * AppShell — Main Layout Shell (Phase 1 — UI Shell)
 *
 * Left navigation per spec section 15:
 *   Investigation, Overview, Evidence, Fragments, Reconstruction,
 *   Validation, Reports, Settings
 *
 * Header: system status (API health, current phase, disclaimer).
 * Sidebar: workbench navigation with phase badges + investigation context.
 */

import React from 'react';
import { useInvestigation, PageId } from '../../context/InvestigationContext';

interface AppShellProps {
  children: React.ReactNode;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

interface NavItem {
  id: PageId;
  label: string;
  icon: string;
  phaseLabel: string;
  live: boolean;    // true = real endpoint available
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: 'Investigation',
    items: [
      { id: 'overview', label: 'Overview', icon: '📊', phaseLabel: 'Phase 0', live: true },
    ],
  },
  {
    label: 'Pipeline Stages',
    items: [
      { id: 'evidence', label: 'Evidence', icon: '💾', phaseLabel: 'Phase 1', live: true },
      { id: 'fragments', label: 'Fragments', icon: '🧩', phaseLabel: 'Phase 2', live: false },
      { id: 'reconstruction', label: 'Reconstruction', icon: '🔗', phaseLabel: 'Phase 4', live: false },
      { id: 'validation', label: 'Validation', icon: '🛡️', phaseLabel: 'Phase 6', live: false },
    ],
  },
  {
    label: 'Output',
    items: [
      { id: 'reports', label: 'Reports', icon: '📄', phaseLabel: 'Phase 8', live: false },
    ],
  },
  {
    label: 'System',
    items: [
      { id: 'settings', label: 'Settings', icon: '⚙️', phaseLabel: 'Phase 0', live: true },
    ],
  },
];

// Pulse animation injected once
const PULSE_STYLE = `
  @keyframes rw-pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.35; }
  }
  @keyframes rw-spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }
`;

if (typeof document !== 'undefined' && !document.getElementById('rw-keyframes')) {
  const s = document.createElement('style');
  s.id = 'rw-keyframes';
  s.textContent = PULSE_STYLE;
  document.head.appendChild(s);
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { currentPage, setCurrentPage, apiHealth, isApiOnline, isLoadingHealth, healthError, refreshHealth } =
    useInvestigation();

  const currentPhase = apiHealth?.current_phase ?? 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', overflow: 'hidden' }}>

      {/* ═══════════════════════════════════════════════════════════════════
          TOP BAR
         ═══════════════════════════════════════════════════════════════════ */}
      <header
        style={{
          height: 'var(--topbar-height)',
          background: 'var(--bg-surface)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0 var(--space-6)', flexShrink: 0, zIndex: 10,
          boxShadow: '0 1px 0 rgba(255,255,255,0.03)',
        }}
      >
        {/* Left: Logo + Phase Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            {/* Logo Mark */}
            <div style={{
              width: '30px', height: '30px', borderRadius: 'var(--radius-sm)',
              background: 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontWeight: 800, color: '#030712', fontSize: '13px',
              boxShadow: '0 0 14px rgba(6,182,212,0.35)',
              letterSpacing: '-0.5px',
            }}>
              RC
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 'var(--text-base)', letterSpacing: '0.06em', lineHeight: 1 }}>
                RECONSTRUCT
              </div>
              <div className="font-mono" style={{ fontSize: '9px', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>
                FORENSIC WORKBENCH
              </div>
            </div>
          </div>

          <div style={{ width: '1px', height: '28px', background: 'var(--border-subtle)' }} />

          <span className="badge badge-phase">
            Phase {currentPhase} — {currentPhase === 0 ? 'Scaffolding' : currentPhase === 1 ? 'Evidence Ingest' : `Live`}
          </span>
        </div>

        {/* Right: Status Indicators */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>

          {/* Mandatory Legal Disclaimer */}
          <div style={{
            padding: '4px 10px', borderRadius: 'var(--radius-md)',
            background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.25)',
            color: '#FCA5A5', fontSize: '10px', fontWeight: 700,
            display: 'flex', alignItems: 'center', gap: '5px', letterSpacing: '0.03em',
          }}>
            <span>⚠️</span>
            <span>PORTFOLIO PROTOTYPE — NOT LEGALLY ADMISSIBLE</span>
          </div>

          {/* API Status */}
          <button
            id="btn-refresh-health"
            onClick={refreshHealth}
            title="Click to refresh API status"
            style={{
              display: 'flex', alignItems: 'center', gap: 'var(--space-2)',
              fontSize: 'var(--text-xs)', padding: '4px 10px', borderRadius: 'var(--radius-md)',
              background: isApiOnline ? 'rgba(16, 185, 129, 0.08)' : healthError ? 'rgba(239,68,68,0.08)' : 'rgba(100,116,139,0.08)',
              border: `1px solid ${isApiOnline ? 'rgba(16, 185, 129, 0.25)' : healthError ? 'rgba(239,68,68,0.25)' : 'rgba(100,116,139,0.25)'}`,
              color: isApiOnline ? '#34D399' : healthError ? '#F87171' : '#94A3B8',
              cursor: 'pointer', transition: 'all 0.15s',
            }}
          >
            <span style={{
              width: '7px', height: '7px', borderRadius: '50%',
              backgroundColor: isApiOnline ? '#10B981' : healthError ? '#EF4444' : '#64748B',
              boxShadow: isApiOnline ? '0 0 8px #10B981' : 'none',
              flexShrink: 0,
              animation: isLoadingHealth ? 'rw-pulse 1s ease-in-out infinite' : 'none',
            }} />
            <span className="font-mono">
              {isLoadingHealth ? 'CHECKING…' : isApiOnline ? `API v${apiHealth?.version}` : 'API OFFLINE'}
            </span>
          </button>
        </div>
      </header>

      {/* ═══════════════════════════════════════════════════════════════════
          MAIN SPLIT: SIDEBAR + PAGE CANVAS
         ═══════════════════════════════════════════════════════════════════ */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* ─── Left Navigation Sidebar ──────────────────────────────────── */}
        <aside style={{
          width: 'var(--sidebar-width)', background: 'var(--bg-surface)',
          borderRight: '1px solid var(--border-subtle)',
          display: 'flex', flexDirection: 'column',
          justifyContent: 'space-between', padding: 'var(--space-4) 0',
          flexShrink: 0,
        }}>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', overflowY: 'auto' }}>
            {NAV_GROUPS.map((group) => (
              <div key={group.label} style={{ marginBottom: 'var(--space-3)' }}>
                {/* Group Label */}
                <div style={{
                  fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)',
                  textTransform: 'uppercase', letterSpacing: '0.1em',
                  padding: 'var(--space-2) var(--space-4)',
                }}>
                  {group.label}
                </div>

                {/* Items */}
                {group.items.map((item) => {
                  const isActive = currentPage === item.id;
                  return (
                    <button
                      key={item.id}
                      id={`nav-${item.id}`}
                      onClick={() => setCurrentPage(item.id)}
                      style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: '7px var(--space-4)', borderRadius: 0,
                        border: 'none',
                        borderLeft: isActive ? '3px solid var(--border-focus)' : '3px solid transparent',
                        background: isActive ? 'rgba(6,182,212,0.08)' : 'transparent',
                        color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                        fontWeight: isActive ? 600 : 400,
                        fontSize: 'var(--text-sm)', cursor: 'pointer',
                        transition: 'all 0.15s', textAlign: 'left', width: '100%',
                      }}
                      onMouseEnter={(e) => { if (!isActive) { e.currentTarget.style.background = 'var(--bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; } }}
                      onMouseLeave={(e) => { if (!isActive) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; } }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                        <span style={{ fontSize: '14px', width: '18px', textAlign: 'center', flexShrink: 0 }}>
                          {item.icon}
                        </span>
                        <span>{item.label}</span>
                      </div>

                      {/* Phase badge */}
                      <span style={{
                        fontSize: '9px', fontWeight: 600,
                        padding: '1px 5px', borderRadius: 'var(--radius-sm)',
                        background: item.live ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.04)',
                        color: item.live ? '#34D399' : 'var(--text-muted)',
                        border: item.live ? '1px solid rgba(16,185,129,0.25)' : '1px solid transparent',
                        letterSpacing: '0.04em', flexShrink: 0,
                      }}>
                        {item.live ? '● LIVE' : item.phaseLabel}
                      </span>
                    </button>
                  );
                })}
              </div>
            ))}
          </nav>

          {/* Sidebar Footer — DB info */}
          <div style={{
            padding: 'var(--space-3) var(--space-4)',
            borderTop: '1px solid var(--border-subtle)',
          }}>
            <div className="font-mono" style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '3px' }}>
              SQLite · reconstruct.db
            </div>
            <div className="font-mono" style={{ fontSize: '10px', color: 'var(--text-disabled)' }}>
              Schema v1 · 7 tables
            </div>
            {apiHealth && (
              <div className="font-mono" style={{ fontSize: '10px', color: 'var(--text-disabled)', marginTop: '3px' }}>
                API {apiHealth.version} · {apiHealth.api_version}
              </div>
            )}
          </div>
        </aside>

        {/* ─── Page Content Viewport ────────────────────────────────────── */}
        <main style={{
          flex: 1, overflowY: 'auto', padding: 'var(--space-8)',
          background: 'var(--bg-page)',
        }}>
          {children}
        </main>
      </div>
    </div>
  );
};
