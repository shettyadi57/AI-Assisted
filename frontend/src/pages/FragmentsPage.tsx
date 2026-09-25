/**
 * Fragments Page — Phase 2 LIVE
 *
 * Left panel: real fragment list (ID, size, offset, entropy, duplicate flag, type: unknown)
 * Right panel: hex inspector — real bytes, real offset, ASCII + hex side-by-side
 *
 * Data flows:
 *   1. Load evidence list → user picks an evidence record
 *   2. POST /api/v1/analysis/fragments  → get/run fragment analysis
 *   3. GET /api/v1/analysis/fragments/{id}/hex → hex dump on selection
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface EvidenceSummary {
  id: string;
  filename: string;
  file_size_bytes: number;
  sha256_hash: string;
  status: string;
  is_sample_dataset: boolean;
}

interface FragmentRecord {
  id: string;
  evidence_id: string;
  offset_start: number;
  offset_end: number;
  size_bytes: number;
  sha256_hash: string;
  entropy: number;
  status: string;
  entropy_class: string;
  content_class: string;
  hex_preview: string;
  flags: string[];
  inferred_format: string | null;
  created_at: string;
}

interface HexRow {
  offset: number;
  offset_hex: string;
  hex: string;
  ascii: string;
}

interface HexDump {
  fragment_id: string;
  evidence_filename: string;
  offset_start: number;
  size_bytes: number;
  bytes_returned: number;
  truncated: boolean;
  rows: HexRow[];
}

interface AnalysisResult {
  evidence_id: string;
  evidence_filename: string;
  fragment_count: number;
  duplicate_count: number;
  block_size_used: number;
  fragments: FragmentRecord[];
  disclaimer: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const formatBytes = (n: number) => {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
};

const entropyColor = (ent: number) => {
  if (ent >= 7.2) return '#F87171';   // high — red
  if (ent >= 5.0) return '#FB923C';   // medium-high — orange
  if (ent >= 2.5) return '#FBBF24';   // medium — amber
  return '#34D399';                    // low — green
};

const statusStyle = (status: string): React.CSSProperties => {
  const map: Record<string, [string, string, string]> = {
    UNCERTAIN:  ['var(--status-uncertain)',  'var(--status-uncertain-bg)',  'var(--status-uncertain-border)'],
    DUPLICATE:  ['var(--status-duplicate)',  'var(--status-duplicate-bg)',  'var(--status-duplicate-border)'],
    CONFIRMED:  ['var(--status-valid)',      'var(--status-valid-bg)',      'var(--status-valid-border)'],
    CORRUPTED:  ['var(--status-corrupted)',  'var(--status-corrupted-bg)',  'var(--status-corrupted-border)'],
    MISSING:    ['var(--status-missing)',    'var(--status-missing-bg)',    'var(--status-missing-border)'],
    INFERRED:   ['var(--status-recovered)', 'var(--status-recovered-bg)',  'var(--status-recovered-border)'],
  };
  const [color, bg, border] = map[status] ?? ['#94A3B8', 'rgba(100,116,139,0.1)', 'rgba(100,116,139,0.25)'];
  return { color, background: bg, border: `1px solid ${border}` };
};

// ─── EntropyBar ───────────────────────────────────────────────────────────────

const EntropyBar: React.FC<{ value: number }> = ({ value }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0 }}>
    <div style={{
      flex: 1, height: '6px', background: 'var(--bg-raised)',
      borderRadius: 'var(--radius-pill)', overflow: 'hidden',
    }}>
      <div style={{
        height: '100%', width: `${(value / 8.0) * 100}%`,
        background: entropyColor(value), borderRadius: 'var(--radius-pill)',
        transition: 'width 0.3s ease',
      }} />
    </div>
    <span className="font-mono" style={{ fontSize: '10px', color: entropyColor(value), flexShrink: 0, width: '34px', textAlign: 'right' }}>
      {value.toFixed(2)}
    </span>
  </div>
);

// ─── HexInspector ─────────────────────────────────────────────────────────────

const HexInspector: React.FC<{ fragment: FragmentRecord | null; dump: HexDump | null; loading: boolean }> = ({
  fragment, dump, loading,
}) => {
  const [hoveredRow, setHoveredRow] = useState<number | null>(null);

  if (!fragment) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', gap: 'var(--space-3)' }}>
        <div style={{ fontSize: '32px' }}>🔬</div>
        <div style={{ fontSize: 'var(--text-sm)' }}>Select a fragment to inspect its bytes</div>
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-disabled)' }}>Hex · ASCII · Offset view</div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 'var(--space-3)' }}>
      {/* Fragment summary header */}
      <div style={{ padding: 'var(--space-3)', background: 'var(--bg-raised)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', flexShrink: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>Fragment ID</div>
            <div className="font-mono" style={{ fontSize: 'var(--text-xs)', color: '#06B6D4', letterSpacing: '0.03em' }}>{fragment.id}</div>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
            {[
              ['Offset', `0x${fragment.offset_start.toString(16).toUpperCase().padStart(8, '0')}`],
              ['Size', formatBytes(fragment.size_bytes)],
              ['Entropy', fragment.entropy.toFixed(4)],
            ].map(([label, val]) => (
              <div key={label} style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>{label}</div>
                <div className="font-mono" style={{ fontSize: 'var(--text-xs)', color: 'var(--text-primary)' }}>{val}</div>
              </div>
            ))}
          </div>
        </div>
        <div style={{ marginTop: 'var(--space-2)', display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          <span className="badge" style={{ ...statusStyle(fragment.status), fontSize: '10px' }}>{fragment.status}</span>
          <span className="badge" style={{ background: 'rgba(100,116,139,0.1)', color: '#94A3B8', border: '1px solid rgba(100,116,139,0.2)', fontSize: '10px' }}>{fragment.entropy_class}</span>
          <span className="badge" style={{ background: 'rgba(100,116,139,0.1)', color: '#94A3B8', border: '1px solid rgba(100,116,139,0.2)', fontSize: '10px' }}>{fragment.content_class}</span>
          <span className="badge" style={{ background: 'rgba(139,92,246,0.1)', color: '#A78BFA', border: '1px solid rgba(139,92,246,0.2)', fontSize: '10px' }}>
            TYPE: UNKNOWN (Phase 3)
          </span>
          {fragment.flags.map((f) => (
            <span key={f} className="badge" style={{ background: 'rgba(245,158,11,0.1)', color: '#FCD34D', border: '1px solid rgba(245,158,11,0.2)', fontSize: '10px' }}>
              {f.split(':')[0]}
            </span>
          ))}
        </div>
        {/* SHA-256 */}
        <div className="font-mono" style={{ marginTop: 'var(--space-2)', fontSize: '10px', color: 'var(--text-muted)', letterSpacing: '0.02em', wordBreak: 'break-all' }}>
          SHA-256: {fragment.sha256_hash}
        </div>
      </div>

      {/* Hex dump area */}
      <div style={{ flex: 1, overflow: 'auto', position: 'relative' }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', marginBottom: 'var(--space-2)' }}>⏳</div>
              <div>Loading hex dump…</div>
            </div>
          </div>
        ) : dump ? (
          <>
            {/* Column header */}
            <div className="font-mono" style={{
              display: 'grid', gridTemplateColumns: '90px 1fr 140px',
              gap: '12px', padding: '6px 8px',
              fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600,
              borderBottom: '1px solid var(--border-subtle)', position: 'sticky', top: 0,
              background: 'var(--bg-page)', zIndex: 1,
            }}>
              <span>OFFSET</span>
              <span>00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F</span>
              <span>ASCII</span>
            </div>

            {dump.rows.map((row, idx) => (
              <div
                key={row.offset}
                onMouseEnter={() => setHoveredRow(idx)}
                onMouseLeave={() => setHoveredRow(null)}
                className="font-mono"
                style={{
                  display: 'grid', gridTemplateColumns: '90px 1fr 140px',
                  gap: '12px', padding: '3px 8px',
                  fontSize: '11px', lineHeight: 1.8,
                  background: hoveredRow === idx ? 'rgba(6,182,212,0.06)' : 'transparent',
                  transition: 'background 0.1s',
                  cursor: 'default',
                }}
              >
                <span style={{ color: '#64748B' }}>{row.offset_hex}</span>
                <span style={{ color: '#CBD5E1', letterSpacing: '0.02em' }}>{row.hex}</span>
                <span style={{ color: '#4B6B8A', letterSpacing: '0.05em' }}>{row.ascii}</span>
              </div>
            ))}

            {dump.truncated && (
              <div style={{ padding: '8px', textAlign: 'center', fontSize: 'var(--text-xs)', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)' }}>
                ⚠ Showing first {dump.bytes_returned} of {dump.size_bytes} bytes
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────

export const FragmentsPage: React.FC = () => {
  // Evidence selector
  const [evidenceList, setEvidenceList] = useState<EvidenceSummary[]>([]);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceSummary | null>(null);

  // Analysis state
  const [analysisState, setAnalysisState] = useState<'idle' | 'running' | 'done' | 'error'>('idle');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // Fragment selection + hex inspector
  const [selectedFragment, setSelectedFragment] = useState<FragmentRecord | null>(null);
  const [hexDump, setHexDump] = useState<HexDump | null>(null);
  const [hexLoading, setHexLoading] = useState(false);

  // Filter
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Block size config
  const [blockSize, setBlockSize] = useState(4096);

  // ── Load evidence list ─────────────────────────────────────────────────
  useEffect(() => {
    fetch('/api/v1/discovery/evidence')
      .then((r) => r.json())
      .then((d) => {
        setEvidenceList(d.items ?? []);
        // Auto-select the first evidence if any
        if (d.items?.length > 0 && !selectedEvidence) {
          setSelectedEvidence(d.items[0]);
        }
      })
      .catch(() => {});
  }, []);

  // ── Run / load fragment analysis ──────────────────────────────────────
  const runAnalysis = useCallback(
    async (evId: string, forceReanalyze = false) => {
      setAnalysisState('running');
      setAnalysisResult(null);
      setAnalysisError(null);
      setSelectedFragment(null);
      setHexDump(null);
      try {
        const res = await fetch('/api/v1/analysis/fragments', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ evidence_id: evId, block_size: blockSize, force_reanalyze: forceReanalyze }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`);
        setAnalysisResult(data);
        setAnalysisState('done');
      } catch (err: any) {
        setAnalysisError(err.message);
        setAnalysisState('error');
      }
    },
    [blockSize]
  );

  // Auto-run when evidence is selected
  useEffect(() => {
    if (selectedEvidence) runAnalysis(selectedEvidence.id);
  }, [selectedEvidence]);

  // ── Fetch hex dump on fragment selection ──────────────────────────────
  const selectFragment = useCallback(async (frag: FragmentRecord) => {
    setSelectedFragment(frag);
    setHexLoading(true);
    setHexDump(null);
    try {
      const res = await fetch(`/api/v1/analysis/fragments/${frag.id}/hex?max_bytes=4096`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? `HTTP ${res.status}`);
      setHexDump(data);
    } catch (err: any) {
      // Show what we have in hex_preview as fallback
    } finally {
      setHexLoading(false);
    }
  }, []);

  // ── Filter fragments ──────────────────────────────────────────────────
  const filteredFragments = (analysisResult?.fragments ?? []).filter((f) => {
    if (statusFilter !== 'ALL' && f.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        f.id.toLowerCase().includes(q) ||
        f.sha256_hash.toLowerCase().includes(q) ||
        f.entropy_class.toLowerCase().includes(q) ||
        f.content_class.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const dupCount = analysisResult?.fragments.filter((f) => f.status === 'DUPLICATE').length ?? 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 'var(--space-4)', overflow: 'hidden' }}>

      {/* ── Page Header ─────────────────────────────────────────────────── */}
      <div style={{ flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
          <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 700 }}>Fragment Discovery</h1>
          <span className="badge badge-valid" style={{ fontSize: '10px' }}>Phase 2 — LIVE</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-6)', flexWrap: 'wrap' }}>
          <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-sm)', maxWidth: '560px', margin: 0 }}>
            Fixed-block analysis · Shannon entropy · Duplicate detection.
            File-type identification is <span style={{ color: '#A78BFA' }}>Phase 3</span>.
          </p>
          <div style={{
            padding: '4px 10px', borderRadius: 'var(--radius-md)',
            background: 'rgba(167,139,250,0.08)', border: '1px solid rgba(167,139,250,0.2)',
            color: '#A78BFA', fontSize: '10px', fontWeight: 600,
          }}>
            ℹ PRELIMINARY — entropy class &amp; content class are Phase 2 heuristics
          </div>
        </div>
      </div>

      {/* ── Evidence selector + config bar ──────────────────────────────── */}
      <div style={{
        flexShrink: 0, display: 'flex', gap: 'var(--space-3)', alignItems: 'center',
        flexWrap: 'wrap', padding: 'var(--space-3) var(--space-4)',
        background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flex: 1, minWidth: '200px' }}>
          <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', flexShrink: 0 }}>
            Evidence
          </label>
          <select
            id="evidence-selector"
            value={selectedEvidence?.id ?? ''}
            onChange={(e) => {
              const ev = evidenceList.find((x) => x.id === e.target.value) ?? null;
              setSelectedEvidence(ev);
            }}
            style={{
              flex: 1, background: 'var(--bg-page)', color: 'var(--text-primary)',
              border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
              padding: '4px 8px', fontSize: 'var(--text-sm)', fontFamily: 'var(--font-sans)',
            }}
          >
            {evidenceList.length === 0 && <option value="">No evidence registered</option>}
            {evidenceList.map((ev) => (
              <option key={ev.id} value={ev.id}>
                {ev.filename} — {formatBytes(ev.file_size_bytes)}
                {ev.is_sample_dataset ? ' [SAMPLE]' : ''}
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <label style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', flexShrink: 0 }}>
            Block Size
          </label>
          <select
            id="block-size-selector"
            value={blockSize}
            onChange={(e) => setBlockSize(Number(e.target.value))}
            style={{
              background: 'var(--bg-page)', color: 'var(--text-primary)',
              border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
              padding: '4px 8px', fontSize: 'var(--text-sm)', fontFamily: 'var(--font-mono)',
            }}
          >
            {[512, 1024, 2048, 4096, 8192].map((b) => (
              <option key={b} value={b}>{b.toLocaleString()} B</option>
            ))}
          </select>
        </div>

        <button
          id="btn-run-analysis"
          className="btn-primary"
          disabled={!selectedEvidence || analysisState === 'running'}
          onClick={() => selectedEvidence && runAnalysis(selectedEvidence.id, true)}
          style={{ fontSize: 'var(--text-xs)', padding: '6px 14px' }}
        >
          {analysisState === 'running' ? '⏳ Analyzing…' : '▶ Re-analyze'}
        </button>
      </div>

      {/* ── Stats bar ────────────────────────────────────────────────────── */}
      {analysisResult && (
        <div style={{
          flexShrink: 0, display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)', gap: 'var(--space-3)',
        }}>
          {[
            { label: 'Total Fragments', value: analysisResult.fragment_count, color: '#06B6D4' },
            { label: 'Duplicates', value: dupCount, color: '#F59E0B' },
            { label: 'Block Size', value: `${analysisResult.block_size_used.toLocaleString()} B`, color: '#94A3B8' },
            { label: 'Evidence Size', value: formatBytes(selectedEvidence?.file_size_bytes ?? 0), color: '#94A3B8' },
            { label: 'Unique Fragments', value: analysisResult.fragment_count - dupCount, color: '#10B981' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{
              background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)', padding: 'var(--space-3)',
            }}>
              <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: '4px' }}>{label}</div>
              <div className="font-mono" style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color }}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* ── Main split: fragment list + hex inspector ─────────────────────── */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '400px 1fr', gap: 'var(--space-4)', overflow: 'hidden', minHeight: 0 }}>

        {/* Left: Fragment List */}
        <div style={{
          background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)', display: 'flex',
          flexDirection: 'column', overflow: 'hidden',
        }}>
          {/* List header */}
          <div style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--border-subtle)', flexShrink: 0 }}>
            <div style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-2)', flexWrap: 'wrap' }}>
              {['ALL', 'UNCERTAIN', 'DUPLICATE', 'CONFIRMED'].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  style={{
                    fontSize: '10px', fontWeight: 600, padding: '2px 8px',
                    borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer',
                    background: statusFilter === s ? 'var(--border-focus)' : 'var(--bg-raised)',
                    color: statusFilter === s ? '#041016' : 'var(--text-muted)',
                    transition: 'all 0.15s',
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
            <input
              placeholder="Search ID, hash, class…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%', background: 'var(--bg-page)', color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)',
                padding: '5px 10px', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Fragment rows */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {analysisState === 'running' ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: 'var(--text-muted)', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div style={{ fontSize: '28px' }}>⏳</div>
                <div>Analyzing fragments…</div>
              </div>
            ) : analysisState === 'error' ? (
              <div style={{ padding: 'var(--space-4)', color: '#FCA5A5', fontSize: 'var(--text-sm)' }}>
                ⚠ {analysisError}
              </div>
            ) : analysisState === 'idle' ? (
              <div style={{ padding: 'var(--space-6)', color: 'var(--text-muted)', textAlign: 'center', fontSize: 'var(--text-sm)' }}>
                Select an evidence record above to begin
              </div>
            ) : filteredFragments.length === 0 ? (
              <div style={{ padding: 'var(--space-4)', color: 'var(--text-muted)', textAlign: 'center', fontSize: 'var(--text-sm)' }}>
                No fragments match the current filter
              </div>
            ) : (
              filteredFragments.map((frag) => {
                const isSelected = selectedFragment?.id === frag.id;
                const isDup = frag.status === 'DUPLICATE';
                return (
                  <div
                    key={frag.id}
                    id={`frag-${frag.id.slice(0, 8)}`}
                    onClick={() => selectFragment(frag)}
                    style={{
                      padding: 'var(--space-3) var(--space-4)',
                      borderBottom: '1px solid var(--border-subtle)',
                      cursor: 'pointer', transition: 'background 0.1s',
                      borderLeft: isSelected ? '3px solid var(--border-focus)' : '3px solid transparent',
                      background: isSelected ? 'rgba(6,182,212,0.06)' : 'transparent',
                    }}
                    onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.background = 'var(--bg-hover)'; }}
                    onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}
                  >
                    {/* Row top: offset + status badges */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <span className="font-mono" style={{ fontSize: '10px', color: '#64748B' }}>
                        0x{frag.offset_start.toString(16).toUpperCase().padStart(8, '0')}
                      </span>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <span className="badge" style={{ ...statusStyle(frag.status), fontSize: '9px', padding: '1px 5px' }}>
                          {frag.status}
                        </span>
                        {isDup && <span style={{ fontSize: '12px' }} title="Duplicate fragment">♦</span>}
                      </div>
                    </div>

                    {/* Fragment ID (shortened) */}
                    <div className="font-mono" style={{ fontSize: '10px', color: '#06B6D4', marginBottom: '4px' }}>
                      {frag.id.slice(0, 8)}…
                    </div>

                    {/* Size + class */}
                    <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: '6px', fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>
                      <span>{formatBytes(frag.size_bytes)}</span>
                      <span>{frag.content_class}</span>
                      <span style={{ color: '#A78BFA' }}>type: unknown</span>
                    </div>

                    {/* Entropy bar */}
                    <EntropyBar value={frag.entropy} />

                    {/* Hex preview */}
                    <div className="font-mono" style={{
                      marginTop: '5px', fontSize: '9px', color: '#475569',
                      letterSpacing: '0.03em', overflow: 'hidden',
                      textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {frag.hex_preview}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* List footer */}
          {analysisResult && (
            <div style={{ padding: 'var(--space-2) var(--space-4)', borderTop: '1px solid var(--border-subtle)', fontSize: '10px', color: 'var(--text-muted)', flexShrink: 0 }}>
              {filteredFragments.length} of {analysisResult.fragment_count} fragments
            </div>
          )}
        </div>

        {/* Right: Hex Inspector */}
        <div style={{
          background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
          padding: 'var(--space-4)',
        }}>
          <div style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-3)', flexShrink: 0 }}>
            Hex Inspector
          </div>
          <HexInspector fragment={selectedFragment} dump={hexDump} loading={hexLoading} />
        </div>
      </div>

      {/* ── Phase gate notice for downstream stages ───────────────────────── */}
      <div style={{
        flexShrink: 0, padding: 'var(--space-3) var(--space-4)',
        background: 'rgba(56,189,248,0.04)', borderRadius: 'var(--radius-md)',
        border: '1px solid rgba(56,189,248,0.12)', fontSize: 'var(--text-xs)',
        color: 'var(--text-muted)', display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap',
      }}>
        <span style={{ color: '#38BDF8' }}>ℹ</span>
        <span><strong style={{ color: 'var(--text-secondary)' }}>File-type signature detection</strong> — Phase 3 · </span>
        <span><strong style={{ color: 'var(--text-secondary)' }}>Fragment relationship scoring (ML)</strong> — Phase 3 · </span>
        <span><strong style={{ color: 'var(--text-secondary)' }}>Reconstruction candidates</strong> — Phase 4</span>
      </div>
    </div>
  );
};
